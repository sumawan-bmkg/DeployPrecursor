"""PSDRule: power spectral density check."""
from ..context import RuleContext
from .base import QCRule
import numpy as np


class PSDRule(QCRule):
    name = "psd"
    version = "1.0"
    category = "statistical"
    description = "Power spectral density dominant frequency ratio"
    weight = 0.10
    priority = "LOW"
    min_dominant_freq_ratio = 0.1

    def evaluate(self, ctx: RuleContext):
        for name, arr in [("H", ctx.H), ("D", ctx.D), ("Z", ctx.Z)]:
            if arr is None: continue
            vals = arr.ravel(); valid = vals[np.isfinite(vals)]
            if len(valid) < 64: continue
            fft_vals = np.abs(np.fft.fft(valid))
            total_power = float(fft_vals.sum())
            if total_power == 0: continue
            max_power = float(fft_vals[1:].max())
            ratio = max_power / total_power
            if ratio < self.min_dominant_freq_ratio:
                return {"passed": False, "metric": "%s_psd_ratio" % name, "value": round(ratio, 4)}
        return {"passed": True, "metric": "psd", "value": "ok"}
