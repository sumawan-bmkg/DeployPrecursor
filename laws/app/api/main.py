#!/usr/bin/env python3
"""
main.py — FastAPI application for BMKG LAWS operational deployment.

Hybrid V9.5 (PIMES) + LightGBM Decoupled Architecture:
    ┌─────────────────────────────────────────────────┐
    │  Incoming Data                                  │
    │       │                                         │
    │       ▼                                         │
    │  [HDF5 Loader]  →  x_img, x_cosmic, meta       │
    │       │                                         │
    │       ▼                                         │
    │  [Storm Gate: Kp/Dst]                           │
    │       │                                         │
    │   ┌───┴──────────────────────┐                  │
    │   │ Kp>4 or Dst<-30?         │                  │
    │   │ YES → bypass V9.5        │ NO → run V9.5    │
    │   └───┬──────────────────────┘                  │
    │       │                                         │
    │       ▼                                         │
    │  [V9.5 PIMES]                                   │
    │    ├── Detection (biner)                        │
    │    ├── Azimuth (station-aware + Bayesian prior) │
    │    └── Storm verdict                            │
    │       │                                         │
    │       ▼                                         │
    │  [LightGBM Magnitude]                           │
    │    └── Magnitude from 53 ULF2 features          │
    │       │                                         │
    │       ▼                                         │
    │  Fused Response                                 │
    └─────────────────────────────────────────────────┘

Endpoints:
    POST /predict        — Full hybrid pipeline (V9.5 + LGBM)
    POST /predict/mag    — LGBM-only magnitude from ULF2 features
    GET  /health         — System health & model status
    GET  /stations       — Station configuration
    GET  /               — API documentation redirect
"""

import math
import time
import logging
import traceback
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any

import numpy as np
import torch
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

# ─── Internal imports ───────────────────────────────────────────────
from app.config import (
    BASE_DIR, CHECKPOINTS_DIR, PRIORS_DIR, H5_DIR,
    LGBM_MAG_MODEL_PATH, V95_CHECKPOINT,
    DEVICE, DETECTION_THRESHOLD,
    KP_STORM_THRESHOLD, DST_STORM_THRESHOLD,
    STATIONS, N_STATIONS, STATION_TO_ID,
    API_HOST, API_PORT, API_LOG_LEVEL,
    API_TITLE, API_VERSION, API_DESCRIPTION,
    LOG_FORMAT, LOG_DATE_FORMAT,
)
from app.utils.hdf5_loader import build_h5_index, load_multi_station, validate_tensor
from app.utils.prior_loader import load_all_priors, get_prior_for_station
from app.utils.kp_dst_gate import storm_gate_decision, StormGateConfig
from app.utils.cwt_generator import generate_cwt_tensor_batch
from app.models.lgbm_model import LgbmMagInference
from app.models.v95_model import V95PimesInference
from app.models.ulf2_inference import extract_features_realtime_batch

# ─── Logging ────────────────────────────────────────────────────────
logging.basicConfig(
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
    level=logging.INFO,
)
logger = logging.getLogger('laws.api')


# ─── Application State ──────────────────────────────────────────────
class AppState:
    """Mutable singleton holding loaded models and data."""
    lgbm_model: Optional[LgbmMagInference] = None
    v95_model: Optional[V95PimesInference] = None
    all_priors: Optional[torch.Tensor] = None
    h5_index: Optional[dict] = None
    storm_config: Optional[StormGateConfig] = None
    models_loaded: bool = False
    startup_time: Optional[str] = None
    load_duration_s: Optional[float] = None

state = AppState()


# ─── Lifespan ───────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models and build HDF5 index on startup."""
    global state
    t0 = time.time()
    logger.info('═' * 60)
    logger.info('BMKG LAWS — Startup Phase (v9.5.1-LGBM)')
    logger.info('═' * 60)

    # 1. Load priors
    logger.info('[1/4] Loading station priors from %s', PRIORS_DIR)
    try:
        state.all_priors = load_all_priors(PRIORS_DIR, DEVICE)
        logger.info('  ✓ %d station priors loaded', state.all_priors.shape[0])
    except Exception as e:
        logger.error('  ✗ Priors failed: %s', e)
        state.all_priors = torch.ones(N_STATIONS, 360, device=DEVICE) / 360

    # 2. Build HDF5 index
    logger.info('[2/4] Building HDF5 index from %s', H5_DIR)
    try:
        state.h5_index = build_h5_index(H5_DIR)
        n_dates = len(state.h5_index)
        n_files = sum(len(v) for v in state.h5_index.values())
        logger.info('  ✓ %d files across %d dates', n_files, n_dates)
    except Exception as e:
        logger.warning('  ✗ HDF5 index build failed: %s (will use on-demand)', e)
        state.h5_index = {}

    # 3. Load LightGBM magnitude model
    logger.info('[3/4] Loading LightGBM magnitude from %s', LGBM_MAG_MODEL_PATH)
    try:
        state.lgbm_model = LgbmMagInference(LGBM_MAG_MODEL_PATH)
        logger.info('  ✓ LGBM loaded (53 features → magnitude)')
    except Exception as e:
        logger.error('  ✗ LGBM load failed: %s', e)
        raise RuntimeError(f'LGBM model load failed: {e}') from e

    # 4. Load V9.5 model
    logger.info('[4/4] Loading V9.5 (PIMES) from %s', V95_CHECKPOINT)
    try:
        state.v95_model = V95PimesInference(V95_CHECKPOINT, DEVICE)
        logger.info('  ✓ V9.5 loaded')
    except Exception as e:
        logger.error('  ✗ V9.5 load failed: %s', e)
        raise RuntimeError(f'V9.5 model load failed: {e}') from e

    # Storm config
    state.storm_config = StormGateConfig(
        kp_threshold=KP_STORM_THRESHOLD,
        dst_threshold=DST_STORM_THRESHOLD,
    )

    state.models_loaded = True
    state.startup_time = datetime.now(timezone.utc).isoformat()
    state.load_duration_s = round(time.time() - t0, 2)

    logger.info('═' * 60)
    logger.info('BMKG LAWS — Ready (%.1fs startup, device=%s)',
                state.load_duration_s, DEVICE)
    logger.info('═' * 60)

    yield

    # Shutdown
    logger.info('BMKG LAWS — Shutdown')


# ─── App ────────────────────────────────────────────────────────────
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


# ─── Request / Response Models ──────────────────────────────────────
# ─── Raw signal models (for real-time extraction) ─────────────────

class RawSignal(BaseModel):
    """Single station's raw magnetometer components."""
    station_id: str = Field(
        ..., 
        description='Station code, e.g., "ALR"',
        examples=['ALR', 'PLU', 'YOG'],
    )
    raw_h: List[float] = Field(
        ..., 
        description='Raw H component (1440 samples, 1 Hz)',
        min_length=100,
        max_length=10000,
    )
    raw_d: List[float] = Field(
        ..., 
        description='Raw D component (1440 samples, 1 Hz)',
        min_length=100,
        max_length=10000,
    )
    raw_z: List[float] = Field(
        ..., 
        description='Raw Z component (1440 samples, 1 Hz)',
        min_length=100,
        max_length=10000,
    )


class PredictRequest(BaseModel):
    """Request body for /predict endpoint (full hybrid pipeline)."""
    date: str = Field(
        ...,
        description='Date string YYYYMMDD',
        examples=['20260101'],
        pattern=r'^\d{8}$',
    )
    kp_index: float = Field(
        ..., 
        description='Kp index (0-9 scale)',
        ge=0.0, le=9.0,
        examples=[2.0, 4.5],
    )
    dst_index: float = Field(
        ..., 
        description='Dst index (nT)',
        ge=-500.0, le=100.0,
        examples=[-10.0, -30.0],
    )
    raw_signals: List[RawSignal] = Field(
        default_factory=list,
        description='Batch of station signals for on-the-fly ULF2 extraction',
        min_items=1,
    )


class MagPredictRequest(BaseModel):
    """Request body for /predict/mag endpoint (LGBM-only magnitude)."""
    ulf2_features: List[float] = Field(
        ...,
        description='53 ULF2 tabular features for magnitude estimation',
        min_length=53,
        max_length=53,
        examples=[[0.5] * 53],  # placeholder example
    )


class PredictionResponse(BaseModel):
    """Hybrid V9.5 + LightGBM prediction response."""
    timestamp: str
    date: str
    pipeline: str = 'ulf2_realtime'

    # V9.5 Gatekeeper
    storm_mode: bool
    storm_reason: str
    kp_raw: float
    dst_raw: float

    # V9.5 Detection
    detection_prob: float
    detection_class: int
    earthquake_detected: bool

    # V9.5 Azimuth
    azimuth_deg: float
    azimuth_sin: float
    azimuth_cos: float
    azimuth_source: str  # 'v95_pimes'

    # LightGBM Magnitude (per-station)
    magnitude: float  # First station magnitude (legacy compatibility)
    magnitude_source: str  # 'lgbm_v2_stable_guarded'
    alert_status: str  # 'NORMAL', 'DANGER', 'WARNING_LOW_MAGNITUDE'
    per_station_magnitudes: Optional[Dict[str, float]] = None  # New: dict of station → magnitude

    # Server profiling
    server_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description='Server-side timing metrics (ms)',
        examples=[{'ulf2_extraction_ms': 45.3, 'lgbm_inference_ms': 8.7}]
    )

    # Audit
    stations_used: List[str]
    n_stations: int
    inference_time_ms: float
    device: str


class MagResponse(BaseModel):
    """LightGBM-only magnitude prediction response."""
    timestamp: str
    pipeline: str = 'lgbm_magnitude'

    magnitude: float
    magnitude_source: str

    inference_time_ms: float


class HealthResponse(BaseModel):
    """System health check response."""
    status: str
    models_loaded: bool
    startup_time: Optional[str]
    load_duration_s: Optional[float]
    device: str
    lgbm_checkpoint: str
    lgbm_features: int
    v95_checkpoint: str
    h5_dates_available: int
    priors_loaded: bool
    storm_config: dict


# ─── Endpoints ──────────────────────────────────────────────────────
@app.get('/', include_in_schema=False)
async def root():
    """Redirect to API docs."""
    return RedirectResponse(url='/docs')


@app.get('/health', response_model=HealthResponse, tags=['System'])
async def health_check():
    """System health and model status."""
    return HealthResponse(
        status='ok' if state.models_loaded else 'degraded',
        models_loaded=state.models_loaded,
        startup_time=state.startup_time,
        load_duration_s=state.load_duration_s,
        device=DEVICE,
        lgbm_checkpoint=str(LGBM_MAG_MODEL_PATH),
        lgbm_features=53,
        v95_checkpoint=str(V95_CHECKPOINT),
        h5_dates_available=len(state.h5_index) if state.h5_index else 0,
        priors_loaded=state.all_priors is not None,
        storm_config={
            'kp_threshold': KP_STORM_THRESHOLD,
            'dst_threshold': DST_STORM_THRESHOLD,
        },
    )


@app.get('/stations', tags=['System'])
async def list_stations():
    """Station configuration and prior status."""
    priors_available = {}
    for code in STATIONS:
        if code == 'UNK':
            continue
        prior_path = PRIORS_DIR / f'prior_{code}.pt'
        priors_available[code] = prior_path.exists()

    return {
        'stations': STATIONS,
        'n_stations': N_STATIONS,
        'station_to_id': STATION_TO_ID,
        'priors_available': priors_available,
        'h5_dates': sorted(state.h5_index.keys()) if state.h5_index else [],
    }


@app.post('/predict', response_model=PredictionResponse, tags=['Inference'])
async def predict_hybrid(req: PredictRequest):
    """
    Full hybrid V9.5 → LightGBM pipeline (Real-Time In-Memory).
    """
    if not state.models_loaded:
        raise HTTPException(status_code=503, detail='Models not loaded')

    t_start = time.perf_counter()
    metrics = {}

    # ── 1. Storm Gate Check ──
    kp_norm = req.kp_index / 9.0
    dst_norm = math.tanh(req.dst_index / 50.0)
    
    gate = storm_gate_decision(
        kp_norm, dst_norm,
        req.kp_index, req.dst_index,
        state.storm_config,
    )
    storm_mode = gate['storm_mode']

    # ── 2. Real-Time CWT Generation ──
    t_cwt_start = time.perf_counter()
    n_stations = len(req.raw_signals)
    stations_used = [sig.station_id for sig in req.raw_signals]
    
    raw_dicts = []
    for sig in req.raw_signals:
        raw_dicts.append({
            'raw_h': sig.raw_h,
            'raw_d': sig.raw_d,
            'raw_z': sig.raw_z
        })
        
    x_img = generate_cwt_tensor_batch(raw_dicts, normalize=True)
    metrics['cwt_generation_ms'] = round((time.perf_counter() - t_cwt_start) * 1000, 2)

    # ── 3. V9.5 PIMES Inference ──
    t_v95_start = time.perf_counter()
    
    # Prepare batch inputs
    x_cosmic = torch.tensor([[kp_norm, dst_norm]] * n_stations, dtype=torch.float32)
    
    station_ids = []
    prior_vecs = []
    for st in stations_used:
        stn_id, prior_vec = get_prior_for_station(st, state.all_priors)
        station_ids.append(stn_id)
        prior_vecs.append(prior_vec)
        
    station_ids_t = torch.tensor(station_ids, dtype=torch.long)
    prior_vecs_t = torch.stack(prior_vecs)

    v95_result = None
    if not storm_mode and state.v95_model is not None:
        try:
            v95_result = state.v95_model.predict_batch(
                x_img, x_cosmic, station_ids_t, prior_vecs_t
            )
        except Exception as e:
            logger.error('V9.5 inference failed: %s', e)

    metrics['v95_inference_ms'] = round((time.perf_counter() - t_v95_start) * 1000, 2)

    # Summarize V9.5 results (take max prob across stations)
    if v95_result:
        max_prob_idx = np.argmax(v95_result['detection_probs'])
        detection_prob = v95_result['detection_probs'][max_prob_idx]
        detection_class = v95_result['detection_classes'][max_prob_idx]
        azimuth_deg = v95_result['azimuths_deg'][max_prob_idx]
        # Calculate sin/cos
        azimuth_sin = math.sin(math.radians(azimuth_deg))
        azimuth_cos = math.cos(math.radians(azimuth_deg))
        azimuth_source = 'v95_pimes'
    else:
        detection_prob = 0.0
        detection_class = 0
        azimuth_deg = 0.0
        azimuth_sin = 0.0
        azimuth_cos = 1.0
        azimuth_source = 'fallback'

    earthquake_detected = bool(detection_prob > DETECTION_THRESHOLD)

    # ── 4. ULF2 Extraction & LightGBM Magnitude ──
    magnitude = 0.0
    magnitude_source = 'unavailable'
    per_station_magnitudes = {}
    
    if earthquake_detected:
        t_ulf2_start = time.perf_counter()
        try:
            # Format for ulf2 extractor
            batch_for_ulf2 = {}
            for sig in req.raw_signals:
                batch_for_ulf2[sig.station_id] = (
                    np.array(sig.raw_h, dtype=np.float64),
                    np.array(sig.raw_d, dtype=np.float64),
                    np.array(sig.raw_z, dtype=np.float64)
                )
            
            # Extract features (N_stations, 53)
            features_matrix = extract_features_realtime_batch(batch_for_ulf2)
            metrics['ulf2_extraction_ms'] = round((time.perf_counter() - t_ulf2_start) * 1000, 2)
            
            t_lgbm_start = time.perf_counter()
            
            # Predict magnitude per station
            if state.lgbm_model is not None:
                raw_station_magnitudes = {}
                for i, st in enumerate(sorted(batch_for_ulf2.keys())):
                    raw_mag = float(state.lgbm_model.predict(features_matrix[i].tolist()))
                    # Guardrail: ULF magnitude regression is trend-level only.
                    # Clip to empirical operational range to avoid unsafe extremes.
                    clipped_mag = float(np.clip(raw_mag, 3.0, 6.5))
                    raw_station_magnitudes[st] = raw_mag
                    per_station_magnitudes[st] = clipped_mag
                
                # Take average clipped magnitude across stations
                magnitude = float(np.mean(list(per_station_magnitudes.values())))
                magnitude = float(np.clip(magnitude, 3.0, 6.5))
                magnitude_source = 'lgbm_v2_stable_guarded'
                metrics['lgbm_raw_magnitude_mean'] = round(float(np.mean(list(raw_station_magnitudes.values()))), 3)
                metrics['lgbm_guardrail_min'] = 3.0
                metrics['lgbm_guardrail_max'] = 6.5
                
            metrics['lgbm_inference_ms'] = round((time.perf_counter() - t_lgbm_start) * 1000, 2)
            
        except Exception as e:
            logger.error('ULF2/LGBM failed: %s', e)
            magnitude_source = 'lgbm_error'

    t_elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
    metrics['total_inference_ms'] = t_elapsed_ms

    alert_status = 'NORMAL'
    if earthquake_detected:
        alert_status = 'DANGER'
        # Confidence discounting: magnitude regression is weakly identifiable.
        # Low-magnitude detections should not escalate as full DANGER alerts.
        if magnitude < 4.5:
            alert_status = 'WARNING_LOW_MAGNITUDE'

    return PredictionResponse(
        timestamp=datetime.now(timezone.utc).isoformat(),
        date=req.date,
        storm_mode=storm_mode,
        storm_reason=gate['reason'],
        kp_raw=req.kp_index,
        dst_raw=req.dst_index,
        detection_prob=detection_prob,
        detection_class=detection_class,
        earthquake_detected=earthquake_detected,
        azimuth_deg=azimuth_deg,
        azimuth_sin=azimuth_sin,
        azimuth_cos=azimuth_cos,
        azimuth_source=azimuth_source,
        magnitude=magnitude,
        magnitude_source=magnitude_source,
        alert_status=alert_status,
        per_station_magnitudes=per_station_magnitudes,
        stations_used=stations_used,
        n_stations=n_stations,
        inference_time_ms=t_elapsed_ms,
        device=DEVICE,
        server_metrics=metrics
    )


@app.post('/predict/mag', response_model=MagResponse, tags=['Inference'])
async def predict_magnitude(req: MagPredictRequest):
    """
    LightGBM-only magnitude estimation from 53 ULF2 features.

    Bypasses V9.5 gatekeeper and HDF5 loading.
    For direct magnitude estimation with pre-computed features.
    """
    if not state.models_loaded or state.lgbm_model is None:
        raise HTTPException(status_code=503, detail='LightGBM model not loaded')

    t_start = time.time()

    try:
        magnitude = state.lgbm_model.predict(req.ulf2_features)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'LGBM inference failed: {e}')

    t_elapsed = (time.time() - t_start) * 1000

    return MagResponse(
        timestamp=datetime.now(timezone.utc).isoformat(),
        magnitude=magnitude,
        magnitude_source='lgbm_hub7d',
        inference_time_ms=round(t_elapsed, 1),
    )


# ─── Run ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        'app.api.main:app',
        host=API_HOST,
        port=API_PORT,
        reload=False,
        log_level=API_LOG_LEVEL,
    )
