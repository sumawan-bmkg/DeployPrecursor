"""P7 Drift Monitor — track distribution changes over time."""
import json
import os
import numpy as np
from datetime import datetime, timezone
from collections import deque


class DriftMonitor:
    """Monitor distributions of probability, uncertainty, QC score.
    Reports drift when KS-statistic exceeds threshold."""

    def __init__(self, output_dir: str, window_size: int = 100, drift_threshold: float = 0.2):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.window_size = window_size
        self.drift_threshold = drift_threshold
        self._baseline = {"probability": deque(maxlen=1000), "uncertainty": deque(maxlen=1000)}
        self._recent = {"probability": deque(maxlen=self.window_size), "uncertainty": deque(maxlen=self.window_size)}

    def record(self, prediction):
        """Record a prediction into baseline and sliding window."""
        self._baseline["probability"].append(prediction.probability)
        self._baseline["uncertainty"].append(prediction.uncertainty)
        self._recent["probability"].append(prediction.probability)
        self._recent["uncertainty"].append(prediction.uncertainty)

    def check_drift(self) -> dict:
        """Compare recent vs baseline distributions."""
        results = {}
        for field in ["probability", "uncertainty"]:
            bl = list(self._baseline[field])
            rec = list(self._recent[field])
            if len(bl) < self.window_size or len(rec) < self.window_size * 0.5:
                results[field] = {"drifted": False, "ks_stat": 0.0, "reason": "insufficient_data"}
                continue
            from scipy.stats import ks_2samp
            ks_stat, p_val = ks_2samp(bl[-1000:], rec)
            drifted = ks_stat > self.drift_threshold
            results[field] = {
                "drifted": bool(drifted),
                "ks_stat": round(float(ks_stat), 4),
                "p_value": round(float(p_val), 4),
                "baseline_mean": round(float(np.mean(bl[-1000:])), 4),
                "baseline_std": round(float(np.std(bl[-1000:])), 4),
                "recent_mean": round(float(np.mean(rec)), 4),
                "recent_std": round(float(np.std(rec)), 4),
                "n_baseline": min(1000, len(bl)),
                "n_recent": len(rec),
            }
        return results

    def save_report(self, filename: str = "drift_report.json") -> str:
        drift = self.check_drift()
        report = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            "drift_threshold": self.drift_threshold,
            "any_drift": any(d.get("drifted", False) for d in drift.values()),
            "fields": drift,
        }
        fp = os.path.join(self.output_dir, filename)
        with open(fp, "w") as f:
            json.dump(report, f, indent=2)
        return fp
