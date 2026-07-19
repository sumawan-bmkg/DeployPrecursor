"""FlatlineRule: detect stuck/frozen sensor."""
from ..context import RuleContext
from .base import QCRule
import numpy as np


class FlatlineRule(QCRule):
    name = "flatline"
    version = "1.1"
    category = "signal_quality"
    description = "Detect stuck sensor via consecutive near-zero differences"
    weight = 0.15
    priority = "HIGH"

    min_rolling_std = 0.001  # nT — typical 1Hz diff is ~0.1 nT
    max_consecutive_minutes = 10

    def evaluate(self, ctx: RuleContext):
        sampling_rate = getattr(ctx, 'sampling_rate', None) or 1.0
        threshold_samples = int(self.max_consecutive_minutes * 60 * sampling_rate)

        for name, arr in [("H", ctx.H), ("D", ctx.D), ("Z", ctx.Z)]:
            if arr is None:
                continue
            vals = arr.ravel()
            valid = vals[np.isfinite(vals)]
            if len(valid) < threshold_samples + 1:
                continue

            # Count consecutive near-zero diffs
            diffs = np.abs(np.diff(valid))
            flat = diffs < self.min_rolling_std

            # Find longest consecutive True run in flat array
            # Use rle: where value changes from False to True
            max_run = 0
            current_run = 0
            for is_flat in flat:
                if is_flat:
                    current_run += 1
                    if current_run > max_run:
                        max_run = current_run
                else:
                    current_run = 0

            if max_run >= threshold_samples:
                return {
                    "passed": False,
                    "metric": f"{name}_flatline_run",
                    "value": int(max_run),
                    "details": f"stuck for {max_run / sampling_rate:.0f}s"
                }

        return {"passed": True, "metric": "flatline", "value": "ok"}
