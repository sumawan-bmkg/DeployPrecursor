#!/usr/bin/env python3
"""
inference.py — ScalogramV3 V8 Production Inference
Gunakan script ini untuk menjalankan prediksi pada data baru.

Usage:
    python inference.py --h5_path path/to/data.h5 --split val
    python inference.py --tensor_npy path/to/tensor.npy --kp 2.5 --dst -10
"""

import torch
import numpy as np
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'models'))
from V3_Model_v8 import (
    MultiTaskScalogramV3_v8,
    azimuth_from_sincos,
    find_optimal_threshold_f2,
    dynamic_threshold_from_negatives,
)

ROOT_CKPT = Path(__file__).parent.parent / 'checkpoints'
DEFAULT_CKPT = ROOT_CKPT / 'v3_v8_conv_fpr_best_weights.pth'


def load_model(ckpt_path=DEFAULT_CKPT, device='cpu'):
    model = MultiTaskScalogramV3_v8(pretrained=False).to(device)
    state = torch.load(ckpt_path, map_location=device)
    if isinstance(state, dict) and 'model_state_dict' in state:
        state = state['model_state_dict']
    model.load_state_dict(state, strict=False)
    model.eval()
    print(f"[OK] Model loaded: {Path(ckpt_path).name}")
    return model


def predict_batch(model, tensors: np.ndarray, cosmic: np.ndarray,
                  threshold: float = 0.30, device: str = 'cpu',
                  batch_size: int = 8):
    """
    Jalankan prediksi pada batch data.

    Args:
        tensors: (N, 3, 128, 1440) float32
        cosmic:  (N, 2) float32 [Kp_raw, Dst_raw]
        threshold: detection threshold (default 0.30)

    Returns:
        dict dengan keys: probs, alerts, azimuths, magnitudes
    """
    all_probs, all_azm, all_mag = [], [], []

    with torch.no_grad():
        for i in range(0, len(tensors), batch_size):
            x = torch.from_numpy(tensors[i:i+batch_size]).float().to(device)
            c = torch.from_numpy(cosmic[i:i+batch_size]).float().to(device)

            det, mag, azm, _, _, _ = model(x, c)

            probs = torch.softmax(det, dim=1)[:, 1].cpu().numpy()
            azm_deg = azimuth_from_sincos(azm).cpu().numpy()
            mag_bins = np.array([3.5, 4.5, 5.5, 6.5, 7.5])
            mag_pred = mag_bins[torch.argmax(mag, dim=1).cpu().numpy()]

            all_probs.append(probs)
            all_azm.append(azm_deg)
            all_mag.append(mag_pred)

    probs = np.concatenate(all_probs)
    azimuths = np.concatenate(all_azm)
    magnitudes = np.concatenate(all_mag)
    alerts = probs >= threshold

    return {
        'probs':      probs,
        'alerts':     alerts,
        'azimuths':   azimuths,
        'magnitudes': magnitudes,
        'threshold':  threshold,
        'n_alerts':   int(alerts.sum()),
        'n_total':    len(probs),
    }


def predict_from_h5(h5_path: str, split: str = 'val',
                    ckpt_path=DEFAULT_CKPT, device: str = 'cpu',
                    max_samples: int = 200):
    """Predict dari HDF5 file."""
    import h5py

    model = load_model(ckpt_path, device)

    with h5py.File(h5_path, 'r') as f:
        grp = f[split]
        n = min(grp['tensors'].shape[0], max_samples)
        tensors = np.array(grp['tensors'][:n], dtype=np.float32)
        cosmic  = np.array(grp['cosmic_features'][:n], dtype=np.float32)
        labels  = np.array(grp['label_event'][:n], dtype=np.int32) \
                  if 'label_event' in grp else None

    print(f"[OK] Loaded {n} samples from {split}")

    results = predict_batch(model, tensors, cosmic, device=device)

    if labels is not None:
        # Compute optimal threshold from data
        probs_t  = torch.from_numpy(results['probs'])
        labels_t = torch.from_numpy(labels)
        opt_th = find_optimal_threshold_f2(probs_t, labels_t)
        results['optimal_threshold'] = opt_th

        # Metrics
        preds = results['probs'] >= opt_th
        tp = ((preds == 1) & (labels == 1)).sum()
        fp = ((preds == 1) & (labels == 0)).sum()
        tn = ((preds == 0) & (labels == 0)).sum()
        fn = ((preds == 0) & (labels == 1)).sum()

        prec = tp / (tp + fp + 1e-8)
        rec  = tp / (tp + fn + 1e-8)
        fpr  = fp / (fp + tn + 1e-8)
        f2   = 5 * prec * rec / (4 * prec + rec + 1e-8)

        results['metrics'] = {
            'precision': float(prec), 'recall': float(rec),
            'fpr': float(fpr), 'f2': float(f2),
            'tp': int(tp), 'fp': int(fp),
            'tn': int(tn), 'fn': int(fn),
        }

        print(f"\nMetrics (th={opt_th:.3f}):")
        print(f"  Precision: {prec:.3f}  Recall: {rec:.3f}")
        print(f"  FPR: {fpr:.4f}  F2: {f2:.3f}")
        print(f"  TP={tp} FP={fp} TN={tn} FN={fn}")

    return results


def predict_single(tensor: np.ndarray, kp: float, dst: float,
                   ckpt_path=DEFAULT_CKPT, device: str = 'cpu',
                   threshold: float = 0.30):
    """Predict satu sampel."""
    model = load_model(ckpt_path, device)

    if tensor.ndim == 3:
        tensor = tensor[np.newaxis]  # add batch dim

    cosmic = np.array([[kp, dst]], dtype=np.float32)
    results = predict_batch(model, tensor, cosmic, threshold, device)

    print(f"\nPrediction:")
    print(f"  Detection probability: {results['probs'][0]:.4f}")
    print(f"  Alert (th={threshold}): {'YES ⚠️' if results['alerts'][0] else 'NO ✅'}")
    print(f"  Predicted azimuth: {results['azimuths'][0]:.1f}°")
    print(f"  Predicted magnitude bin: M{results['magnitudes'][0]:.1f}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ScalogramV3 V8 Inference")
    parser.add_argument('--h5_path',    type=str, default=None)
    parser.add_argument('--split',      type=str, default='val')
    parser.add_argument('--tensor_npy', type=str, default=None)
    parser.add_argument('--kp',         type=float, default=2.0)
    parser.add_argument('--dst',        type=float, default=-10.0)
    parser.add_argument('--threshold',  type=float, default=0.30)
    parser.add_argument('--ckpt',       type=str,
                        default=str(DEFAULT_CKPT))
    parser.add_argument('--device',     type=str, default='cpu')
    parser.add_argument('--max_samples', type=int, default=200)
    args = parser.parse_args()

    if args.h5_path:
        results = predict_from_h5(
            args.h5_path, args.split, args.ckpt,
            args.device, args.max_samples)
        print(f"\nAlerts: {results['n_alerts']}/{results['n_total']}")

    elif args.tensor_npy:
        tensor = np.load(args.tensor_npy).astype(np.float32)
        results = predict_single(tensor, args.kp, args.dst,
                                  args.ckpt, args.device, args.threshold)
    else:
        print("Provide --h5_path or --tensor_npy")
        print("Example: python inference.py --h5_path ../scalogram_v8_true_negatives.h5")
