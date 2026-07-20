#!/usr/bin/env python3
"""
predict_cli.py — JSON-based LAWS V9.5 inference CLI.
Called by collector/laws_predictor.py via subprocess.

Usage:
    python predict_cli.py --station ALR --h5-date 20260720 --h5-dir /opt/pimes/2026/scalogram
    echo '{"station":"ALR","x_img":[...],"x_cosmic":[...]}' | python predict_cli.py --stdin
"""
import argparse, json, sys, time, os
from pathlib import Path

LAWS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(LAWS_DIR))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--station', type=str, default=None)
    parser.add_argument('--h5-date', type=str, default=None, help='Date YYYYMMDD')
    parser.add_argument('--h5-dir', type=str, default=None)
    parser.add_argument('--device', type=str, default='cpu')
    parser.add_argument('--stdin', action='store_true', help='Read JSON from stdin')
    args = parser.parse_args()

    result = run_inference(args)
    print(json.dumps(result))

def run_inference(args):
    t0 = time.time()
    try:
        # Determine device
        device = args.device or os.environ.get('LAWS_DEVICE', 'cpu')

        # Import LAWS modules
        from app.config import CHECKPOINTS_DIR, PRIORS_DIR, H5_DIR, STATIONS, STATION_TO_ID, V95_CHECKPOINT
        from app.models.v95_model import V95PimesInference
        from app.utils.prior_loader import load_all_priors, get_prior_for_station

        import torch

        if args.stdin:
            # Direct tensor input via stdin
            data = json.load(sys.stdin)
            station = data.get('station', 'UNK')
            x_img = torch.tensor(data['x_img'], dtype=torch.float32)
            x_cosmic = torch.tensor(data['x_cosmic'], dtype=torch.float32)
            prior_vec = torch.tensor(data.get('prior_vec', [[0.0]*360]), dtype=torch.float32)
            stn_id = torch.tensor([STATION_TO_ID.get(station, 22)], dtype=torch.long)
        elif args.station and args.h5_date:
            # Load from HDF5
            from app.utils.hdf5_loader import build_h5_index, load_per_station_tensors, validate_tensor

            h5_dir = Path(args.h5_dir) if args.h5_dir else H5_DIR
            h5_index = build_h5_index(h5_dir)
            if args.h5_date not in h5_index:
                return {"error": f"No HDF5 data for {args.h5_date}", "latency_ms": 0}

            per_station = load_per_station_tensors(args.h5_date, h5_index)
            station = args.station
            if station not in per_station:
                return {"error": f"Station {station} not in data", "latency_ms": 0}
            x_img, x_cosmic = per_station[station]
            validate_tensor(x_img, f'{args.h5_date}/{station}')

            all_priors = load_all_priors(PRIORS_DIR, device)
            stn_id, prior_vec = get_prior_for_station(station, all_priors)
            stn_id = torch.tensor([stn_id], dtype=torch.long)
            prior_vec = prior_vec.unsqueeze(0)
        else:
            return {"error": "Provide --station/--h5-date or --stdin", "latency_ms": 0}

        # Load model
        v95 = V95PimesInference(V95_CHECKPOINT, device)

        # Run inference
        result = v95.predict(x_img, x_cosmic, stn_id, prior_vec)

        return {
            "station": station if args.station else data.get('station', 'UNK'),
            "detection_prob": result['detection_prob'],
            "detection_class": result['detection_class'],
            "azimuth_deg": result['azimuth_deg'],
            "gate_value": result['gate_value'],
            "device": device,
            "model_version": "v9.5-champion",
            "latency_ms": round((time.time() - t0) * 1000, 1),
        }
    except Exception as e:
        return {"error": str(e)[:500], "latency_ms": round((time.time() - t0) * 1000, 1)}

if __name__ == '__main__':
    main()
