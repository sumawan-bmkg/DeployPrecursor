"""LAWS Adapter stub (P6B+P6C) — PredictorInterface implementation."""
from predictor_base import PredictorInterface, Prediction


class LAWSPredictor(PredictorInterface):
    """Adapter for LAWS V2 model. Currently a stub returning zero predictions."""

    def __init__(self, model_path: str = "", mode: str = "standard"):
        self.model_path = model_path
        self.mode = mode
        self._version = "laws-v2-adapter-0.1"

    def get_name(self) -> str:
        return "LAWSV2Adapter"

    def get_model_info(self) -> dict:
        return {
            "model_name": self.get_name(),
            "version": self._version,
            "mode": self.mode,
            "model_path": self.model_path,
            "status": "stub — replace with real ModelLoader",
        }

    def predict(self, context) -> Prediction:
        import time
        station = getattr(context, 'station', 'unknown') if context else 'unknown'

        return Prediction(
            probability=0.0,
            confidence=0.0,
            uncertainty=1.0,
            station=station,
            explanation="LAWS adapter stub — no real model loaded",
            model_version=self._version,
            model_name=self.get_name(),
            backend="laws-stub",
            latency_ms=0.0,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            qc_version="sciqg-1.0",
            pipeline_version="laws-v2",
        )


class EnsemblePredictor(PredictorInterface):
    """Runs multiple predictors and combines via weighted average."""

    def __init__(self, predictors: list[PredictorInterface], weights: list[float] | None = None):
        if not predictors:
            raise ValueError("Need at least one predictor")
        self.predictors = predictors
        self.weights = weights or [1.0] * len(predictors)
        total = sum(self.weights)
        self.weights = [w / total * len(predictors) for w in self.weights]

    def get_name(self) -> str:
        return "Ensemble+" + "+".join(p.get_name() for p in self.predictors)

    def get_model_info(self) -> dict:
        return {
            "model_name": self.get_name(),
            "n_predictors": len(self.predictors),
            "weights": self.weights,
        }

    def predict(self, context) -> Prediction:
        import time
        results = [p.predict(context) for p in self.predictors]
        prob = sum(w * r.probability for w, r in zip(self.weights, results)) / len(self.predictors)
        base = results[0]
        return Prediction(
            probability=round(prob, 3),
            confidence=base.confidence,
            uncertainty=base.uncertainty,
            magnitude=base.magnitude,
            azimuth=base.azimuth,
            station=base.station,
            explanation=f"Ensemble of {len(self.predictors)} predictors",
            model_version=f"ensemble-v1-{len(self.predictors)}predictors",
            model_name=self.get_name(),
            backend="ensemble",
            latency_ms=base.latency_ms,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            qc_version="sciqg-1.0",
            pipeline_version="laws-v2",
        )
