"""CrossCorrelationRule: cross-component consistency."""
from ..context import RuleContext
from .base import QCRule
import numpy as np


class CrossCorrelationRule(QCRule):
    name = "cross_correlation"
    version = "1.0"
    category = "physical"
    description = "Cross-component correlation check"
    weight = 0.20
    priority = "HIGH"
    min_correlation = 0.1

    def evaluate(self, ctx: RuleContext):
        comps = [c for c in [ctx.H, ctx.D, ctx.Z] if c is not None]
        if len(comps) < 2: return {"passed": True, "metric": "cross_correlation", "value": "skip"}
        for i in range(len(comps)):
            for j in range(i + 1, len(comps)):
                a = comps[i].ravel(); b = comps[j].ravel()
                n = min(len(a), len(b))
                if n < 10: continue
                a_v = a[:n][np.isfinite(a[:n])]; b_v = b[:n][np.isfinite(b[:n])]
                m = min(len(a_v), len(b_v))
                if m < 5: continue
                corr = float(np.corrcoef(a_v[:m], b_v[:m])[0, 1])
                if abs(corr) < self.min_correlation:
                    return {"passed": False, "metric": "cross_correlation", "value": round(corr, 4)}
        return {"passed": True, "metric": "cross_correlation", "value": "ok"}
