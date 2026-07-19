"""
Temporal Buffer — sliding window state per station.

Stores last N 128D projections per station with timestamps.
Provides rolling mean/std for anomaly detection.
"""

import numpy as np
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


class TemporalBuffer:
    """Per-station sliding window of projection vectors."""

    def __init__(self, window_size: int = 10, max_history_hours: int = 48):
        self.window_size = window_size
        self.max_history_hours = max_history_hours
        # station_code → list of (timestamp, proj_128d)
        self._buffers: Dict[str, List[Tuple[datetime, np.ndarray]]] = {}

    def push(self, station: str, proj: np.ndarray, ts: Optional[datetime] = None) -> None:
        """Add a projection vector for a station."""
        if ts is None:
            ts = datetime.utcnow()
        if station not in self._buffers:
            self._buffers[station] = []
        self._buffers[station].append((ts, proj.astype(np.float64).flatten()))

        # Trim to max window
        if len(self._buffers[station]) > self.window_size * 2:  # 2x for smooth
            self._buffers[station] = self._buffers[station][-self.window_size * 2:]

        # Age out old entries
        cutoff = ts - timedelta(hours=self.max_history_hours)
        self._buffers[station] = [
            (t, v) for t, v in self._buffers[station]
            if t >= cutoff
        ]

    def get_window(self, station: str) -> Optional[np.ndarray]:
        """
        Get sliding window as (N, 128) array.
        Returns None if insufficient data.
        """
        if station not in self._buffers or len(self._buffers[station]) < 2:
            return None
        entries = self._buffers[station][-self.window_size:]
        return np.stack([v for _, v in entries])

    def get_all_station_windows(self) -> Dict[str, Optional[np.ndarray]]:
        """Get windows for all stations that have data."""
        return {s: self.get_window(s) for s in self._buffers}

    def get_baseline(self, station: str) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Compute mean + std of recent window.
        Returns (mean_128, std_128) or None.
        """
        window = self.get_window(station)
        if window is None or len(window) < 2:
            return None
        return (np.mean(window, axis=0), np.std(window, axis=0) + 1e-8)

    def recent_activity_raw(self, station: str) -> Optional[float]:
        """
        Recent activity: mean z-score deviation from baseline.
        Higher = more anomalous recent behavior.
        """
        baseline = self.get_baseline(station)
        if baseline is None:
            return None
        mean_v, std_v = baseline
        latest = self._buffers[station][-1][1]
        z_scores = np.abs((latest - mean_v) / std_v)
        return float(np.clip(np.mean(z_scores), 0, 10))  # 0-10 scale

    def clear(self) -> None:
        self._buffers.clear()

    def station_count(self) -> int:
        return len(self._buffers)

    def oldest_timestamp(self) -> Optional[datetime]:
        all_ts = [t for buf in self._buffers.values() for t, _ in buf]
        return min(all_ts) if all_ts else None
