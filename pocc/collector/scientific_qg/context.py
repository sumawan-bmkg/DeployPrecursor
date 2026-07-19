"""RuleContext - Single input object for all QC rules."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class RuleContext:
    """Single input contract for all QC rules.
    Stable. Add fields here when new data sources become available.
    """
    H: Optional[Any] = None
    D: Optional[Any] = None
    Z: Optional[Any] = None
    station: str = ""
    utc: str = ""
    sampling_rate: float = 1.0
    pipeline_version: str = ""
    kp: Optional[float] = None
    dst: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_arrays(cls, H, D, Z, **kw):
        return cls(H=H, D=D, Z=Z, **kw)
