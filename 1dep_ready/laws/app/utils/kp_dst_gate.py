#!/usr/bin/env python3
"""
kp_dst_gate.py — Geomagnetic storm gate (Kp/Dst) for V9.5 PIMES filter.

If Kp > threshold or Dst < threshold, V9.5 is bypassed (high noise regime).
In that mode, only V8 magnitude estimation runs.

Reference:
  - Kp ≥ 5 → G-scale minor storm
  - Dst ≤ −50 nT → moderate storm
  - Training MAG-R3: data with Kp > 4 or Dst < -30 degraded performance
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class StormGateConfig:
    """Configurable thresholds for geomagnetic storm gate."""

    kp_threshold: float = 4.0       # Kp > this → storm mode
    dst_threshold: float = -30.0    # Dst < this → storm mode
    strict_mode: bool = False       # If True, also check individual station Kp


DEFAULT_GATE_CONFIG = StormGateConfig()


def storm_gate_decision(
    kp_norm: float,
    dst_norm: float,
    kp_raw: Optional[float] = None,
    dst_raw: Optional[float] = None,
    config: StormGateConfig = DEFAULT_GATE_CONFIG,
) -> dict:
    """
    Evaluate geomagnetic storm gate.

    Args:
        kp_norm: Normalized Kp (0-1 range, = raw/9.0)
        dst_norm: Normalized Dst (tanh-scaled)
        kp_raw: Optional raw Kp value for threshold comparison
        dst_raw: Optional raw Dst value for threshold comparison
        config: StormGateConfig with thresholds

    Returns:
        dict with:
            storm_mode: bool (True = bypass V9.5)
            reason: str explanation
            kp_value: float (raw if available, else back-computed)
            dst_value: float (raw if available, else back-computed)
    """
    # Back-compute raw values if not provided
    if kp_raw is None:
        kp_raw = kp_norm * 9.0
    if dst_raw is None:
        # Inverse of tanh(x/50): x = 50 * arctanh(dst_norm)
        import math
        dst_clipped = max(-0.999, min(0.999, dst_norm))
        dst_raw = 50.0 * math.atanh(dst_clipped)

    storm = bool(kp_raw > config.kp_threshold or dst_raw < config.dst_threshold)

    reasons = []
    if kp_raw > config.kp_threshold:
        reasons.append(f'Kp={kp_raw:.1f} > {config.kp_threshold}')
    if dst_raw < config.dst_threshold:
        reasons.append(f'Dst={dst_raw:.0f} < {config.dst_threshold}')

    return {
        'storm_mode': storm,
        'reason': ' | '.join(reasons) if reasons else 'clear',
        'kp_raw': round(kp_raw, 1),
        'dst_raw': round(dst_raw, 0),
    }


def should_run_v95(kp_norm: float, dst_norm: float) -> bool:
    """
    Quick check: should V9.5 gatekeeper run?

    Returns False if geomagnetic conditions are too noisy for PIMES filter.
    """
    kp_raw = kp_norm * 9.0
    dst_raw = 50.0 * __import__('math').atanh(max(-0.999, min(0.999, dst_norm)))
    return not (kp_raw > 4.0 or dst_raw < -30.0)
