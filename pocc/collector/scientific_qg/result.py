"""QCResult - Standard QC result contract. Permanent."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class RuleResult:
    """Per-rule evaluation result."""
    name: str = ""
    passed: bool = True
    score: float = 1.0
    metric: Optional[str] = None
    value: Any = None
    execution_time_ms: float = 0.0
    priority: str = "NORMAL"
    weight: float = 1.0
    category: str = "general"
    version: str = "1.0"


@dataclass
class QCResult:
    """Standard QC evaluation result. Permanent contract. Do not modify."""
    passed: bool = True
    score: float = 1.0
    severity: str = "NONE"
    failed_rules: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    warnings: List[str] = field(default_factory=list)
    rule_results: Dict[str, RuleResult] = field(default_factory=dict)

    def summary(self) -> str:
        if self.passed: return "PASSED (score=%.3f, severity=%s, %.1fms)" % (self.score, self.severity, self.execution_time_ms)
        return "FAILED (score=%.3f, severity=%s, rules=%s, %.1fms)" % (self.score, self.severity, self.failed_rules, self.execution_time_ms)

    @classmethod
    def excellent(cls, metrics=None, ms=0):
        return cls(passed=True, score=1.0, severity="EXCELLENT", metrics=metrics or {}, execution_time_ms=ms)

    @classmethod
    def failed(cls, rules, metrics=None, ms=0, warnings=None, rule_results=None):
        score = max(0.0, 1.0 - len(rules) * 0.15)
        severity = score_to_severity(score)
        return cls(passed=score >= 0.40, score=round(score, 3), severity=severity,
                   failed_rules=rules, metrics=metrics or {}, execution_time_ms=ms,
                   warnings=warnings or [], rule_results=rule_results or {})


def score_to_severity(score):
    if score >= 0.90: return "EXCELLENT"
    if score >= 0.75: return "GOOD"
    if score >= 0.60: return "ACCEPTABLE"
    if score >= 0.40: return "SUSPICIOUS"
    return "CORRUPTED"


def score_action(severity):
    return {
        "EXCELLENT": "proceed", "GOOD": "proceed", "ACCEPTABLE": "proceed_with_warning",
        "SUSPICIOUS": "quarantine_review", "CORRUPTED": "quarantine",
    }.get(severity, "quarantine")
