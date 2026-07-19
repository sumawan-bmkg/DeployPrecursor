#!/usr/bin/env python3
"""
config.py — Central configuration for LAWS Operational Deployment.

All paths, thresholds, and model parameters in one place.
Environment variable overrides supported via LAWS_* prefix.
"""

import os
from pathlib import Path

# ─── Directory Structure ────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
CHECKPOINTS_DIR = BASE_DIR / 'checkpoints'
LOGS_DIR = BASE_DIR / 'logs'
PRIORS_DIR = BASE_DIR / 'priors'

# HDF5 data directory (adjust for production server)
H5_DIR = Path(os.environ.get(
    'LAWS_H5_DIR',
    str(BASE_DIR.parent / '2026' / 'scalogram')
))

# ─── Model Checkpoints ─────────────────────────────────────────────
LGBM_MAG_MODEL_PATH = CHECKPOINTS_DIR / 'lgbm_mag_regression_v2_stable.pkl'
V95_CHECKPOINT = CHECKPOINTS_DIR / 'v95_pimes_champion.pth'

# ─── Device ─────────────────────────────────────────────────────────
DEVICE = os.environ.get('LAWS_DEVICE', 'cuda')  # 'cuda' or 'cpu'

# ─── Inference Settings ────────────────────────────────────────────
# Detection threshold
DETECTION_THRESHOLD = 0.5  # P(class=1) > this → earthquake detected

# ─── Storm Gate Thresholds ─────────────────────────────────────────
KP_STORM_THRESHOLD = 4.0     # Kp > this → storm mode (bypass V9.5)
DST_STORM_THRESHOLD = -30.0  # Dst < this → storm mode

# ─── Station Configuration ─────────────────────────────────────────
STATIONS = [
    'ALR', 'AMB', 'CLP', 'GTO', 'KPY', 'LPS', 'LUT', 'LWA', 'LWK',
    'MLB', 'PLU', 'ROT', 'SBG', 'SCN', 'SKB', 'SMI', 'SRG', 'SRO',
    'TNT', 'TRD', 'TRT', 'YOG', 'UNK',
]
N_STATIONS = len(STATIONS)
STATION_TO_ID = {s: i for i, s in enumerate(STATIONS)}

# ─── API Configuration ─────────────────────────────────────────────
API_HOST = os.environ.get('LAWS_HOST', '0.0.0.0')
API_PORT = int(os.environ.get('LAWS_PORT', '8000'))
API_LOG_LEVEL = os.environ.get('LAWS_LOG_LEVEL', 'info')
API_TITLE = 'BMKG LAWS — Geomagnetic lithosphere activity warning'
API_VERSION = '9.5.1'
API_DESCRIPTION = """
**Lithosphere Activity Warning System (LAWS)**

Hybrid V9.5 + LightGBM Tabular pipeline:
- **V9.5 PIMES**: Gatekeeper (Kp/Dst storm filter) + Detection + Azimuth
- **LightGBM Huber Regressor**: Magnitude estimation (53 ULF2 features)

Endpoints:
- `POST /predict` — Full hybrid prediction (V9.5 gate → LGBM magnitude)
- `GET /health` — System health check
- `GET /stations` — Station list and configuration
"""

# ─── Logging ────────────────────────────────────────────────────────
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
