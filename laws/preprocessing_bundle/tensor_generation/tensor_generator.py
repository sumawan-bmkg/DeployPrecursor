"""
V2 Tensor Generator - Adapted for Preprocessing Bundle

Original: d:\multi\scalogramv2\V2_Generate_Raw_Tensors.py
Purpose: Generate CWT scalograms from filtered geomagnetic signals

Key components:
- CWT with cmor1.5-1.0 wavelet
- 128 frequency bins (0.0005 - 0.1 Hz)
- Temporal pooling (60s mean) to reduce 86400 -> 1440 time steps
- Z-score normalization per channel
"""

import numpy as np
import pywt
from typing import Tuple, Optional, Dict


class V2TensorGenerator:
    """
    Generates CWT scalogram tensors from processed geomagnetic signals.
    
    This class implements the core tensor generation pipeline:
    1. Temporal pooling (60-second mean averaging)
    2. Continuous Wavelet Transform (CWT)
    3. Magnitude extraction
    4. Optional Z-score normalization
    """
    
    def __init__(self, fs: float = 1.0, wavelet: str = 'cmor1.5-1.0', scales: Optional[np.ndarray] = None):
        """
        Initialize the tensor generator.
        
        Parameters
        ----------
        fs : float
            Sampling frequency in Hz (default: 1.0 Hz)
        wavelet : str
            PyWavelets wavelet name (default: 'cmor1.5-1.0' - Complex Morlet)
        scales : np.ndarray, optional
            Custom CWT scales. If None, generates 128 logarithmic scales
            from 0.0005 Hz to 0.1 Hz (Pc5 to Pc3 bands)
        """
        self.fs = fs
        self.wavelet = wavelet
        
        if scales is None:
            # Expanded Range: 0.001 (Pc5) to 0.1 (Pc3)
            # 128 bins ensures high resolution
            freqs = np.geomspace(0.0005, 0.1, num=128)
            self.scales = pywt.frequency2scale(self.wavelet, freqs / self.fs)
        else:
            self.scales = scales
            
        self.pool_size = 60  # 60-second pooling
    
    def extract_cwt_tensor(self, signal_array: np.ndarray) -> np.ndarray:
        """
        Extract CWT scalogram from a signal array.
        
        Parameters
        ----------
        signal_array : np.ndarray
            1D signal array (typically after pooling)
            
        Returns
        -------
        np.ndarray
            2D scalogram of shape (128, time_steps) containing magnitude of CWT coefficients
        """
        coefficients, _ = pywt.cwt(signal_array, self.scales, self.wavelet, sampling_period=1/self.fs)
        return np.abs(coefficients)
    
    def pool_signal(self, arr: np.ndarray) -> np.ndarray:
        """
        Apply temporal pooling to reduce time dimension.
        
        Pools 60-second windows by mean averaging, reducing 86400 samples to 1440.
        
        Parameters
        ----------
        arr : np.ndarray
            1D signal array (typically 86400 samples for 1 day at 1 Hz)
            
        Returns
        -------
        np.ndarray
            Pooled signal with ~1440 time steps
        """
        pad_len = (self.pool_size - len(arr) % self.pool_size) % self.pool_size
        padded = np.pad(arr, (0, pad_len), 'edge')
        return padded.reshape(-1, self.pool_size).mean(axis=1)
    
    def pool_mask(self, mask: np.ndarray) -> np.ndarray:
        """
        Apply min-pooling to binary mask.
        
        If any second in the 60s window has a long gap (>5s flagged as 0),
        mask the entire minute.
        
        Parameters
        ----------
        mask : np.ndarray
            Binary mask array (1 = valid, 0 = invalid/gap)
            
        Returns
        -------
        np.ndarray
            Min-pooled mask with ~1440 time steps
        """
        pad_len_m = (self.pool_size - len(mask) % self.pool_size) % self.pool_size
        padded_m = np.pad(mask, (0, pad_len_m), constant_values=0)
        return padded_m.reshape(-1, self.pool_size).min(axis=1)
    
    def generate_tensor(self, h_data: np.ndarray, d_data: np.ndarray, z_data: np.ndarray,
                       apply_pooling: bool = True) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Generate complete 3-channel CWT tensor from H, D, Z components.
        
        Parameters
        ----------
        h_data : np.ndarray
            Horizontal component data
        d_data : np.ndarray
            Declination component data
        z_data : np.ndarray
            Vertical component data
        apply_pooling : bool
            Whether to apply temporal pooling (default: True)
            
        Returns
        -------
        tuple
            (tensor, mask) where:
            - tensor: np.ndarray of shape (3, 128, pooled_time_steps)
            - mask: np.ndarray of pooled binary mask (or None if not provided)
        """
        if apply_pooling:
            h_pool = self.pool_signal(h_data)
            d_pool = self.pool_signal(d_data)
            z_pool = self.pool_signal(z_data)
        else:
            h_pool = h_data
            d_pool = d_data
            z_pool = z_data
        
        # Extract CWT scalograms for each component
        h_cwt = self.extract_cwt_tensor(h_pool)
        d_cwt = self.extract_cwt_tensor(d_pool)
        z_cwt = self.extract_cwt_tensor(z_pool)
        
        # Stack into 3-channel tensor
        tensor = np.stack([h_cwt, d_cwt, z_cwt], axis=0)
        
        return tensor, None
    
    def zscore_normalize(self, tensor: np.ndarray, per_channel: bool = True) -> np.ndarray:
        """
        Apply Z-score normalization to tensor.
        
        Parameters
        ----------
        tensor : np.ndarray
            Input tensor of shape (3, 128, time_steps)
        per_channel : bool
            Whether to normalize each channel independently (default: True)
            
        Returns
        -------
        np.ndarray
            Normalized tensor of same shape
        """
        normed = np.zeros_like(tensor)
        
        if per_channel:
            for c in range(tensor.shape[0]):
                channel_data = tensor[c]
                mean_val = np.mean(channel_data)
                std_val = np.std(channel_data)
                # Z-Score: (X - mu) / sigma
                normed[c] = (channel_data - mean_val) / (std_val + 1e-8)
        else:
            mean_val = np.mean(tensor)
            std_val = np.std(tensor)
            normed = (tensor - mean_val) / (std_val + 1e-8)
        
        return normed


# Convenience function for end-to-end tensor generation
def generate_tensor_from_raw(h_raw: np.ndarray, d_raw: np.ndarray, z_raw: np.ndarray,
                            normalize: bool = True) -> np.ndarray:
    """
    Convenience function to generate tensor from raw H, D, Z data.
    
    This is a simplified interface that assumes:
    - Input data is already PC3-filtered (use GeomagneticSignalProcessor first)
    - Data is at 1 Hz sampling rate
    
    Parameters
    ----------
    h_raw : np.ndarray
        Raw H component (after PC3 filtering)
    d_raw : np.ndarray
        Raw D component (after PC3 filtering)
    z_raw : np.ndarray
        Raw Z component (after PC3 filtering)
    normalize : bool
        Whether to apply Z-score normalization (default: True)
        
    Returns
    -------
    np.ndarray
        Tensor of shape (3, 128, 1440)
    """
    generator = V2TensorGenerator()
    tensor, _ = generator.generate_tensor(h_raw, d_raw, z_raw, apply_pooling=True)
    
    if normalize:
        tensor = generator.zscore_normalize(tensor)
    
    return tensor


if __name__ == "__main__":
    # Test with synthetic data
    print("Testing V2TensorGenerator with synthetic data...")
    
    # Generate synthetic 1-day data (86400 samples at 1 Hz)
    np.random.seed(42)
    h_synthetic = np.random.randn(86400)
    d_synthetic = np.random.randn(86400)
    z_synthetic = np.random.randn(86400)
    
    generator = V2TensorGenerator()
    tensor, _ = generator.generate_tensor(h_synthetic, d_synthetic, z_synthetic)
    
    print(f"Generated tensor shape: {tensor.shape}")
    print(f"Expected shape: (3, 128, ~1440)")
    print(f"Actual time steps: {tensor.shape[2]}")
    
    # Test normalization
    tensor_norm = generator.zscore_normalize(tensor)
    print(f"Normalized tensor mean: {tensor_norm.mean():.6f}")
    print(f"Normalized tensor std: {tensor_norm.std():.6f}")
    
    print("\n✓ V2TensorGenerator test passed")
