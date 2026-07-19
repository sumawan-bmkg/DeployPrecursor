#!/usr/bin/env python3
"""
hdf5_loader.py — Per-station HDF5 scalogram loader for LAWS operational deployment.

HDF5 structure (confirmed):
    daily/{STATION}/tensors        shape=(1,3,128,1440) dtype=float16
    daily/{STATION}/cosmic_features shape=(1,2)         dtype=float32

Two modes:
    1. load_station_scalogram()  — single station
    2. load_multi_station()      — aggregate N stations for a date
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch

logger = logging.getLogger(__name__)

H5_PATTERN = re.compile(r'scalogram_([A-Z]+)_(\d{8})\.h5$')

# Default H5 directory — adjust for production
DEFAULT_H5_DIR = Path(__file__).resolve().parents[2] / '..' / '2026' / 'scalogram'


def build_h5_index(h5_dir: Path) -> Dict[str, List[Tuple[str, Path]]]:
    """
    Build date → [(station, path)] index from HDF5 filenames.
    Filename format: scalogram_{STATION}_{YYYYMMDD}.h5
    """
    idx: Dict[str, List[Tuple[str, Path]]] = {}
    h5_files = list(h5_dir.glob('*.h5'))
    if not h5_files:
        logger.warning('No .h5 files found in %s', h5_dir)

    for f in sorted(h5_files):
        m = H5_PATTERN.match(f.name)
        if m:
            stn, date = m.group(1), m.group(2)
            idx.setdefault(date, []).append((stn, f))

    logger.info(
        'HDF5 index built: %d files across %d dates',
        sum(len(v) for v in idx.values()),
        len(idx),
    )
    return idx


def load_station_scalogram(
    h5_path: Path,
    station_code: str,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load a single station's scalogram from HDF5.

    Returns:
        tensor   : (3, 128, 1440) float32
        cosmic   : (2,) float32  — [Kp_raw, Dst_raw]
    """
    import h5py

    with h5py.File(str(h5_path), 'r') as hf:
        tensor = np.array(
            hf['daily'][station_code]['tensors'][0],
            dtype=np.float32,
        )  # (3,128,1440)
        cosmic = np.array(
            hf['daily'][station_code]['cosmic_features'][0],
            dtype=np.float32,
        )  # (2,)

    return tensor, cosmic


def load_multi_station(
    date_str: str,
    h5_index: Dict[str, List[Tuple[str, Path]]],
    target_stations: Optional[List[str]] = None,
) -> Tuple[torch.Tensor, torch.Tensor, dict]:
    """
    Load and aggregate all stations for a given date.

    If target_stations provided, only load those. Otherwise load all.

    Aggregation: channel-wise mean across stations.
    (Consistent with V8 GNN which repeats a single feature 8 times.)

    Returns:
        x_img    : (1, 3, 128, 1440) float32
        x_cosmic : (1, 2) float32  — [Kp_norm, Dst_norm]
        meta     : dict with audit info
    """
    if date_str not in h5_index:
        raise ValueError(f'No HDF5 files for date {date_str}')

    station_entries = h5_index[date_str]
    tensors_loaded: List[np.ndarray] = []
    cosmic_loaded: List[np.ndarray] = []
    stations_used: List[str] = []

    for stn, h5_path in station_entries:
        if target_stations and stn not in target_stations:
            continue
        try:
            tensor, cosmic = load_station_scalogram(h5_path, stn)
            tensors_loaded.append(tensor)
            cosmic_loaded.append(cosmic)
            stations_used.append(stn)
        except Exception as exc:
            logger.warning('Skip station %s: %s', stn, exc)
            continue

    if not tensors_loaded:
        raise ValueError(
            f'All HDF5 reads failed for date {date_str}'
        )

    # Aggregate: mean across stations → (3,128,1440)
    tensor_agg = np.mean(np.stack(tensors_loaded, axis=0), axis=0)
    cosmic_agg = np.mean(np.stack(cosmic_loaded, axis=0), axis=0)

    # Normalize cosmic features (same as training pipeline)
    kp_norm = float(cosmic_agg[0]) / 9.0
    dst_norm = float(np.tanh(cosmic_agg[1] / 50.0))

    x_img = torch.from_numpy(tensor_agg).float().unsqueeze(0)   # (1,3,128,1440)
    x_cosmic = torch.tensor(
        [[kp_norm, dst_norm]], dtype=torch.float32
    )  # (1,2)

    meta = {
        'date_str': date_str,
        'stations_used': stations_used,
        'n_stations': len(stations_used),
        'tensor_mean': float(tensor_agg.mean()),
        'tensor_std': float(tensor_agg.std()),
        'kp_raw': float(cosmic_agg[0]),
        'dst_raw': float(cosmic_agg[1]),
        'kp_norm': kp_norm,
        'dst_norm': dst_norm,
    }
    return x_img, x_cosmic, meta


def load_per_station_tensors(
    date_str: str,
    h5_index: Dict[str, List[Tuple[str, Path]]],
) -> Dict[str, Tuple[torch.Tensor, torch.Tensor]]:
    """
    Load individual station tensors WITHOUT aggregation.
    Useful for per-station inference and GNN input.

    Returns:
        dict[station_code] = (x_img, x_cosmic)  each (1,3,128,1440) and (1,2)
    """
    if date_str not in h5_index:
        raise ValueError(f'No HDF5 files for date {date_str}')

    result: Dict[str, Tuple[torch.Tensor, torch.Tensor]] = {}
    for stn, h5_path in h5_index[date_str]:
        try:
            tensor, cosmic = load_station_scalogram(h5_path, stn)
            kp_norm = float(cosmic[0]) / 9.0
            dst_norm = float(np.tanh(cosmic[1] / 50.0))

            x_img = torch.from_numpy(tensor).float().unsqueeze(0)
            x_cosmic = torch.tensor(
                [[kp_norm, dst_norm]], dtype=torch.float32
            )
            result[stn] = (x_img, x_cosmic)
        except Exception as exc:
            logger.warning('Skip station %s: %s', stn, exc)
            continue

    return result


def validate_tensor(x_img: torch.Tensor, event_id: str = '') -> None:
    """
    Mandatory validation — no fallback to zero tensor.
    Raises ValueError on failure.
    """
    std_val = float(x_img.std().item())
    abs_sum = float(x_img.abs().sum().item())

    if std_val <= 0:
        raise ValueError(
            f'INPUT_VALIDATION_FAIL: std={std_val:.6f} for {event_id}'
        )
    if abs_sum <= 0:
        raise ValueError(
            f'INPUT_VALIDATION_FAIL: abs_sum={abs_sum:.2f} for {event_id}'
        )
