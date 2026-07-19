#!/usr/bin/env python3
"""
prior_loader.py — Load station-specific azimuth priors for V9.5 inference.
"""
from pathlib import Path
from typing import Dict, Optional

import torch


# Canonical station ordering — matches BayesianAzimuthHeadV95(num_stations=23).
# Index 22 reserved for unknown/padding.
STATION_ORDER: list[str] = [
    'ALR', 'AMB', 'CLP', 'GTO', 'KPY', 'LPS', 'LUT', 'LWA', 'LWK',
    'MLB', 'PLU', 'ROT', 'SBG', 'SCN', 'SKB', 'SMI', 'SRG', 'SRO',
    'TNT', 'TRD', 'TRT', 'YOG', 'UNK',
]

STATION_TO_ID: Dict[str, int] = {s: i for i, s in enumerate(STATION_ORDER)}

DEFAULT_PRIORS_DIR = Path(__file__).resolve().parents[2] / 'priors'


def load_all_priors(
    priors_dir: Path = DEFAULT_PRIORS_DIR,
    device: str = 'cpu',
) -> torch.Tensor:
    """
    Load all station priors into a single (N_stations, 360) tensor.
    Missing stations get a uniform prior.
    """
    n_bins = 360
    priors = torch.ones(len(STATION_ORDER), n_bins, device=device) / n_bins

    for station_code, idx in STATION_TO_ID.items():
        if station_code == 'UNK':
            continue
        prior_path = priors_dir / f'prior_{station_code}.pt'
        if prior_path.exists():
            tensor = torch.load(str(prior_path), map_location=device)
            if tensor.shape == (n_bins,):
                priors[idx] = tensor.to(device)
            else:
                raise ValueError(
                    f'Prior shape mismatch for {station_code}: '
                    f'expected ({n_bins},), got {tensor.shape}'
                )

    return priors


def get_prior_for_station(
    station_code: str,
    all_priors: Optional[torch.Tensor] = None,
    priors_dir: Path = DEFAULT_PRIORS_DIR,
    device: str = 'cpu',
) -> tuple[int, torch.Tensor]:
    """
    Returns (station_id, prior_vector) for a given station code.
    If station not in known list, returns UNK index with uniform prior.
    """
    if station_code not in STATION_TO_ID:
        station_code = 'UNK'

    station_id = STATION_TO_ID[station_code]

    if all_priors is not None:
        return station_id, all_priors[station_id].clone()

    n_bins = 360
    prior_path = priors_dir / f'prior_{station_code}.pt'
    if prior_path.exists():
        prior = torch.load(str(prior_path), map_location=device)
    else:
        prior = torch.ones(n_bins, device=device) / n_bins

    return station_id, prior


def load_prior_metadata(priors_dir: Path = DEFAULT_PRIORS_DIR) -> Dict[str, dict]:
    """Load metadata text files for each station."""
    metadata = {}
    for station_code in STATION_ORDER:
        if station_code == 'UNK':
            continue
        meta_path = priors_dir / f'prior_{station_code}_metadata.txt'
        if meta_path.exists():
            lines = meta_path.read_text().strip().splitlines()
            meta = {}
            for line in lines:
                if ':' in line:
                    key, val = line.split(':', 1)
                    meta[key.strip()] = val.strip()
            metadata[station_code] = meta
    return metadata
