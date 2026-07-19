"""
ST-LAF Pipeline — orchestrates temporal buffer + spatial fuser + activity estimator.

Single entry point: ingest(station, proj_128d) → activity dict.
"""

import sys
import numpy as np
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

# Ensure app is importable
_HERE = Path(__file__).resolve().parent.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from app.config import (
    WINDOW_SIZE, MAX_HISTORY_HOURS, FALLBACK_PRIOR, DEVICE,
)
from app.models.temporal_buffer import TemporalBuffer
from app.models.spatial_fuser import SpatialFuser
from app.models.activity_estimator import ActivityEstimator

_STATE = {
    'buffer': TemporalBuffer(window_size=WINDOW_SIZE, max_history_hours=MAX_HISTORY_HOURS),
    'fuser': SpatialFuser(),
    'estimator': ActivityEstimator(fallback_z=FALLBACK_PRIOR),
    'last_output': None,
}


def ingest(
    station: str,
    proj_128d: np.ndarray,
    timestamp: Optional[datetime] = None,
) -> Dict:
    """
    Feed one station projection → update state → return activity.

    Args:
        station: station code (e.g. 'ALR')
        proj_128d: (128,) float32/64 L2-normalized projection
        timestamp: optional, defaults to now

    Returns:
        dict with activity_index, per_station, system_status, components
    """
    buf = _STATE['buffer']
    fuser = _STATE['fuser']
    estimator = _STATE['estimator']

    # 1. Push to temporal buffer
    buf.push(station, proj_128d, timestamp)

    # 2. Get latest projection per station
    all_windows = buf.get_all_station_windows()
    latest = {}
    for s, win in all_windows.items():
        if win is not None:
            latest[s] = win[-1]  # most recent projection

    # 3. Spatial fusion
    fused = fuser.fuse(latest)

    # 4. Temporal activity per station
    temporal_raw = {}
    for s in list(latest.keys()):
        temporal_raw[s] = buf.recent_activity_raw(s)

    # 5. Estimate combined activity
    result = estimator.estimate(temporal_raw, fused, baseline_prior=None)

    # 6. Attach spatial metadata
    result['spatial'] = {
        'n_stations': fused['n_stations'],
        'stations_used': fused['stations_used'],
        'mean_inter_distance_km': fused.get('mean_inter_distance', 0),
        'cluster_radius_km': fused.get('cluster_radius', 0),
    }

    _STATE['last_output'] = result
    return result


def ingest_batch(
    projections: Dict[str, np.ndarray],
    timestamps: Optional[Dict[str, datetime]] = None,
) -> Dict:
    """
    Feed multiple stations at once.

    Args:
        projections: {station: (128,) proj}
        timestamps:  optional {station: datetime}

    Returns:
        dict with aggregated activity result
    """
    if timestamps is None:
        timestamps = {}
    for stn, proj in projections.items():
        ts = timestamps.get(stn, None)
        buf = _STATE['buffer']
        buf.push(stn, proj, ts)

    # Recompute with all new data
    all_windows = _STATE['buffer'].get_all_station_windows()
    latest = {}
    for s, win in all_windows.items():
        if win is not None:
            latest[s] = win[-1]

    fused = _STATE['fuser'].fuse(latest)
    temporal_raw = {}
    for s in list(latest.keys()):
        temporal_raw[s] = _STATE['buffer'].recent_activity_raw(s)

    result = _STATE['estimator'].estimate(temporal_raw, fused, baseline_prior=None)
    result['spatial'] = {
        'n_stations': fused['n_stations'],
        'stations_used': fused['stations_used'],
        'mean_inter_distance_km': fused.get('mean_inter_distance', 0),
        'cluster_radius_km': fused.get('cluster_radius', 0),
    }
    _STATE['last_output'] = result
    return result


def get_state() -> Dict:
    """Get current pipeline state summary."""
    buf = _STATE['buffer']
    return {
        'stations_active': buf.station_count(),
        'oldest_timestamp': str(buf.oldest_timestamp()),
        'last_activity': _STATE['last_output'],
    }


def reset_state() -> None:
    """Clear all temporal buffers."""
    _STATE['buffer'].clear()
    _STATE['last_output'] = None
