#!/usr/bin/env python3
"""
main.py — FastAPI application for ST-LAF.

Endpoints:
    POST /ingest          — feed 128D projection, get activity index
    POST /ingest/batch    — feed multiple stations at once
    GET  /activity        — latest activity result
    GET  /health          — system health
    GET  /stations        — station list
    GET  /                — docs redirect
"""

import sys
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from contextlib import asynccontextmanager
from typing import List, Dict, Optional, Any

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

# Ensure app is importable
_HERE = Path(__file__).resolve().parent.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from app.config import (
    API_HOST, API_PORT, API_LOG_LEVEL, API_TITLE, API_VERSION,
    STATIONS, N_STATIONS, STATION_TO_ID,
)
from app.pipeline import (
    ingest, ingest_batch, get_state, reset_state,
)

logging.basicConfig(
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO,
)
logger = logging.getLogger('st-laf.api')


# ─── Request / Response Models ────────────────────────────────────────

class IngestRequest(BaseModel):
    station: str = Field(..., description='Station code', examples=['ALR'])
    projection: List[float] = Field(
        ..., min_length=128, max_length=128,
        description='128D L2-normalized projection vector from LAWS SharedCore'
    )
    timestamp: Optional[str] = Field(
        None,
        description='ISO timestamp (defaults to server now)',
        examples=['2026-01-15T00:00:00Z'],
    )


class BatchIngestRequest(BaseModel):
    projections: Dict[str, List[float]] = Field(
        ...,
        description='{station_code: [128 floats]}',
        examples=[{'ALR': [0.1]*128, 'SCN': [0.2]*128}],
    )


class ActivityResponse(BaseModel):
    timestamp: str
    activity_index: float = Field(..., ge=0, le=100)
    system_status: str
    components: Dict[str, float]
    spatial: Dict[str, Any]
    per_station: Dict[str, float]
    n_stations_active: int


class BatchIngestResponse(BaseModel):
    timestamp: str
    activity: ActivityResponse


class HealthResponse(BaseModel):
    status: str
    version: str
    stations_configured: int
    stations_active: int
    oldest_timestamp: Optional[str]


# ─── Lifespan ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('═' * 60)
    logger.info('ST-LAF — Starting Spatio-Temporal Lithosphere Activity Forecaster')
    logger.info('═' * 60)
    logger.info(f'  Stations configured: {N_STATIONS}')
    logger.info('═' * 60)
    yield
    logger.info('ST-LAF — Shutdown')


# ─── App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


# ─── Endpoints ────────────────────────────────────────────────────────

@app.get('/', include_in_schema=False)
async def root():
    return RedirectResponse(url='/docs')


@app.get('/health', response_model=HealthResponse, tags=['System'])
async def health():
    state = get_state()
    return HealthResponse(
        status='ok',
        version=API_VERSION,
        stations_configured=N_STATIONS,
        stations_active=state.get('stations_active', 0),
        oldest_timestamp=state.get('oldest_timestamp'),
    )


@app.get('/stations', tags=['System'])
async def list_stations():
    return {
        'stations': STATIONS,
        'n_stations': N_STATIONS,
        'station_to_id': STATION_TO_ID,
    }


@app.post('/ingest', response_model=ActivityResponse, tags=['Inference'])
async def ingest_projection(req: IngestRequest):
    """
    Feed one station's 128D projection.

    Returns updated activity index combining temporal + spatial context.
    """
    if req.station not in STATION_TO_ID:
        raise HTTPException(
            status_code=400,
            detail=f'Unknown station: {req.station}. Valid: {STATIONS}',
        )

    proj = np.array(req.projection, dtype=np.float32)

    ts = None
    if req.timestamp:
        try:
            ts = datetime.fromisoformat(req.timestamp.replace('Z', '+00:00'))
        except ValueError:
            try:
                ts = datetime.strptime(req.timestamp, '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f'Invalid timestamp format: {req.timestamp}',
                )

    t0 = time.perf_counter()
    result = ingest(req.station, proj, ts)
    latency_ms = (time.perf_counter() - t0) * 1000

    return ActivityResponse(
        timestamp=datetime.now(timezone.utc).isoformat(),
        activity_index=result['activity_index'],
        system_status=result['system_status'],
        components=result['components'],
        spatial=result['spatial'],
        per_station=result['per_station'],
        n_stations_active=result['spatial']['n_stations'],
    )


@app.post('/ingest/batch', response_model=BatchIngestResponse, tags=['Inference'])
async def ingest_batch_projections(req: BatchIngestRequest):
    """
    Feed multiple stations' projections at once.
    """
    if not req.projections:
        raise HTTPException(status_code=400, detail='Empty projections dict')

    unknown = [s for s in req.projections if s not in STATION_TO_ID]
    if unknown:
        raise HTTPException(status_code=400, detail=f'Unknown stations: {unknown}')

    projections_np = {}
    for stn, proj in req.projections.items():
        projections_np[stn] = np.array(proj, dtype=np.float32)

    t0 = time.perf_counter()
    result = ingest_batch(projections_np)
    latency_ms = (time.perf_counter() - t0) * 1000

    return BatchIngestResponse(
        timestamp=datetime.now(timezone.utc).isoformat(),
        activity=ActivityResponse(
            timestamp=datetime.now(timezone.utc).isoformat(),
            activity_index=result['activity_index'],
            system_status=result['system_status'],
            components=result['components'],
            spatial=result['spatial'],
            per_station=result['per_station'],
            n_stations_active=result['spatial']['n_stations'],
        ),
    )


@app.get('/activity', response_model=ActivityResponse, tags=['System'])
async def get_latest_activity():
    """Return the most recent activity computation."""
    state = get_state()
    if state.get('last_activity') is None:
        raise HTTPException(status_code=404, detail='No activity computed yet. POST /ingest first.')
    a = state['last_activity']
    return ActivityResponse(
        timestamp=datetime.now(timezone.utc).isoformat(),
        activity_index=a['activity_index'],
        system_status=a['system_status'],
        components=a['components'],
        spatial=a['spatial'],
        per_station=a['per_station'],
        n_stations_active=a['spatial']['n_stations'],
    )


@app.post('/reset', tags=['System'])
async def reset():
    """Clear all temporal buffers."""
    reset_state()
    return {'status': 'cleared', 'timestamp': datetime.now(timezone.utc).isoformat()}


# ─── Run ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        'app.api.main:app',
        host=API_HOST,
        port=API_PORT,
        reload=False,
        log_level=API_LOG_LEVEL,
    )
