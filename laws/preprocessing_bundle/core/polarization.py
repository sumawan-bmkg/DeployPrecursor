# utils/polarization.py
"""Polarization feature utilities.

Provides:
- `compute_polarization(H, Z, eps=1e-6, quantile=0.995)`: returns stacked tensor [H, Z, log1p(clipped_ratio)]
- `mad_norm(tensor)`: channel‑wise Median‑Absolute‑Deviation normalization.

All operations are torch‑based for GPU/AMP compatibility.
"""
import torch

def compute_polarization(H: torch.Tensor, Z: torch.Tensor, eps: float = 1e-6, quantile: float = 0.995):
    """Compute physics‑informed polarization channel.

    Parameters
    ----------
    H, Z : torch.Tensor
        Tensors of shape (Freq, Time) – already on the same device.
    eps : float
        Small constant to avoid division by zero.
    quantile : float
        Quantile for adaptive clipping (default 0.995).
    Returns
    -------
    torch.Tensor
        Stacked tensor of shape (3, Freq, Time) = [H, Z, log1p(ratio_clipped)].
    """
    # raw ratio
    ratio = Z / (H + eps)
    # protect NaN/Inf
    ratio = torch.nan_to_num(ratio, nan=0.0, posinf=1e3, neginf=0.0)
    # adaptive clipping
    clip_val = torch.quantile(ratio.flatten(), quantile)
    ratio = torch.clamp(ratio, min=0.0, max=clip_val)
    # log1p transform (numerically stable)
    polarization = torch.log1p(ratio)
    # stack
    return torch.stack([H, Z, polarization], dim=0)

def mad_norm(tensor: torch.Tensor, eps: float = 1e-6):
    """Channel‑wise Median‑Absolute‑Deviation normalization.

    Works on a tensor of shape (C, F, T).
    Returns a tensor of the same shape where each channel is normalized
    as (x - median) / (MAD + eps).
    """
    # compute median per channel
    c = tensor.shape[0]
    # flatten spatial dimensions
    flat = tensor.view(c, -1)
    median = flat.median(dim=1).values.view(c, 1, 1)
    # compute MAD per channel
    mad = (tensor - median).abs().view(c, -1).median(dim=1).values.view(c, 1, 1)
    return (tensor - median) / (mad + eps)
