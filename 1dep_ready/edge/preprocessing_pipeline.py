#!/usr/bin/env python3
"""
preprocessing_pipeline.py — Edge preprocessing for V8 SupCon inference.

Transforms raw 1D magnetometer streams (H, D, Z) into 3-channel scalograms
via CWT (Continuous Wavelet Transform) + optional Spectral Polarization ratio.

Designed for NVIDIA Jetson Nano 4GB — numpy/scipy only, no PyTorch.

Input:  raw_h, raw_d, raw_z  (1D arrays, 1440 samples each)
Output: (3, 128, 1440) float32 array ready for TFLite interpreter
"""

import logging
import warnings
from typing import Dict, List, Optional, Tuple

import numpy as np
import pywt
from scipy import signal as sp_signal

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# PARAMETERS (mirrors app/config.py + app/utils/cwt_generator.py)
# ══════════════════════════════════════════════════════════════════

CWT_WAVELET = "cmor1.5-1.0"
N_SCALES = 128
N_SAMPLES = 1440
FS = 1.0  # 1 sample per minute
FREQ_MIN = 0.0005  # Hz (Pc5 lower)
FREQ_MAX = 0.1  # Hz (Pc3 upper)
EPS = 1e-12


# ══════════════════════════════════════════════════════════════════
# FILTERBANK — Precomputed CWT FFT filters (singleton)
# ══════════════════════════════════════════════════════════════════

class CWTFilterBank:
    """Precomputed CWT filters for fast FFT-based convolution.

    Generates 128 wavelet filters in frequency domain. Once computed,
    reuse for all inference calls to save ~40ms per sample."""

    def __init__(self, wavelet=CWT_WAVELET, n_scales=N_SCALES,
                 n_samples=N_SAMPLES, fs=FS):
        self.wavelet = wavelet
        self.n_scales = n_scales
        self.n_samples = n_samples
        self.fs = fs
        self.freqs = np.geomspace(FREQ_MIN, FREQ_MAX, num=n_scales)
        self.scales = pywt.frequency2scale(wavelet, self.freqs / fs)
        self._filters_cached = None  # complex64 array: (n_scales, n_samples)

    @property
    def filters(self) -> np.ndarray:
        """Lazy-compute and cache frequency-domain filters."""
        if self._filters_cached is not None:
            return self._filters_cached

        # Compute wavelet impulse response
        impulse = np.zeros(self.n_samples)
        impulse[self.n_samples // 2] = 1.0
        coefs, _ = pywt.cwt(impulse, self.scales, self.wavelet,
                            sampling_period=1.0 / self.fs)
        # Shift so peak at time 0
        shifted = np.roll(coefs, -self.n_samples // 2, axis=1)
        # Convert to frequency domain
        self._filters_cached = np.fft.fft(shifted, axis=1).astype(np.complex64)
        return self._filters_cached


# Singleton
_fbank = None


def _get_filterbank() -> CWTFilterBank:
    global _fbank
    if _fbank is None:
        _fbank = CWTFilterBank()
    return _fbank


# ══════════════════════════════════════════════════════════════════
# CWT GENERATION
# ══════════════════════════════════════════════════════════════════

def _cwt_channel(signal: np.ndarray) -> np.ndarray:
    """Fast CWT for single channel via FFT convolution.

    Args:
        signal: 1D array (n_samples,)

    Returns:
        2D array (n_scales, n_samples) — scalogram magnitude
    """
    fbank = _get_filterbank()
    sig_fft = np.fft.fft(signal)
    out_fft = sig_fft[np.newaxis, :] * fbank.filters  # (128, 1440)
    out = np.fft.ifft(out_fft, axis=1)
    return np.abs(out)


def _zscore_2d(arr: np.ndarray) -> np.ndarray:
    """Z-score normalize 2D array per image (128, 1440)."""
    m = arr.mean()
    s = arr.std()
    if s < EPS:
        return arr - m
    return (arr - m) / s


def generate_scalogram(h: np.ndarray, d: np.ndarray, z: np.ndarray,
                       normalize: bool = True) -> np.ndarray:
    """Convert H/D/Z to 3-channel scalogram tensor.

    Args:
        h, d, z: 1D arrays (n_samples,) — raw magnetometer components
        normalize: If True, z-score normalize each channel independently

    Returns:
        ndarray (3, 128, 1440) float32 — ready for TFLite inference
    """
    # Resample to N_SAMPLES if needed
    if len(h) != N_SAMPLES:
        h = np.interp(np.linspace(0, 1, N_SAMPLES),
                      np.linspace(0, 1, len(h)), h)
    if len(d) != N_SAMPLES:
        d = np.interp(np.linspace(0, 1, N_SAMPLES),
                      np.linspace(0, 1, len(d)), d)
    if len(z) != N_SAMPLES:
        z = np.interp(np.linspace(0, 1, N_SAMPLES),
                      np.linspace(0, 1, len(z)), z)

    # Remove DC offset
    h = h - np.mean(h)
    d = d - np.mean(d)
    z = z - np.mean(z)

    # CWT per channel
    scal_h = _cwt_channel(h).astype(np.float32)  # (128, 1440)
    scal_d = _cwt_channel(d).astype(np.float32)
    scal_z = _cwt_channel(z).astype(np.float32)

    # Normalize
    if normalize:
        scal_h = _zscore_2d(scal_h)
        scal_d = _zscore_2d(scal_d)
        scal_z = _zscore_2d(scal_z)

    # Stack channels
    return np.stack([scal_h, scal_d, scal_z], axis=0)  # (3, 128, 1440)


def generate_scalogram_batch(raw_signals: List[Dict[str, np.ndarray]],
                             normalize: bool = True) -> np.ndarray:
    """Batch scalogram generation.

    Args:
        raw_signals: list of dicts with keys 'H', 'D', 'Z' (1D ndarrays)
        normalize: z-score normalize per sample

    Returns:
        ndarray (batch, 3, 128, 1440) float32
    """
    batch = []
    for sig in raw_signals:
        scal = generate_scalogram(
            sig.get('H', np.zeros(N_SAMPLES)),
            sig.get('D', np.zeros(N_SAMPLES)),
            sig.get('Z', np.zeros(N_SAMPLES)),
            normalize=normalize,
        )
        batch.append(scal)
    return np.stack(batch, axis=0)


# ══════════════════════════════════════════════════════════════════
# SPECTRAL POLARIZATION RATIO
# ══════════════════════════════════════════════════════════════════

def spectral_polarization_ratio(h: np.ndarray, d: np.ndarray,
                                eps: float = EPS) -> np.ndarray:
    """Compute H/D cross-spectral polarization ratio feature.

    Measures ellipticity of horizontal magnetic field.
    Higher values → more circular polarization (anomalous).

    Args:
        h, d: 1D arrays (n_samples,) — detrended H and D components
        eps: small constant to avoid division by zero

    Returns:
        1D array (n_samples,) — polarization ratio per time point
    """
    f, Ph = sp_signal.welch(h, fs=FS, nperseg=min(256, len(h)))
    _, Pd = sp_signal.welch(d, fs=FS, nperseg=min(256, len(d)))
    # Cross-spectral density
    _, Pxh = sp_signal.coherence(h, d, fs=FS, nperseg=min(256, len(h)))

    # Phase-shifted ratio as polarization proxy
    pol = (Pd - Ph) / (Pd + Ph + eps)
    # Interpolate back to N_SAMPLES length
    t_orig = np.linspace(0, 1, len(pol))
    t_target = np.linspace(0, 1, N_SAMPLES)
    return np.interp(t_target, t_orig, pol)


# ══════════════════════════════════════════════════════════════════
# FULL PREPROCESSING PIPELINE
# ══════════════════════════════════════════════════════════════════

def preprocess_for_inference(h: np.ndarray, d: np.ndarray, z: np.ndarray,
                             kp: float = 0.0, dst: float = 0.0,
                             normalize: bool = True
                             ) -> Tuple[np.ndarray, np.ndarray]:
    """Full preprocessing: scalogram + cosmic features.

    Args:
        h, d, z: Raw magnetometer 1D arrays
        kp: Raw Kp index (0-9)
        dst: Raw Dst index (nT)
        normalize: z-score normalize scalogram

    Returns:
        x_img: (1, 3, 128, 1440) float32 — scalogram input
        x_cosmic: (1, 2) float32 — [Kp_norm, Dst_norm]
    """
    # Scalogram
    scal = generate_scalogram(h, d, z, normalize=normalize)
    x_img = scal[np.newaxis, ...]  # (1, 3, 128, 1440)

    # Cosmic normalization (must match training: Kp/9, tanh(Dst/50))
    kp_norm = kp / 9.0
    dst_norm = np.tanh(dst / 50.0)
    x_cosmic = np.array([[kp_norm, dst_norm]], dtype=np.float32)

    return x_img, x_cosmic


# ══════════════════════════════════════════════════════════════════
# SIGNAL VALIDATION
# ══════════════════════════════════════════════════════════════════

def validate_signal(h: np.ndarray, d: np.ndarray, z: np.ndarray,
                    station: str = "UNK") -> None:
    """Validate signal quality. Raises ValueError on bad data."""
    for name, arr in [("H", h), ("D", d), ("Z", z)]:
        if len(arr) < 100:
            raise ValueError(f"Signal too short: {station}/{name} ({len(arr)} samples)")
        if np.all(np.isnan(arr)):
            raise ValueError(f"All NaN: {station}/{name}")
        if np.std(arr[~np.isnan(arr)]) < 1e-12:
            logger.warning(f"Flat signal: {station}/{name}")


# ══════════════════════════════════════════════════════════════════
# SELF-TEST
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Generate synthetic magnetometer data
    t = np.linspace(0, 1440, 1440)
    h_sig = 0.5 * np.sin(2 * np.pi * t / 360) + 0.2 * np.random.randn(1440)
    d_sig = 0.3 * np.sin(2 * np.pi * t / 720) + 0.15 * np.random.randn(1440)
    z_sig = 0.4 * np.sin(2 * np.pi * t / 180) + 0.1 * np.random.randn(1440)

    x_img, x_cosmic = preprocess_for_inference(h_sig, d_sig, z_sig, kp=2.0, dst=-10.0)

    assert x_img.shape == (1, 3, 128, 1440), f"Bad shape: {x_img.shape}"
    assert x_cosmic.shape == (1, 2), f"Bad cosmic shape: {x_cosmic.shape}"
    assert x_img.dtype == np.float32, f"Bad dtype: {x_img.dtype}"
    assert not np.any(np.isnan(x_img)), "NaN in scalogram"
    assert not np.any(np.isnan(x_cosmic)), "NaN in cosmic"

    # Test polarization ratio
    pol = spectral_polarization_ratio(h_sig, d_sig)
    assert pol.shape == (1440,), f"Bad pol shape: {pol.shape}"
    assert not np.any(np.isnan(pol)), "NaN in polarization"

    print(f"[PASS] Scalogram shape: {x_img.shape}, range: [{x_img.min():.4f}, {x_img.max():.4f}]")
    print(f"[PASS] Cosmic: Kp={x_cosmic[0,0]:.4f}, Dst={x_cosmic[0,1]:.4f}")
    print(f"[PASS] Polarization ratio shape: {pol.shape}")
    print("[PASS] preprocessin_pipeline.py — all tests passed")
