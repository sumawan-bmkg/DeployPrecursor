"""
Spatial Fuser — combine 128D projections across stations.

Two modes:
1. MEAN: simple mean embedding → global activity
2. GRAPH: station graph adjacency → GNN-style message passing (future)

Output: fused_128d, per_station_scores.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple

# Station coordinates (proxy adjacency: inverse distance weighting)
STATION_COORDS = {
    'ALR': (-8.15, 115.09), 'AMB': (-6.84, 113.76), 'CLP': (-7.16, 112.74),
    'GTO': (0.53, 123.56),   'KPY': (-8.63, 115.52), 'LPS': (-8.45, 115.60),
    'LUT': (-10.17, 123.56), 'LWA': (-8.33, 116.35), 'LWK': (-2.44, 121.35),
    'MLB': (-2.63, 107.63),  'PLU': (-6.85, 107.61), 'ROT': (-1.46, 123.09),
    'SBG': (-1.00, 100.46),  'SCN': (-10.28, 105.24), 'SKB': (-2.09, 105.11),
    'SMI': (-0.87, 100.64),  'SRG': (-3.31, 114.59), 'SRO': (-7.52, 112.72),
    'TNT': (-6.59, 106.77),  'TRD': (-8.21, 115.52), 'TRT': (-5.64, 105.76),
    'YOG': (-7.79, 110.37),
}

STATIONS = list(STATION_COORDS.keys())


def _haversine(lat1, lon1, lat2, lon2):
    """Distance in km between two lat/lon points."""
    R = 6371.0
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


def _distance_weight(km: float, sigma: float = 300.0) -> float:
    """Gaussian distance weight. sigma=300km gives ~30% weight at 300km."""
    return float(np.exp(-0.5 * (km / sigma) ** 2))


class SpatialFuser:
    """Fuse station projections into global + per-station scores."""

    def __init__(self):
        # Precompute distance matrix
        self._stations = STATIONS
        n = len(self._stations)
        self._dist_km = np.zeros((n, n))
        self._weights = np.zeros((n, n))
        for i, s1 in enumerate(self._stations):
            lat1, lon1 = STATION_COORDS[s1]
            for j, s2 in enumerate(self._stations):
                lat2, lon2 = STATION_COORDS[s2]
                d = _haversine(lat1, lon1, lat2, lon2)
                self._dist_km[i, j] = d
                self._weights[i, j] = _distance_weight(d)

    def fuse(self, projections: Dict[str, np.ndarray]) -> Dict:
        """
        Args:
            projections: {station: (128,) float64} — latest projection per station.

        Returns:
            {
                'fused_embedding': (128,) mean embedding of available stations,
                'n_stations': int,
                'stations_used': list[str],
                'mean_inter_distance': float — avg km between active stations,
                'cluster_radius': float — max km among active stations,
                'per_station': {station: {}}
            }
        """
        active = [s for s in projections if s in STATION_COORDS]
        if not active:
            return {
                'fused_embedding': np.zeros(128),
                'n_stations': 0,
                'stations_used': [],
                'mean_inter_distance': 0.0,
                'cluster_radius': 0.0,
                'per_station': {},
            }

        # Simple mean fusion
        embs = np.stack([projections[s] for s in active])
        fused = np.mean(embs, axis=0)

        # Inter-station distances among active
        indices = [STATIONS.index(s) for s in active]
        if len(active) > 1:
            dists = []
            for ii in range(len(active)):
                for jj in range(ii + 1, len(active)):
                    dists.append(self._dist_km[indices[ii], indices[jj]])
            mean_dist = float(np.mean(dists))
            max_dist = float(np.max(dists))
        else:
            mean_dist = 0.0
            max_dist = 0.0

        per_station = {}
        for s in active:
            idx = STATIONS.index(s)
            # Distance-weighted influence from other stations
            other_weights = []
            for other in active:
                if other == s:
                    continue
                oidx = STATIONS.index(other)
                other_weights.append(self._weights[idx, oidx])
            influence = float(np.mean(other_weights)) if other_weights else 0.0
            per_station[s] = {
                'embedding': projections[s].tolist(),
                'influence_score': round(influence, 4),
            }

        return {
            'fused_embedding': fused,
            'n_stations': len(active),
            'stations_used': active,
            'mean_inter_distance': round(mean_dist, 1),
            'cluster_radius': round(max_dist, 1),
            'per_station': per_station,
        }
