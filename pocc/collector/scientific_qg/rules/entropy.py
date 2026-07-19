"""EntropyRule: Shannon entropy check."""
from ..context import RuleContext
from .base import QCRule
import math, numpy as np


class EntropyRule(QCRule):
    name = "entropy"
    version = "1.0"
    category = "statistical"
    description = "Shannon entropy of waveform amplitude distribution"
    weight = 0.10
    priority = "MEDIUM"
    min_entropy = 2.0

    def evaluate(self, ctx: RuleContext):
        for name, arr in [("H", ctx.H), ("D", ctx.D), ("Z", ctx.Z)]:
            if arr is None: continue
            vals = arr.ravel(); valid = vals[np.isfinite(vals)]
            if len(valid) < 10: continue
            hist, _ = np.histogram(valid, bins=256)
            probs = hist[hist > 0] / float(hist.sum())
            entropy = -float(sum(p * math.log2(float(p)) for p in probs))
            if entropy < self.min_entropy:
                return {"passed": False, "metric": "%s_entropy" % name, "value": round(entropy, 4)}
        return {"passed": True, "metric": "entropy", "value": "ok"}
