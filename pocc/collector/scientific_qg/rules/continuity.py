"""ContinuityRule: check for NaN or zero runs."""
from ..context import RuleContext
from .base import QCRule


class ContinuityRule(QCRule):
    name = "continuity"
    version = "1.0"
    category = "physical"
    description = "NaN or zero run length check"
    weight = 0.20
    priority = "HIGH"
    max_consecutive_nan = 600

    def evaluate(self, ctx: RuleContext):
        for name, arr in [("H", ctx.H), ("D", ctx.D), ("Z", ctx.Z)]:
            if arr is None: continue
            vals = arr.ravel()
            max_run = run = 0
            for v in vals:
                if v != v or v == 0:
                    run += 1; max_run = max(max_run, run)
                else: run = 0
            if max_run > self.max_consecutive_nan:
                return {"passed": False, "metric": "%s_max_run" % name, "value": max_run}
        return {"passed": True, "metric": "continuity", "value": "ok"}
