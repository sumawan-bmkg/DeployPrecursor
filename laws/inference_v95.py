#!/usr/bin/env python3
"""
inference_v95.py — Standalone V9.5 PIMES inference runner (CLI).

For testing the V9.5 gatekeeper model directly without the FastAPI server.
Can run on aggregated or single-station data.

Usage:
    python inference_v95.py --date 20260101
    python inference_v95.py --date 20260101 --station ALR
    python inference_v95.py --date 20260101 --raw-tensors '{"x_img":...}'
    python inference_v95.py --list-dates
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import torch

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.config import (
    BASE_DIR, CHECKPOINTS_DIR, PRIORS_DIR, H5_DIR,
    V95_CHECKPOINT, V8_CHECKPOINT,
    DEVICE, STATIONS, STATION_TO_ID,
)
from app.utils.hdf5_loader import build_h5_index, load_multi_station, load_per_station_tensors, validate_tensor
from app.utils.prior_loader import load_all_priors, get_prior_for_station
from app.utils.kp_dst_gate import storm_gate_decision, StormGateConfig
from app.models.v95_model import V95PimesInference
from app.models.v8_model import V8SupConInference

logging.basicConfig(
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO,
)
logger = logging.getLogger('inference_v95')


def run_station_inference(v95: V95PimesInference, all_priors, station_code: str,
                           x_img, x_cosmic):
    """Run V9.5 inference for a specific station."""
    stn_id, prior_vec = get_prior_for_station(station_code, all_priors)
    station_id_t = torch.tensor([stn_id], dtype=torch.long)
    prior_vec_t = prior_vec.unsqueeze(0)

    result = v95.predict(x_img, x_cosmic, station_id_t, prior_vec_t)
    return result


def run_v8_magnitude(v8: V8SupConInference, x_img, x_cosmic):
    """Run V8 magnitude estimation."""
    return v8.predict(x_img, x_cosmic)


def list_dates(h5_dir: Path):
    """List available dates in HDF5 directory."""
    index = build_h5_index(h5_dir)
    if not index:
        logger.warning('No HDF5 files found in %s', h5_dir)
        return

    print(f'\n{"Date":<12} {"Stations":<8} {"Files"}')
    print('-' * 40)
    for date in sorted(index.keys()):
        entries = index[date]
        print(f'{date:<12} {len(entries):<8} {", ".join(s for s, _ in entries)}')


def main():
    parser = argparse.ArgumentParser(
        description='V9.5 PIMES Standalone Inference Runner',
    )
    parser.add_argument('--date', type=str, help='Date YYYYMMDD')
    parser.add_argument('--station', type=str, default=None,
                        help='Station code (default: aggregate all)')
    parser.add_argument('--h5-dir', type=Path, default=H5_DIR,
                        help=f'HDF5 directory (default: {H5_DIR})')
    parser.add_argument('--device', type=str, default=DEVICE,
                        help=f'Device (default: {DEVICE})')
    parser.add_argument('--list-dates', action='store_true',
                        help='List available HDF5 dates and exit')
    parser.add_argument('--per-station', action='store_true',
                        help='Run per-station instead of aggregated')
    parser.add_argument('--v8-only', action='store_true',
                        help='Run V8 magnitude only (no V9.5 gate)')
    args = parser.parse_args()

    if args.list_dates:
        list_dates(args.h5_dir)
        return

    if not args.date:
        parser.print_help()
        print('\nError: --date required unless --list-dates')
        sys.exit(1)

    device = args.device
    logger.info('═' * 60)
    logger.info('V9.5 PIMES Standalone Inference')
    logger.info(f'Date:    {args.date}')
    logger.info(f'Device:  {device}')
    logger.info(f'H5 dir:  {args.h5_dir}')
    if args.station:
        logger.info(f'Station: {args.station}')
    else:
        logger.info('Mode:    aggregate all stations')
    logger.info('═' * 60)

    # ── Load priors ──
    logger.info('[1/4] Loading priors...')
    all_priors = load_all_priors(PRIORS_DIR, device)

    # ── Build HDF5 index ──
    logger.info('[2/4] Building HDF5 index...')
    h5_index = build_h5_index(args.h5_dir)
    if args.date not in h5_index:
        logger.error('No data for date %s', args.date)
        sys.exit(1)
    logger.info('Found %d stations for %s', len(h5_index[args.date]), args.date)

    # ── Load V9.5 model (unless V8 only) ──
    v95_model = None
    if not args.v8_only:
        logger.info('[3/4] Loading V9.5 model...')
        v95_model = V95PimesInference(V95_CHECKPOINT, device)

    # ── Load V8 model ──
    logger.info('[4/4] Loading V8 model...')
    v8_model = V8SupConInference(V8_CHECKPOINT, device)

    # ── Run inference ──
    logger.info('─' * 50)
    logger.info('Running inference...')
    t_start = time.time()

    if args.per_station:
        # Per-station inference
        per_station = load_per_station_tensors(args.date, h5_index)
        logger.info('Loaded %d stations', len(per_station))

        for stn_code in sorted(per_station.keys()):
            x_img, x_cosmic = per_station[stn_code]
            try:
                validate_tensor(x_img, f'{args.date}/{stn_code}')
            except ValueError as e:
                logger.warning('%s — skip', e)
                continue

            print(f'\n─ Station: {stn_code} ─────────────────────')
            print(f'  Tensor shape: {x_img.shape}')
            print(f'  Kp={float(x_cosmic[0,0].item())*9:.1f}  Dst={50.0*__import__("math").atanh(max(-0.999,min(0.999,float(x_cosmic[0,1].item())))):.0f}')

            # Storm gate
            kp_norm = float(x_cosmic[0, 0].item())
            dst_norm = float(x_cosmic[0, 1].item())
            gate = storm_gate_decision(kp_norm, dst_norm)
            print(f'  Storm gate: {"STORM" if gate["storm_mode"] else "clear"} ({gate["reason"]})')

            # V9.5
            if v95_model:
                v95_res = run_station_inference(
                    v95_model, all_priors, stn_code, x_img, x_cosmic
                )
                print(f'  V9.5 detection:  P={v95_res["detection_prob"]:.3f} class={v95_res["detection_class"]}')
                print(f'  V9.5 azimuth:    {v95_res["azimuth_deg"]:.1f}°')
                print(f'  V9.5 gate:       {v95_res["gate_value"]:.4f}')

            # V8
            v8_res = run_v8_magnitude(v8_model, x_img, x_cosmic)
            print(f'  V8 magnitude:    M{v8_res["magnitude"]:.2f}')
            print(f'  V8 detection:    P={v8_res["detection_prob"]:.3f}')
            print(f'  V8 bins:         {[f"{p:.3f}" for p in v8_res["magnitude_bin_probs"]]}')

    else:
        # Aggregated inference
        x_img, x_cosmic, meta = load_multi_station(args.date, h5_index)
        try:
            validate_tensor(x_img, args.date)
        except ValueError as e:
            logger.error('Validation failed: %s', e)
            sys.exit(1)

        logger.info('Aggregated %d stations → %s', meta['n_stations'], list(x_img.shape))
        print(f'\n  Stations: {meta["stations_used"]}')
        print(f'  Kp={meta["kp_raw"]:.1f}  Dst={meta["dst_raw"]:.0f}')

        # Storm gate
        gate = storm_gate_decision(meta['kp_norm'], meta['dst_norm'], meta.get('kp_raw'), meta.get('dst_raw'))
        print(f'  Storm gate: {"STORM" if gate["storm_mode"] else "clear"} ({gate["reason"]})')

        # V9.5
        if v95_model:
            stn_code = meta['stations_used'][0] if meta['stations_used'] else 'UNK'
            v95_res = run_station_inference(
                v95_model, all_priors, stn_code, x_img, x_cosmic
            )
            print(f'\n  ── V9.5 PIMES ──')
            print(f'  Detection:      P={v95_res["detection_prob"]:.4f} class={v95_res["detection_class"]}')
            print(f'  Azimuth:        {v95_res["azimuth_deg"]:.1f}°')
            print(f'  Gate value:     {v95_res["gate_value"]:.4f}')

        # V8
        v8_res = run_v8_magnitude(v8_model, x_img, x_cosmic)
        print(f'\n  ── V8 SupCon ──')
        print(f'  Magnitude:      M{v8_res["magnitude"]:.2f}')
        print(f'  Detection:      P={v8_res["detection_prob"]:.4f} class={v8_res["detection_class"]}')
        print(f'  Magnitude bins: {[f"{p:.3f}" for p in v8_res["magnitude_bin_probs"]]}')
        print(f'  Azimuth sin/cos:{v8_res["azimuth_sin"]:.4f}/{v8_res["azimuth_cos"]:.4f}')
        print(f'  Reg score:      {v8_res["reg_score"]:.4f}')

    elapsed = time.time() - t_start
    print(f'\n{"─" * 50}')
    print(f'Inference completed in {elapsed:.2f}s')
    print(f'{"═" * 50}')


if __name__ == '__main__':
    main()
