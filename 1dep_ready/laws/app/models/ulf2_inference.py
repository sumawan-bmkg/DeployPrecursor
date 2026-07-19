#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ulf2_inference.py — Real-time ULF2 feature extraction wrapper for API.

Extracts 53 physics-based features from raw magnetometer data (H, D, Z)
in batch mode across multiple stations.

Feature families (53 total):
  1. Energy (12)       — H/D/Z rms, energy, power, dominant freq
  2. Spectral (8)      — Pc band ratios, centroid, edge, flatness
  3. Entropy (6)       — spectral + dynamical (sample, permutation)
  4. Burst (5)         — envelope peak statistics
  5. Polarization (6)  — H/D cross-spectrum, ellipticity, planarity
  6. Consensus (8)     — cross-station RMS agreement (requires ≥2 stations)
  7. Coherence (8)     — pairwise correlation, PLV, growth rates

NOTE: D component (horizontal East/declination) is REQUIRED for polarization.
      If only H and Z available, polarization features will be degraded.
"""

import time
import warnings
from typing import Dict, Tuple, List, Optional

import numpy as np
from scipy import signal as sp_signal

warnings.filterwarnings('ignore')

# Import core extraction functions from root-level extractor
# (Assumes ulf2_feature_extractor.py is in parent directory)
import sys
from pathlib import Path
PARENT = Path(__file__).resolve().parents[3]  # Go up to scalogramv3/
sys.path.insert(0, str(PARENT))

from ulf2_feature_extractor import (
    extract_single_window,
    compute_cross_station_features,
    FEATURE_NAMES,
)

# Verify feature count
assert len(FEATURE_NAMES) == 53, f"Expected 53 features, got {len(FEATURE_NAMES)}"


# ══════════════════════════════════════════════════════════════════
# PREPROCESSING HELPERS
# ══════════════════════════════════════════════════════════════════

def detrend_signal(x: np.ndarray, method: str = 'linear') -> np.ndarray:
    """
    Detrend time series to remove linear drift or DC offset.
    
    Args:
        x: Raw time series (1D array)
        method: 'linear' (remove linear trend) or 'constant' (remove mean)
    
    Returns:
        Detrended signal (same shape as input)
    """
    if len(x) < 10:
        return x
    return sp_signal.detrend(x, type=method)


def validate_signal(x: np.ndarray, component: str, station: str) -> None:
    """
    Check for common signal quality issues.
    
    Raises ValueError if signal is invalid.
    """
    if len(x) < 100:
        raise ValueError(f"Signal too short: {station}/{component} has {len(x)} samples (min 100)")
    
    if np.all(np.isnan(x)):
        raise ValueError(f"All NaN: {station}/{component}")
    
    if np.std(x[~np.isnan(x)]) < 1e-12:
        warnings.warn(f"Flat signal: {station}/{component} (std < 1e-12)")


# ══════════════════════════════════════════════════════════════════
# BATCH EXTRACTION API
# ══════════════════════════════════════════════════════════════════

def extract_features_realtime_batch(
    raw_signals: Dict[str, Tuple[np.ndarray, np.ndarray, np.ndarray]],
    validate: bool = True
) -> np.ndarray:
    """
    Extract 53 ULF2 features from raw magnetometer data (batch mode).
    
    Args:
        raw_signals: Dict mapping station_id → (raw_h, raw_d, raw_z)
                     Each component is a 1D numpy array (typically 1440-3600 samples).
        validate: If True, check signal quality before extraction.
    
    Returns:
        feature_matrix: np.ndarray of shape (N_stations, 53)
                        Rows correspond to sorted(raw_signals.keys())
                        Columns follow FEATURE_NAMES ordering.
    
    Raises:
        ValueError: If signal validation fails or batch is empty.
    
    Example:
        >>> raw_signals = {
        ...     'ALR': (np.random.randn(1440), np.random.randn(1440), np.random.randn(1440)),
        ...     'PLU': (np.random.randn(1440), np.random.randn(1440), np.random.randn(1440)),
        ... }
        >>> features = extract_features_realtime_batch(raw_signals)
        >>> features.shape
        (2, 53)
    """
    if not raw_signals:
        raise ValueError("Empty batch: raw_signals dict is empty")
    
    stations = sorted(raw_signals.keys())
    n_stations = len(stations)
    
    # ── Phase 1: Station-level features (37 per station) ──
    station_features = np.zeros((n_stations, 37), dtype=np.float64)
    station_data_detrended = {}  # For cross-station phase
    station_rms_map = {}
    
    for i, station in enumerate(stations):
        raw_h, raw_d, raw_z = raw_signals[station]
        
        # Validate
        if validate:
            validate_signal(raw_h, 'H', station)
            validate_signal(raw_d, 'D', station)
            validate_signal(raw_z, 'Z', station)
        
        # Detrend (optimized with mean subtraction)
        h_det = raw_h - np.mean(raw_h)
        d_det = raw_d - np.mean(raw_d)
        z_det = raw_z - np.mean(raw_z)
        
        # Extract station-level features (37 dims)
        station_features[i] = extract_single_window(h_det, d_det, z_det)
        
        # Store for cross-station computation
        station_data_detrended[station] = (h_det, d_det, z_det)
        station_rms_map[station] = float(station_features[i, 0])  # H_rms is first feature
    
    # ── Phase 2: Cross-station features (16 per station) ──
    cross_features = np.zeros((n_stations, 16), dtype=np.float64)
    
    if n_stations >= 2:
        # Compute cross-station consensus & coherence
        cross_result = compute_cross_station_features(
            station_data_detrended,
            station_rms_map
        )
        
        if cross_result is not None:
            # Broadcast same cross-station features to all stations in batch
            for i in range(n_stations):
                cross_features[i] = cross_result
    else:
        # Single station: cross-station features default to 0
        # (This is acceptable as fallback, but not ideal for model)
        pass
    
    # ── Merge: 37 + 16 = 53 ──
    feature_matrix = np.hstack([station_features, cross_features])
    
    assert feature_matrix.shape == (n_stations, 53), \
        f"Feature matrix shape mismatch: {feature_matrix.shape} vs ({n_stations}, 53)"
    
    return feature_matrix


def extract_features_realtime_single(
    raw_h: np.ndarray,
    raw_d: np.ndarray,
    raw_z: np.ndarray,
    station_id: str = "UNK"
) -> np.ndarray:
    """
    Extract 53 features for a single station (convenience wrapper).
    
    Cross-station features (consensus + coherence) will be zero.
    
    Args:
        raw_h, raw_d, raw_z: Raw magnetometer components (1D arrays)
        station_id: Station identifier (for logging)
    
    Returns:
        features: np.ndarray of shape (53,)
    """
    batch = {station_id: (raw_h, raw_d, raw_z)}
    feature_matrix = extract_features_realtime_batch(batch, validate=True)
    return feature_matrix[0]


# ══════════════════════════════════════════════════════════════════
# FEATURE METADATA
# ══════════════════════════════════════════════════════════════════

def get_feature_names() -> List[str]:
    """Return ordered list of 53 feature names."""
    return FEATURE_NAMES.copy()


def get_feature_metadata() -> Dict:
    """
    Return feature metadata dict (families, counts, ordering).
    
    Matches output format of ulf2_feature_metadata.json.
    """
    family_map = {}
    for f in FEATURE_NAMES:
        if f.startswith(('H_', 'D_', 'Z_')) and 'total' not in f:
            family_map[f] = 'energy'
        elif f.startswith('sp_') and 'entropy' not in f:
            family_map[f] = 'spectral'
        elif 'entropy' in f or f.startswith('dyn_'):
            family_map[f] = 'entropy'
        elif f.startswith('burst_'):
            family_map[f] = 'burst'
        elif f.startswith('pol_'):
            family_map[f] = 'polarization'
        elif f.startswith('net_'):
            family_map[f] = 'consensus'
        elif f.startswith(('network_', 'pairwise_', 'station_', 'consensus_',
                           'spread_', 'phase_locking', 'mean_coherence')):
            family_map[f] = 'coherence'
        else:
            family_map[f] = 'unknown'
    
    families = {}
    for fam in set(family_map.values()):
        families[fam] = [f for f in FEATURE_NAMES if family_map[f] == fam]
    
    return {
        'n_features': 53,
        'feature_names': FEATURE_NAMES,
        'feature_families': family_map,
        'families': families,
        'feature_counts': {fam: len(feats) for fam, feats in families.items()},
    }


# ══════════════════════════════════════════════════════════════════
# TIMING UTILITIES (for profiling)
# ══════════════════════════════════════════════════════════════════

class ExtractionTimer:
    """Context manager for timing feature extraction."""
    
    def __init__(self):
        self.start_time = None
        self.elapsed_ms = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000
        return False
