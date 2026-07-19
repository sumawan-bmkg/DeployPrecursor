"""Predictor interface: abstract base + Prediction object for LAWS V2."""
from __future__ import annotations
import abc
import time
import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass(frozen=True)
class Prediction:
    """Immutable prediction output. All predictors must return this."""
    probability: float = 0.0
    confidence: float = 0.0
    uncertainty: float = 0.0
    magnitude: Optional[float] = None
    azimuth: Optional[float] = None
    explanation: str = ""
    model_version: str = ""
    model_name: str = ""
    backend: str = ""
    latency_ms: float = 0.0
    station: str = ""
    artifact_uuid: str = ""
    pipeline_version: str = ""
    qc_version: str = ""
    prediction_uuid: str = ""
    input_hash: str = ""
    prediction_hash: str = ""
    timestamp: str = ""

    def __post_init__(self):
        # Auto-compute hashes if not provided
        import time, hashlib
        if not self.prediction_uuid:
            object.__setattr__(self, 'prediction_uuid', hashlib.md5(f"{self.station}{self.timestamp}{time.time_ns()}".encode()).hexdigest()[:16])
        if not self.prediction_hash:
            raw = f"{self.station}{self.probability}{self.confidence}{self.model_version}{self.timestamp}"
            object.__setattr__(self, 'prediction_hash', hashlib.sha256(raw.encode()).hexdigest()[:16])

    def to_dict(self) -> dict:
        d = {}
        for k, v in asdict(self).items():
            d[k] = v
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def compute_hash(self) -> str:
        raw = f"{self.station}{self.probability}{self.confidence}{self.model_version}{self.timestamp}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


class PredictorInterface(abc.ABC):
    """Abstract predictor. All predictors (mock, LAWS, ONNX, remote) implement this."""

    @abc.abstractmethod
    def predict(self, context) -> Prediction:
        ...

    @abc.abstractmethod
    def get_model_info(self) -> dict:
        ...

    @abc.abstractmethod
    def get_name(self) -> str:
        ...


class PredictionAudit:
    """Audit log for prediction reproducibility."""

    def __init__(self, audit_dir: str):
        self.audit_dir = audit_dir
        import os
        os.makedirs(audit_dir, exist_ok=True)

    def log(self, prediction: Prediction, qc_score: float = 0.0, input_hash: str = ""):
        import os
        entry = {
            "prediction_uuid": prediction.prediction_uuid,
            "artifact_uuid": prediction.artifact_uuid,
            "station": prediction.station,
            "timestamp": prediction.timestamp,
            "model_name": prediction.model_name,
            "model_version": prediction.model_version,
            "backend": prediction.backend,
            "prediction_hash": prediction.prediction_hash,
            "input_hash": input_hash or prediction.input_hash,
            "qc_score": qc_score,
            "qc_version": prediction.qc_version,
            "pipeline_version": prediction.pipeline_version,
            "prediction": prediction.probability,
            "uncertainty": prediction.uncertainty,
            "latency_ms": prediction.latency_ms,
        }
        ts = prediction.timestamp.replace(":", "-")
        fp = os.path.join(self.audit_dir, f"audit_{prediction.station}_{ts}.json")
        with open(fp, "w") as f:
            json.dump(entry, f, indent=2)
        return fp

    def query(self, station: str = "", limit: int = 100) -> list:
        import os, glob
        if station:
            pattern = os.path.join(self.audit_dir, f"audit_{station}_*.json")
        else:
            pattern = os.path.join(self.audit_dir, "audit_*.json")
        files = sorted(glob.glob(pattern))[-limit:]
        results = []
        for fp in files:
            with open(fp) as f:
                results.append(json.load(f))
        return results
