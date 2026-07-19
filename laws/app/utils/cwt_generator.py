#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cwt_generator.py — On-the-fly Continuous Wavelet Transform (CWT) generator.

Generates 2D scalogram tensors of shape [Batch, 3, 128, 1440] from 
raw magnetometer time series components (H, D, Z).
Optimized using PyTorch Batched 1D-FFT Convolution for sub-50ms latency.
"""

import numpy as np
import pywt
import torch
from typing import List, Dict

class RealTimeCWTGenerator:
    """
    On-the-fly CWT generator for real-time inference using Batched FFT.
    Uses 'cmor1.5-1.0' wavelet and 128 scales.
    """
    def __init__(self, fs: float = 1.0, wavelet: str = 'cmor1.5-1.0', n_samples: int = 1440):
        self.fs = fs
        self.wavelet = wavelet
        self.n_samples = n_samples
        
        # Logarithmic scales from 0.0005 Hz to 0.1 Hz (Pc5 to Pc3 bands)
        freqs = np.geomspace(0.0005, 0.1, num=128)
        self.scales = pywt.frequency2scale(self.wavelet, freqs / self.fs)
        
        # Precompute FFT filters (Filter Bank)
        self.wavelet_fft_filters = self._precompute_fft_filters()

    def _precompute_fft_filters(self) -> torch.Tensor:
        """
        Precomputes the frequency domain representation of the wavelets
        for fast FFT-based convolution.
        """
        impulse = np.zeros(self.n_samples)
        impulse[self.n_samples // 2] = 1.0
        
        # Get impulse response of pywt.cwt
        coefs, _ = pywt.cwt(impulse, self.scales, self.wavelet, sampling_period=1.0 / self.fs)
        
        # Shift impulse response to time 0
        shifted = np.roll(coefs, -self.n_samples // 2, axis=1)
        
        # Convert to frequency domain
        fft_filters = np.fft.fft(shifted, axis=1)
        
        # Shape: [1, 1, 128, 1440] to broadcast with [Batch, Channels, 1, Time]
        fft_filters_t = torch.from_numpy(fft_filters).to(torch.complex64)
        return fft_filters_t.unsqueeze(0).unsqueeze(0)

    def zscore_normalize_batch(self, scalogram: torch.Tensor) -> torch.Tensor:
        """
        Apply Z-score normalization to each channel in the batch independently.
        scalogram shape: [Batch, 3, 128, 1440]
        """
        # Compute mean and std over the last two dimensions (128, 1440)
        mean_val = scalogram.mean(dim=(-2, -1), keepdim=True)
        std_val = scalogram.std(dim=(-2, -1), keepdim=True)
        return (scalogram - mean_val) / (std_val + 1e-8)

    def generate_tensor_batch(
        self, 
        signals: List[Dict[str, List[float]]],
        normalize: bool = True
    ) -> torch.Tensor:
        """
        Convert a batch of raw station signals to a PyTorch tensor using Batched FFT.
        
        Args:
            signals: List of dicts, each with 'raw_h', 'raw_d', 'raw_z' lists (len 1440).
            normalize: If True, apply z-score normalization to each channel.
            
        Returns:
            tensor: torch.Tensor of shape [Batch, 3, 128, 1440] on CPU.
        """
        batch_size = len(signals)
        
        # 1. Prepare batch tensor [Batch, Channels, Time]
        batch_np = np.zeros((batch_size, 3, self.n_samples), dtype=np.float32)
        for i, sig_dict in enumerate(signals):
            h = np.array(sig_dict['raw_h'], dtype=np.float32)
            d = np.array(sig_dict['raw_d'], dtype=np.float32)
            z = np.array(sig_dict['raw_z'], dtype=np.float32)
            
            if len(h) != self.n_samples: h = np.interp(np.linspace(0, 1, self.n_samples), np.linspace(0, 1, len(h)), h)
            if len(d) != self.n_samples: d = np.interp(np.linspace(0, 1, self.n_samples), np.linspace(0, 1, len(d)), d)
            if len(z) != self.n_samples: z = np.interp(np.linspace(0, 1, self.n_samples), np.linspace(0, 1, len(z)), z)
                
            batch_np[i, 0] = h
            batch_np[i, 1] = d
            batch_np[i, 2] = z
            
        batch_t = torch.from_numpy(batch_np)  # [Batch, 3, 1440]
        
        # 2. FFT CWT Execution
        # FFT of signals: [Batch, 3, 1440] -> unsqueeze -> [Batch, 3, 1, 1440]
        batch_fft = torch.fft.fft(batch_t, dim=2).unsqueeze(2)
        
        # Element-wise multiply with precomputed filters: [1, 1, 128, 1440]
        # Broadcasting -> [Batch, 3, 128, 1440]
        out_fft = batch_fft * self.wavelet_fft_filters
        
        # IFFT and magnitude
        out_t = torch.fft.ifft(out_fft, dim=3)
        out_mag = torch.abs(out_t)  # [Batch, 3, 128, 1440]
        
        # 3. Normalization
        if normalize:
            out_mag = self.zscore_normalize_batch(out_mag)
            
        return out_mag

# Singleton helper
_cwt_gen = RealTimeCWTGenerator()

def generate_cwt_tensor_batch(signals: List[Dict[str, List[float]]], normalize: bool = True) -> torch.Tensor:
    """Helper function to generate CWT batch tensor using Batched FFT."""
    return _cwt_gen.generate_tensor_batch(signals, normalize=normalize)
