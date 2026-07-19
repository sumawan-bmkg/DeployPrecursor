"""RangeRule: physical geomagnetic range validation."""
from ..context import RuleContext
from .base import QCRule


class RangeRule(QCRule):
    name = "range"
    version = "1.0"
    category = "physical"
    description = "Physical geomagnetic range validation"
    weight = 0.30
    priority = "CRITICAL"
    valid_range = (-5000.0, 5000.0)

    def evaluate(self, ctx: RuleContext):
        for name, arr in [("H", ctx.H), ("D", ctx.D), ("Z", ctx.Z)]:
            if arr is None: continue
            vals = arr.ravel()
            if len(vals) == 0: continue
            if float(vals.min()) < self.valid_range[0] or float(vals.max()) > self.valid_range[1]:
                return {"passed": False, "metric": "%s_range" % name,
                        "value": "%.2f to %.2f" % (float(vals.min()), float(vals.max()))}
        return {"passed": True, "metric": "range", "value": "ok"}
