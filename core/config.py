"""
config — Central configuration for the operational kernel.
"""
from pathlib import Path
from typing import Dict, Any
import json

# Default paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # magbind/../../
MAGBIND = PROJECT_ROOT / "magbind"
CACHE_DIR = MAGBIND / "cache"
FEATURE_CACHE_DIR = CACHE_DIR / "feature_cache"
REGISTRY_PATH = MAGBIND / "core_feature_registry.csv"
MODEL_DIR = MAGBIND / "models"
RELEASE_DIR = MAGBIND / "release"

# Operational defaults
ALERT_THRESHOLD = 0.5
WATCH_THRESHOLD = 0.3
MIN_SAMPLES_FOR_EVALUATION = 10
N_BOOTSTRAP = 100
RANDOM_STATE = 42

# Metric weights for ODRI
ODRI_WEIGHTS = {
    "TII": 0.25,
    "OUI": 0.25,
    "DIS": 0.20,
    "DVI": 0.15,
    "RSI": 0.15,
}


def ensure_dirs():
    """Create all operational directories."""
    for d in [CACHE_DIR, FEATURE_CACHE_DIR, MODEL_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def get_config() -> Dict[str, Any]:
    """Return full configuration as dict."""
    return {
        "project_root": str(PROJECT_ROOT),
        "alert_threshold": ALERT_THRESHOLD,
        "watch_threshold": WATCH_THRESHOLD,
        "odri_weights": ODRI_WEIGHTS,
        "min_samples": MIN_SAMPLES_FOR_EVALUATION,
        "n_bootstrap": N_BOOTSTRAP,
        "random_state": RANDOM_STATE,
    }
