"""
Activity Estimator — compute 0-100 activity score from temporal + spatial.

Formula:
    temporal_activity = f(temporal z-score deviation)
    spatial_activity  = f(spatial dispersion, n_stations)
    combined = w_t * temporal + w_s * spatial

Returns per-station AND global activity index.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple


class ActivityEstimator:
    """Compute lithosphere activity index (0-100)."""

    def __init__(
        self,
        temporal_weight: float = 0.6,
        spatial_weight: float = 0.3,
        baseline_weight: float = 0.1,
        fallback_z: float = 2.0,
    ):
        self.w_t = temporal_weight
        self.w_s = spatial_weight
        self.w_b = baseline_weight
        self.fallback_z = fallback_z

    def estimate(
        self,
        temporal_raw: Dict[str, Optional[float]],  # station → z-mean from buffer
        spatial_fused: Dict,                        # output from SpatialFuser.fuse()
        baseline_prior: Optional[float] = None,     # optional historical baseline
    ) -> Dict:
        """
        Returns:
            {
                'activity_index': float 0-100 (global),
                'per_station': {station: float 0-100},
                'components': {
                    'temporal': float,
                    'spatial': float,
                    'baseline': float,
                },
                'system_status': str,
            }
        """

        # ── Per-station temporal ──
        per_station_scores = {}
        temporal_values = []
        for station, z_mean in temporal_raw.items():
            if z_mean is not None:
                # z=0 → score 0, z=2 → score 50, z=4 → score 100
                score = min(100, z_mean / self.fallback_z * 50)
            else:
                score = 0.0
            per_station_scores[station] = round(score, 2)
            temporal_values.append(score)

        # ── Global temporal (mean across stations) ──
        temporal_global = float(np.mean(temporal_values)) if temporal_values else 0.0

        # ── Spatial component ──
        n = spatial_fused.get('n_stations', 0)
        if n >= 1:
            # More stations with wider spread = higher spatial activity
            cluster_radius = spatial_fused.get('cluster_radius', 0.0)
            # Normalize: 0km→0, 1000km→100
            spatial_global = min(100, cluster_radius / 10.0)
            # Bonus for many stations
            spatial_global = spatial_global * min(1.0, n / 5.0)
        else:
            spatial_global = 0.0

        # ── Baseline prior ──
        if baseline_prior is not None:
            baseline_score = min(100, baseline_prior * 25)
        else:
            baseline_score = 50.0  # neutral

        # ── Combined ──
        combined = (
            self.w_t * temporal_global +
            self.w_s * spatial_global +
            self.w_b * baseline_score
        )
        combined = float(np.clip(combined, 0, 100))

        # ── System status ──
        if combined < 25:
            status = 'QUIET'
        elif combined < 50:
            status = 'MONITOR'
        elif combined < 75:
            status = 'REVIEW'
        else:
            status = 'ALERT'

        return {
            'activity_index': round(combined, 2),
            'per_station': per_station_scores,
            'components': {
                'temporal': round(temporal_global, 2),
                'spatial': round(spatial_global, 2),
                'baseline': round(baseline_score, 2),
            },
            'n_stations_active': n,
            'system_status': status,
        }
