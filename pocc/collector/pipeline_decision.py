"""PipelineDecision - Explicit decision contract for pipeline flow."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import os, json
from datetime import datetime, timezone


class Action(Enum):
    PROCEED = "PROCEED"
    QUARANTINE = "QUARANTINE"
    RETRY = "RETRY"
    REVIEW = "REVIEW"
    SKIP = "SKIP"
    DOWNGRADE = "DOWNGRADE"
    CANCEL = "CANCEL"


@dataclass
class PipelineDecision:
    """Immutable decision contract. Serializable."""
    action: str = "PROCEED"
    reason: str = ""
    qc_score: float = 1.0
    qc_severity: str = "NONE"
    artifact_id: str = ""
    timestamp: str = ""
    decision_source: str = "default"
    policy_name: str = "default"

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def is_quarantine(self):
        return self.action == Action.QUARANTINE.value

    def is_proceed(self):
        return self.action == Action.PROCEED.value

    def to_dict(self):
        return {
            "action": self.action,
            "reason": self.reason,
            "qc_score": self.qc_score,
            "qc_severity": self.qc_severity,
            "artifact_id": self.artifact_id,
            "timestamp": self.timestamp,
            "decision_source": self.decision_source,
            "policy_name": self.policy_name,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    def save_json(self, path):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    @classmethod
    def load_json(cls, path):
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))
