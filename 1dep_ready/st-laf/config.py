"""
st-laf — Spatio-Temporal Lithosphere Activity Forecaster
=========================================================
Consumes 128D projections from LAWS Shared Core, applies temporal
context + spatial fusion, produces activity index (0-100) per station.

Architecture:
  SharedCore (laws) ──128D──→ ┌─────────────────────┐
                              │  st-laf              │
                              │  ├─ Temporal sliding │
                              │  ├─ Spatial fusion   │
                              │  └─ Activity index   │
                              └─────────────────────┘
"""

import os
from pathlib import Path

# ── Root ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ── Shared LAWS resources ──────────────────────────────────────────────
LAWS_DIR = BASE_DIR.parent / 'laws'
LAWS_CHECKPOINTS = LAWS_DIR / 'checkpoints'
LAWS_PRIORS = LAWS_DIR / 'priors' / 'priors'
LAWS_CORE = LAWS_DIR / 'core'

# ── st-laf paths ────────────────────────────────────────────────────────
LOGS_DIR = BASE_DIR / 'logs'
DATA_DIR = BASE_DIR / 'data'

# ── Temporal buffer ────────────────────────────────────────────────────
WINDOW_SIZE = int(os.environ.get('STLAF_WINDOW', '10'))      # timesteps
STRIDE = int(os.environ.get('STLAF_STRIDE', '1'))            # overlap
MAX_HISTORY_HOURS = int(os.environ.get('STLAF_HISTORY', '48'))

# ── Inference ──────────────────────────────────────────────────────────
DEVICE = os.environ.get('STLAF_DEVICE', 'cpu')
FALLBACK_PRIOR = float(os.environ.get('STLAF_FALLBACK', '2.0'))  # z-score threshold

# ── Activity thresholds ────────────────────────────────────────────────
ACTIVITY_STATES = {
    'QUIET':   [0.0, 0.25],
    'MONITOR': [0.25, 0.50],
    'REVIEW':  [0.50, 0.75],
    'ALERT':   [0.75, 1.00],
}

# ── API ─────────────────────────────────────────────────────────────────
API_HOST = os.environ.get('STLAF_HOST', '0.0.0.0')
API_PORT = int(os.environ.get('STLAF_PORT', '8100'))
API_LOG_LEVEL = os.environ.get('STLAF_LOG_LEVEL', 'info')
API_TITLE = 'ST-LAF — Spatio-Temporal Lithosphere Activity Forecaster'
API_VERSION = '1.0.0'

# ── Stations ────────────────────────────────────────────────────────────
STATIONS = [
    'ALR', 'AMB', 'CLP', 'GTO', 'KPY', 'LPS', 'LUT', 'LWA', 'LWK',
    'MLB', 'PLU', 'ROT', 'SBG', 'SCN', 'SKB', 'SMI', 'SRG', 'SRO',
    'TNT', 'TRD', 'TRT', 'YOG',
]
N_STATIONS = len(STATIONS)
STATION_TO_ID = {s: i for i, s in enumerate(STATIONS)}
