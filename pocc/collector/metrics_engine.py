"""P7 Metrics Engine — compute operational prediction metrics."""
import json
import os
import time
from datetime import datetime, timezone


class MetricsEngine:
    """Compute and track prediction quality metrics over time."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self._predictions = []

    def record(self, prediction, ground_truth: bool = False, eq_matched: bool = False):
        """Record a prediction with its ground truth label."""
        self._predictions.append({
            "timestamp": prediction.timestamp,
            "station": prediction.station,
            "probability": prediction.probability,
            "confidence": prediction.confidence,
            "uncertainty": prediction.uncertainty,
            "model_name": prediction.model_name,
            "backend": prediction.backend,
            "latency_ms": prediction.latency_ms,
            "ground_truth": ground_truth,
            "eq_matched": eq_matched,
        })

    def compute_metrics(self) -> dict:
        """Compute all metrics from recorded predictions."""
        if not self._predictions:
            return self._empty_metrics()

        probs = [p["probability"] for p in self._predictions]
        latencies = [p["latency_ms"] for p in self._predictions]
        uncertainties = [p["uncertainty"] for p in self._predictions]
        gt_labels = [p["ground_truth"] for p in self._predictions]
        pred_labels = [p["probability"] > 0.5 for p in self._predictions]
        eq_matches = [p["eq_matched"] for p in self._predictions]

        n = len(probs)
        tp = sum(1 for g, p in zip(gt_labels, pred_labels) if g and p)
        fp = sum(1 for g, p in zip(gt_labels, pred_labels) if not g and p)
        tn = sum(1 for g, p in zip(gt_labels, pred_labels) if not g and not p)
        fn = sum(1 for g, p in zip(gt_labels, pred_labels) if g and not p)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        far = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        miss_rate = fn / (fn + tp) if (fn + tp) > 0 else 0.0

        # Brier score
        brier = sum((p["probability"] - (1.0 if gt else 0.0)) ** 2
                     for p, gt in zip(self._predictions, gt_labels)) / n

        return {
            "n_predictions": n,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "far": round(far, 4),
            "miss_rate": round(miss_rate, 4),
            "brier_score": round(brier, 4),
            "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "mean_probability": round(sum(probs) / n, 4),
            "mean_uncertainty": round(sum(uncertainties) / n, 4),
            "mean_latency_ms": round(sum(latencies) / n, 4),
            "max_latency_ms": round(max(latencies), 4),
            "coverage": 1.0,
            "eq_events_detected": sum(eq_matches),
            "computed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def save_metrics(self, filename: str = "metrics.json") -> str:
        metrics = self.compute_metrics()
        fp = os.path.join(self.output_dir, filename)
        with open(fp, "w") as f:
            json.dump(metrics, f, indent=2)
        return fp

    def _empty_metrics(self):
        return {
            "n_predictions": 0, "precision": 0, "recall": 0, "far": 0,
            "miss_rate": 0, "brier_score": 0, "tp": 0, "fp": 0, "tn": 0, "fn": 0,
            "coverage": 0, "computed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        }
