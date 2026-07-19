"""QCReport - Serializable audit artifact. Immutable. Versioned."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional
import os, json
from datetime import datetime, timezone


@dataclass
class QCReport:
    """Audit artifact. Serializable to JSON. Immutable after creation.
    Never overwrite — always create new version."""
    artifact_uuid: str = ""
    station: str = ""
    utc: str = ""
    score: float = 1.0
    severity: str = "NONE"
    passed: bool = True
    failed_rules: list = field(default_factory=list)
    rule_results: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    pipeline_version: str = ""
    qg_version: str = "2.0"
    schema_version: str = "1.0"
    rule_set_version: str = "1.0"
    timestamp: str = ""
    execution_time_ms: float = 0.0
    action_taken: str = ""
    warnings: list = field(default_factory=list)
    decision_source: str = "default"  # e.g., policy name

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    @classmethod
    def from_qc_result(cls, qc_result, artifact_uuid="", station="", utc="",
                        pipeline_version="", action_taken="", schema_version="1.0",
                        rule_set_version="", decision_source="default"):
        rr_dict = {}
        for name, rr in qc_result.rule_results.items():
            rr_dict[name] = asdict(rr) if hasattr(rr, '__dataclass_fields__') else (rr.__dict__ if hasattr(rr, '__dict__') else rr)
        return cls(
            artifact_uuid=artifact_uuid,
            station=station,
            utc=utc,
            score=qc_result.score,
            severity=qc_result.severity,
            passed=qc_result.passed,
            failed_rules=list(qc_result.failed_rules),
            rule_results=rr_dict,
            metrics=dict(qc_result.metrics),
            pipeline_version=pipeline_version,
            execution_time_ms=qc_result.execution_time_ms,
            action_taken=action_taken,
            warnings=list(qc_result.warnings),
            schema_version=schema_version,
            rule_set_version=rule_set_version or "1.0",
            decision_source=decision_source,
        )

    def to_dict(self):
        return asdict(self)

    def save_json(self, path, immutable=True):
        """Save report. If immutable, append version suffix to avoid overwrite."""
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        if immutable and os.path.exists(path):
            base, ext = os.path.splitext(path)
            v = 1
            while os.path.exists("%s_v%d%s" % (base, v, ext)):
                v += 1
            path = "%s_v%d%s" % (base, v, ext)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
        return path

    @classmethod
    def load_json(cls, path):
        with open(path, "r", encoding="utf-8") as f:
            return cls(**json.load(f))

    def summary(self):
        return "QCReport(%s, score=%.3f, severity=%s, action=%s, schema=%s)" % (
            self.artifact_uuid[:8], self.score, self.severity, self.action_taken, self.schema_version)
