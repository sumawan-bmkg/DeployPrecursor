"""SpectralRule: check spectral anomalies."""
from ..context import RuleContext
from .base import QCRule
import math, numpy as np


class SpectralRule(QCRule):
    name = "spectral"
    version = "1.0"
    category = "statistical"
    description = "Spectral anomaly detection via entropy"
    weight = 0.10
    priority = "MEDIUM"
    min_entropy = 3.0

    def evaluate(self, ctx: RuleContext):
        for name, arr in [("H", ctx.H), ("D", ctx.D), ("Z", ctx.Z)]:
            if arr is None: continue
            vals = arr.ravel(); valid = vals[np.isfinite(vals)]
            if len(valid) < 10: continue
            abs_v = np.abs(valid); total = float(abs_v.sum())
            if total == 0: continue
            probs = abs_v / total
            entropy = -float(sum(p * math.log2(float(p)) for p in probs if float(p) > 0))
            if entropy < self.min_entropy:
                return {"passed": False, "metric": "%s_entropy" % name, "value": round(entropy, 4)}
        return {"passed": True, "metric": "spectral", "value": "ok"}
