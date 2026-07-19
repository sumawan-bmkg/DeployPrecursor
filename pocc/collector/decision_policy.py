"""DecisionPolicy - Configurable decision thresholds. YAML/JSON."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional
from pipeline_decision import Action


DEFAULT_POLICY = {
    "EXCELLENT": {"action": "PROCEED", "min_score": 0.90},
    "GOOD":      {"action": "PROCEED", "min_score": 0.75},
    "ACCEPTABLE": {"action": "PROCEED", "min_score": 0.60},
    "SUSPICIOUS": {"action": "QUARANTINE", "min_score": 0.40},
    "CORRUPTED":  {"action": "QUARANTINE", "min_score": 0.0},
}


@dataclass
class DecisionPolicy:
    """Configurable decision policy. Serialize to/from dict/YAML/JSON."""
    name: str = "default"
    severity_map: Dict[str, str] = field(default_factory=lambda: {
        k: v["action"] for k, v in DEFAULT_POLICY.items()
    })
    score_thresholds: Dict[str, float] = field(default_factory=lambda: {
        k: v["min_score"] for k, v in DEFAULT_POLICY.items()
    })

    @classmethod
    def from_dict(cls, d):
        if "severity_map" not in d and "name" not in d:
            d = {"name": d.get("name", "custom"), "severity_map": d.get("severity_map", {}),
                 "score_thresholds": d.get("score_thresholds", {})}
        return cls(
            name=d.get("name", "custom"),
            severity_map={k.upper(): v for k, v in d.get("severity_map", DEFAULT_POLICY_DICT).items()},
            score_thresholds={k.upper(): float(v) for k, v in d.get("score_thresholds", DEFAULT_SCORE_DICT).items()},
        )

    def decide(self, severity: str, score: float) -> str:
        severity = severity.upper()
        action = self.severity_map.get(severity, "QUARANTINE")
        # Verify score meets threshold for severity
        min_score = self.score_thresholds.get(severity, 0.0)
        if score < min_score:
            # Fall down to next severity
            for sev in ["EXCELLENT", "GOOD", "ACCEPTABLE", "SUSPICIOUS", "CORRUPTED"]:
                if score >= self.score_thresholds.get(sev, 0.0):
                    return self.severity_map.get(sev, "QUARANTINE")
        return action

    def to_dict(self):
        return {"name": self.name, "severity_map": dict(self.severity_map),
                "score_thresholds": dict(self.score_thresholds)}


DEFAULT_POLICY_DICT = {k: v["action"] for k, v in DEFAULT_POLICY.items()}
DEFAULT_SCORE_DICT = {k: v["min_score"] for k, v in DEFAULT_POLICY.items()}
DEFAULT_DECISION_POLICY = DecisionPolicy()
