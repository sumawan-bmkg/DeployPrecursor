"""MissingSampleRule: check total NaN fraction."""
from ..context import RuleContext
from .base import QCRule
import numpy as np


class MissingSampleRule(QCRule):
    name = "missing_sample"
    version = "1.0"
    category = "physical"
    description = "Total NaN fraction check"
    weight = 0.10
    priority = "HIGH"
    max_nan_fraction = 0.5

    def evaluate(self, ctx: RuleContext):
        for name, arr in [("H", ctx.H), ("D", ctx.D), ("Z", ctx.Z)]:
            if arr is None: continue
            vals = arr.ravel()
            nan_frac = float(np.isnan(vals).sum()) / len(vals) if len(vals) > 0 else 0
            if nan_frac > self.max_nan_fraction:
                return {"passed": False, "metric": "%s_nan_fraction" % name, "value": round(nan_frac, 4)}
        return {"passed": True, "metric": "missing_sample", "value": "ok"}
