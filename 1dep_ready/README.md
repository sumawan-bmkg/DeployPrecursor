# PIMES V9.5 — Deployment Package

Deployment artifacts for LAWS (Lithosphere Anomaly Warning System) and ST-LAF
(Spatio-Temporal Lithosphere Activity Forecaster).

## Directory Structure

```
1dep_ready/
├── models/                      ← LAWS inference checkpoints
│   ├── v95_pimes_champion.pth       (37 MB) V9.5 CNN backbone
│   ├── v8_supcon_best.pth           (36 MB) V8 SupCon encoder
│   ├── lgbm_mag_regression_*.pkl    LightGBM magnitude heads (×3)
│   ├── faiss_laws.index             k-NN analogue database
│   ├── quantile_p10/50/90.joblib    Quantile bounds (p10/p50/p90)
│   └── readout_head.joblib          Weighted readout regression
│
├── priors/priors/               ← Station-specific priors (22 stations)
│   ├── prior_ALR.pt ... prior_YOG.pt
│   └── prior_*_metadata.txt
│
├── core/                        ← Shared encoder (ONNX + PyTorch)
│   ├── v8_supcon_encoder.py         SharedEncoder singleton
│   └── weights/v8_supcon_merged.onnx (36 MB)
│
├── laws/                        ← API server + utilities
│   ├── Dockerfile                   Docker build
│   ├── docker-compose.yml           API + harvester
│   ├── requirements.txt             Python deps
│   ├── app/api/main.py              FastAPI inference endpoints
│   ├── app/config.py                Central configuration
│   ├── app/models/*.py              V95, LGBM, ULF2, GNN wrappers
│   ├── app/utils/*.py               CWT, HDF5, gate, harvester
│   └── inference_v95.py             CLI inference runner
│
├── st-laf/                      ← Activity Forecaster (port 8100)
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   ├── test_smoke.py                5-step validation
│   └── app/                         API + models
│
├── edge/                        ← Jetson Nano edge inference
│   ├── edge_inference.py            ONNX Runtime (zero PyTorch)
│   ├── preprocessing_pipeline.py
│   ├── models/                      INT8 + FP32 ONNX models
│   └── Dockerfile
│
└── data/h5/                     ← Sample HDF5 for testing
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| LAWS API | 8000 | V9.5 inference + storm gate |
| ST-LAF | 8100 | Activity index (0-100) |
| Edge | ONNX | Jetson Nano local inference |

## Quick Start

### LAWS API
```bash
cd laws
docker-compose up -d
curl http://localhost:8000/health
```

### ST-LAF
```bash
cd st-laf
docker-compose up -d
curl http://localhost:8100/health
```

### Edge (Jetson Nano)
```bash
cd edge
pip install -r requirements_edge.txt
python edge_inference.py --stream --station ALR
```

## Data Flow

```
Raw BMKG Binary (.raw)
        │
        ▼
Parser (geomagnetic_fetcher.py)
  → 86400 samples × (H, D, Z)
        │
        ▼
CWT Generator (cwt_generator.py)
  → (3, 128, 1440) scalogram tensor
        │
        ▼
SharedEncoder (v8_supcon_encoder.py)
  → 128D L2-normalized projection
        │
        ├─────────────────────┐
        ▼                     ▼
    LAWS API              ST-LAF API
    (V9.5 storm gate)     (temporal + spatial
     + magnitude)          activity index)
```

## Key Models

| Model | Type | Input | Output |
|-------|------|-------|--------|
| V9.5 PIMES | CNN | (1,3,128,1440) | storm probability |
| V8 SupCon | EfficientNet-B1+GRU+GNN | (1,3,128,1440) | 128D projection |
| LGBM | LightGBM | 128D | magnitude (Richter) |
| Quantile | HGBR | 128D | p10/p50/p90 bounds |
| FAISS | k-NN | 128D | historical analogues |
| ST-LAF | Temporal+Spatial | 128D × N_stations | activity 0-100 |

## Stations (22)

ALR, AMB, CLP, GTO, KPY, LPS, LUT, LWA, LWK, MLB, PLU, ROT, SBG, SCN,
SKB, SMI, SRG, SRO, TNT, TRD, TRT, YOG
