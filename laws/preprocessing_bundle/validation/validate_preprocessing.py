#!/usr/bin/env python3
"""
validate_preprocessing.py

Tujuan:
  Memverifikasi bahwa pipeline preprocessing realtime menghasilkan tensor
  yang identik dengan tensor HDF5 training.

Pipeline (identik dengan training V9.5):
  1. read_mdata_file() — parser BMKG binary
  2. GeomagneticSignalProcessor.process_components() — PC3 filter + gap handling
  3. V2TensorGenerator.generate_tensor() — pooling + CWT
  4. compute_polarization() — opsional
  5. mad_norm() — opsional
  6. Load tensor HDF5 daily/<station>/tensors
  7. Bandingkan

Usage:
  python validate_preprocessing.py \\
      --raw /opt/pimes/data/raw/ALR/S260611.ALR \\
      --h5 /opt/pimes/laws/h5/scalogram_ALR_20260101.h5 \\
      --station ALR \\
      --plot
"""

import argparse
import os
import sys
import re
import logging
from pathlib import Path
from datetime import datetime

import numpy as np
from scipy.stats import pearsonr
from scipy.spatial.distance import cosine

logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# ── Path setup: add preprocessing_bundle to sys.path ──────────────────────
_THIS_DIR = Path(__file__).resolve().parent
_LAWS_DIR = _THIS_DIR.parent
_PB_DIR = _LAWS_DIR / 'preprocessing_bundle'
sys.path.insert(0, str(_LAWS_DIR))
sys.path.insert(0, str(_PB_DIR))
sys.path.insert(0, str(_PB_DIR / 'core'))
sys.path.insert(0, str(_PB_DIR / 'tensor_generation'))
sys.path.insert(0, str(_PB_DIR / 'data_fetching'))
sys.path.insert(0, str(_PB_DIR / 'data_loading'))
sys.path.insert(0, "/opt/pimes/scripts")

from core.signal_processing import GeomagneticSignalProcessor
from core.tensor_generator import V2TensorGenerator
from parse_mdata_audit import read_mdata_file

# ── read_mdata_file wrapper ──────────────────────────────────────────────
# ── HDF5 reference loader ────────────────────────────────────────────────
def load_reference_tensor(h5_path: str, station: str) -> np.ndarray:
    """
    Load tensor from HDF5 file.
    Structure: daily/{station}/tensors — shape (1, 3, 128, 1440) float16.
    Returns (3, 128, 1440) float64.
    """
    import h5py

    with h5py.File(h5_path, 'r') as hf:
        grp = hf['daily'][station]
        tensor = np.array(grp['tensors'][0], dtype=np.float64)

    if tensor.ndim == 4 and tensor.shape[0] == 1:
        tensor = tensor[0]  # (1,3,128,1440) → (3,128,1440)

    return tensor


# ── Metrics ───────────────────────────────────────────────────────────────
def compute_metrics(a: np.ndarray, b: np.ndarray) -> dict:
    """Compute pixel-level comparison metrics."""
    a_f = a.ravel()
    b_f = b.ravel()

    mae = float(np.mean(np.abs(a_f - b_f)))
    rmse = float(np.sqrt(np.mean((a_f - b_f) ** 2)))
    max_err = float(np.max(np.abs(a_f - b_f)))
    r, p = pearsonr(a_f, b_f)
    cos_sim = float(1.0 - cosine(a_f, b_f))

    return {
        'mae': mae,
        'rmse': rmse,
        'pearson': float(r),
        'pearson_p': float(p),
        'cosine_similarity': cos_sim,
        'max_abs_error': max_err,
    }


# ── Plotting ───────────────────────────────────────────────────────────────
def _ensure_plt():
    """Lazy-import matplotlib, set non-interactive backend."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    return plt


def plot_differences(t_new: np.ndarray, t_ref: np.ndarray, out_dir: str):
    """
    Generate per-channel difference maps and histogram.
    """
    plt = _ensure_plt()
    os.makedirs(out_dir, exist_ok=True)
    ch_names = ['H', 'D', 'Z']

    diff = t_new.astype(np.float64) - t_ref.astype(np.float64)

    for i, name in enumerate(ch_names):
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))

        vmax = max(abs(diff[i]).max(), 1e-10)
        im0 = axes[0].imshow(t_new[i], aspect='auto', cmap='RdBu_r',
                             vmin=-vmax, vmax=vmax)
        axes[0].set_title(f'{name} — Realtime')
        plt.colorbar(im0, ax=axes[0], shrink=0.8)

        im1 = axes[1].imshow(t_ref[i], aspect='auto', cmap='RdBu_r',
                             vmin=-vmax, vmax=vmax)
        axes[1].set_title(f'{name} — Reference')
        plt.colorbar(im1, ax=axes[1], shrink=0.8)

        im2 = axes[2].imshow(diff[i], aspect='auto', cmap='seismic',
                             vmin=-vmax, vmax=vmax)
        axes[2].set_title(f'{name} — Difference')
        plt.colorbar(im2, ax=axes[2], shrink=0.8)

        for ax in axes:
            ax.set_xlabel('Time step')
            ax.set_ylabel('Frequency bin')

        fig.tight_layout()
        out_path = os.path.join(out_dir, f'difference_{name}.png')
        fig.savefig(out_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"  [PLOT] Saved {out_path}")

    # Histogram of differences
    fig, ax = plt.subplots(figsize=(10, 6))
    for i, name in enumerate(ch_names):
        ax.hist(diff[i].ravel(), bins=200, alpha=0.5, label=f'{name}', density=True)
    ax.set_xlabel('Difference (new - ref)')
    ax.set_ylabel('Density')
    ax.set_title('Histogram of Tensor Differences')
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out_path = os.path.join(out_dir, 'difference_histogram.png')
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  [PLOT] Saved {out_path}")


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description='Validate realtime preprocessing pipeline against HDF5 reference',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--raw', type=str, required=True,
                        help='Path to raw BMKG binary file')
    parser.add_argument('--h5', type=str, required=True,
                        help='Path to reference HDF5 file')
    parser.add_argument('--station', type=str, required=True,
                        help='Station code (e.g., ALR)')
    parser.add_argument('--plot', action='store_true',
                        help='Generate difference plots in validation_output/')
    parser.add_argument('--mad', action='store_true',
                        help='Enable MAD normalization after polarization')
    args = parser.parse_args()

    BANNER = """\
========================================================
            PIPELINE VALIDATION
========================================================"""
    print(BANNER)

    # ── Step 1: Parse raw file ────────────────────────────────────────
    print("\n[1/6] Reading raw BMKG binary...")
    raw = read_mdata_file(args.raw)
    h_raw = raw['H']
    d_raw = raw['D']
    z_raw = raw['Z']
    print(f"      H: {len(h_raw)} samples, mean={np.nanmean(h_raw):.2f}")
    print(f"      D: {len(d_raw)} samples, mean={np.nanmean(d_raw):.2f}")
    print(f"      Z: {len(z_raw)} samples, mean={np.nanmean(z_raw):.2f}")

    # Pad to 86400 if shorter
    n_expected = 86400
    for arr_name, arr in [('H', h_raw), ('D', d_raw), ('Z', z_raw)]:
        if len(arr) < n_expected:
            logger.warning(f"{arr_name} length {len(arr)} < {n_expected}, padding with NaN")
            pad = np.full(n_expected - len(arr), np.nan)
            if arr_name == 'H':
                h_raw = np.concatenate([h_raw, pad])
            elif arr_name == 'D':
                d_raw = np.concatenate([d_raw, pad])
            else:
                z_raw = np.concatenate([z_raw, pad])

    # ── Step 2: PC3 filter ────────────────────────────────────────────
    print("\n[2/6] PC3 bandpass filter (0.022-0.1 Hz)...")
    processor = GeomagneticSignalProcessor(sampling_rate=1.0)
    processed = processor.process_components(h_raw, d_raw, z_raw, apply_pc3=True)
    h_pc3 = processed['h_pc3']
    d_pc3 = processed['d_pc3']
    z_pc3 = processed['z_pc3']
    print(f"      Filtered: H std={np.std(h_pc3):.4f}")

    # ── Step 3: Tensor generation ──────────────────────────────────────
    print("\n[3/6] Generating tensor (pooling + CWT + z-score)...")
    generator = V2TensorGenerator()
    tensor_raw, _ = generator.generate_tensor(h_pc3, d_pc3, z_pc3, apply_pooling=True)
    tensor_norm = generator.zscore_normalize(tensor_raw)
    print(f"      Tensor shape: {tensor_norm.shape}")
    print(f"      dtype: {tensor_norm.dtype}")

    # ── Step 4: Optional polarization ──────────────────────────────────
    import torch
    tensor_out = tensor_norm

    if args.mad:
        print("\n[4/6] Polarization + MAD normalization...")
        from core.polarization import compute_polarization, mad_norm

        t_torch = torch.from_numpy(tensor_norm).float()
        H_ch = t_torch[0]
        Z_ch = t_torch[2]

        # compute_polarization replaces channels [H, Z, log(ratio)] → shape (3, 128, 1440)
        tensor_pol = compute_polarization(H_ch, Z_ch, eps=1e-6, quantile=0.995)
        tensor_pol = mad_norm(tensor_pol)

        tensor_out = tensor_pol.numpy()
        print(f"      Polarization applied: shape={tensor_out.shape}")
    else:
        print("\n[4/6] Polarization: skipped (use --mad to enable)")

    # ── Step 5: Load reference ────────────────────────────────────────
    print(f"\n[5/6] Loading reference HDF5: {args.h5}")
    tensor_ref = load_reference_tensor(args.h5, args.station)
    print(f"      Reference shape: {tensor_ref.shape}")
    print(f"      Reference dtype: {tensor_ref.dtype}")

    # ── Step 6: Compare ───────────────────────────────────────────────
    print("\n[6/6] Comparing tensors...")

    # Shape validation
    if tensor_out.shape != tensor_ref.shape:
        raise ValueError(
            f"Shape mismatch! New: {tensor_out.shape} vs Ref: {tensor_ref.shape}. "
            "Cannot compare. Check pipeline parameters or --mad flag."
        )

    # Per-channel stats
    ch_names = ['H', 'D', 'Z']
    print(f"\n{'Channel':>8} {'Mean(new)':>12} {'Mean(ref)':>12} "
          f"{'Std(new)':>12} {'Std(ref)':>12} "
          f"{'Min(new)':>12} {'Min(ref)':>12} "
          f"{'Max(new)':>12} {'Max(ref)':>12}")
    print('-' * 100)
    for i, name in enumerate(ch_names):
        print(f"{name:>8} "
              f"{tensor_out[i].mean():>12.6f} {tensor_ref[i].mean():>12.6f} "
              f"{tensor_out[i].std():>12.6f} {tensor_ref[i].std():>12.6f} "
              f"{tensor_out[i].min():>12.6f} {tensor_ref[i].min():>12.6f} "
              f"{tensor_out[i].max():>12.6f} {tensor_ref[i].max():>12.6f}")

    # Global metrics
    metrics = compute_metrics(tensor_out, tensor_ref)

    print()
    print(f"{'Metric':<30} {'Value':>15}")
    print('-' * 50)
    print(f"{'MAE':<30} {metrics['mae']:>15.8f}")
    print(f"{'RMSE':<30} {metrics['rmse']:>15.8f}")
    print(f"{'Pearson correlation':<30} {metrics['pearson']:>15.8f}")
    print(f"{'Cosine similarity':<30} {metrics['cosine_similarity']:>15.8f}")
    print(f"{'Max absolute error':<30} {metrics['max_abs_error']:>15.8f}")

    # Warning for low cosine
    print()
    if metrics['cosine_similarity'] < 0.999:
        print("⚠ WARNING: Cosine similarity < 0.999")
        print("  Possible causes:")
        print("    - Different CWT wavelet or frequency range")
        print("    - Different normalization (z-score parameters)")
        print("    - Different pooling method (mean vs median)")
        print("    - Polarization not applied (use --mad)")
        print("    - Different gap handling (NaN vs interpolation)")
    else:
        print("✓ PASS: Cosine similarity >= 0.999")

    print()
    print("========================================================")
    print("            VALIDATION COMPLETE")
    print("========================================================")

    # ── Plot ──────────────────────────────────────────────────────────
    if args.plot:
        out_dir = os.path.join(os.path.dirname(args.h5), 'validation_output')
        print(f"\nGenerating difference plots in {out_dir}...")
        try:
            plot_differences(tensor_out, tensor_ref, out_dir)
            print("  Done.")
        except Exception as e:
            logger.error(f"Plotting failed: {e}")

    return 0 if metrics['cosine_similarity'] >= 0.999 else 1


if __name__ == '__main__':
    sys.exit(main())
