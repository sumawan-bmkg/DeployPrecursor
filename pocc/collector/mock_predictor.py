"""MockPredictor implementing PredictorInterface (P6B+P6C)."""
import os, json, time, hashlib
from collector.predictor_base import PredictorInterface, Prediction


class MockPredictor(PredictorInterface):
    """Deterministic mock predictor. No AI model needed."""

    def __init__(self, mode="normal", anomaly_threshold=0.3):
        self.mode = mode
        self.anomaly_threshold = anomaly_threshold
        self._version = "mock-1.0"

    def get_name(self) -> str:
        return "MockPredictor"

    def get_model_info(self) -> dict:
        return {
            "model_name": self.get_name(),
            "version": self._version,
            "mode": self.mode,
            "anomaly_threshold": self.anomaly_threshold,
            "description": "Deterministic mock predictor for pipeline validation"
        }

    def predict(self, context) -> Prediction:
        """context: object with .score, .severity, .passed, .station."""
        import time
        start = time.time()
        qc_score = getattr(context, 'score', 0.5) if context else 0.5
        qc_passed = getattr(context, 'passed', True) if context else True
        station = getattr(context, 'station', 'unknown') if context else 'unknown'
        qc_severity = getattr(context, 'severity', 'UNKNOWN') if context else 'UNKNOWN'

        if self.mode == "deterministic":
            if qc_score >= 0.5 and qc_passed:
                prob = 0.1 + 0.8 * qc_score
                expl = "QC passed; low anomaly probability"
            else:
                prob = 0.3 + 0.7 * (1 - qc_score)
                expl = "QC failed or low score; elevated anomaly probability"
        else:
            if qc_score >= 0.7 and qc_passed:
                prob = 0.1 + 0.8 * qc_score
                expl = "QC passed; low anomaly probability"
            else:
                prob = 0.3 + 0.7 * (1 - qc_score)
                expl = "QC failed or low score; elevated anomaly probability"

        prob = max(0.0, min(1.0, prob))
        confidence = min(0.9, qc_score) if qc_passed else min(0.8, 1 - qc_score)
        confidence = max(0.1, min(0.99, confidence))
        uncertainty = 1.0 - confidence
        ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        latency = (time.time() - start) * 1000

        pred = Prediction(
            probability=round(prob, 3),
            confidence=round(confidence, 3),
            uncertainty=round(uncertainty, 3),
            station=station,
            explanation=expl,
            model_version=self._version,
            model_name=self.get_name(),
            backend="mock",
            latency_ms=round(latency, 2),
            timestamp=ts,
            qc_version="sciqg-1.0",
            pipeline_version="laws-v2",
        )
        return pred


def create_predictor(mode="normal"):
    return MockPredictor(mode=mode)
