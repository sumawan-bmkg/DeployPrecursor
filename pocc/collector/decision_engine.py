#!/usr/bin/env python3
"""
decision_engine.py — Rule-based Decision Engine for earthquake precursor warnings.

Combines: Prediction + QCResult + station context → Decision.
All decisions are auditable. No black-box.
"""
import json, os, time, logging, hashlib
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional
from pathlib import Path

log = logging.getLogger("decision_engine")


class DecisionLevel(str, Enum):
    CLEAR = "CLEAR"
    WATCH = "WATCH"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class Decision:
    level: str
    probability: float
    confidence: float
    uncertainty: float
    qc_score: float
    station: str
    triggered_rules: list
    explanation: str
    timestamp: str
    prediction_uuid: str = ""
    decision_uuid: str = ""
    event_id: str = ""

    def __post_init__(self):
        if not self.decision_uuid:
            raw = f"{self.station}{self.level}{self.timestamp}"
            self.decision_uuid = hashlib.md5(raw.encode()).hexdigest()[:12]


@dataclass
class DecisionRule:
    name: str
    description: str
    weight: float = 1.0

    def evaluate(self, prediction, qc_score, context=None) -> tuple:
        """Returns (passed: bool, score: float, detail: str)"""
        raise NotImplementedError


class ProbabilityThreshold(DecisionRule):
    """Core rule: P(anomaly) must exceed threshold."""
    def __init__(self, watch=0.40, warning=0.70, critical=0.90):
        super().__init__("probability_threshold", "Detection probability exceeds threshold")
        self.watch = watch
        self.warning = warning
        self.critical = critical

    def evaluate(self, prediction, qc_score, ctx=None):
        p = prediction.probability if hasattr(prediction, 'probability') else prediction.get('probability', 0)
        if p >= self.critical:
            return True, p, f"P={p:.4f} >= {self.critical} → CRITICAL"
        if p >= self.warning:
            return True, p, f"P={p:.4f} >= {self.warning} → WARNING"
        if p >= self.watch:
            return True, p, f"P={p:.4f} >= {self.watch} → WATCH"
        return False, p, f"P={p:.4f} < {self.watch} → CLEAR"


class QCConsistency(DecisionRule):
    """QC score must agree with prediction."""
    def __init__(self, min_score=0.50):
        super().__init__("qc_consistency", "ScientificQG score validates data quality")
        self.min_score = min_score

    def evaluate(self, prediction, qc_score, ctx=None):
        passed = qc_score >= self.min_score
        return passed, qc_score, f"QC={qc_score:.2f} {'≥' if passed else '<'} {self.min_score}"


class UncertaintyGate(DecisionRule):
    """Uncertainty must be below threshold."""
    def __init__(self, max_uncertainty=0.50):
        super().__init__("uncertainty_gate", "Model uncertainty below threshold")
        self.max = max_uncertainty

    def evaluate(self, prediction, qc_score, ctx=None):
        u = prediction.uncertainty if hasattr(prediction, 'uncertainty') else prediction.get('uncertainty', 1.0)
        passed = u <= self.max
        return passed, u, f"U={u:.4f} {'≤' if passed else '>'} {self.max}"


class StormGate(DecisionRule):
    """Suppress warnings during geomagnetic storms."""
    def __init__(self):
        super().__init__("storm_gate", "Suppress warnings during geomagnetic storms (Kp>4)")

    def evaluate(self, prediction, qc_score, ctx=None):
        kp = getattr(ctx, 'kp', 0) if ctx else (ctx.get('kp', 0) if isinstance(ctx, dict) else 0)
        if kp > 4.0:
            return False, kp, f"Kp={kp:.1f} > 4.0 → storm mode, suppressed"
        return True, kp, f"Kp={kp:.1f} ≤ 4.0 → clear"


class DecisionEngine:
    """
    Rule-based decision engine.

    Evaluates all rules, computes final decision level.
    Rules are additive: each rule adds to the weighted score.
    """
    def __init__(self, audit_dir: str = None):
        self.rules = [
            ProbabilityThreshold(watch=0.40, warning=0.70, critical=0.90),
            QCConsistency(min_score=0.50),
            UncertaintyGate(max_uncertainty=0.50),
            StormGate(),
        ]
        self.audit_dir = audit_dir or "/opt/pimes/laws/runtime/validation/pdac/decisions"
        os.makedirs(self.audit_dir, exist_ok=True)

    def evaluate(self, prediction, qc_score: float = 0.5, context=None) -> Decision:
        ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        triggered = []
        scores = []

        for rule in self.rules:
            passed, score, detail = rule.evaluate(prediction, qc_score, context)
            scores.append(score if passed else -score * 0.5)
            triggered.append({
                "rule": rule.name,
                "passed": passed,
                "score": round(score, 4),
                "detail": detail,
            })
            log.info("Rule %s: %s — %s", rule.name, "PASS" if passed else "FAIL", detail)

        # Determine level
        prob = prediction.probability if hasattr(prediction, 'probability') else prediction.get('probability', 0)
        uncertainty = prediction.uncertainty if hasattr(prediction, 'uncertainty') else prediction.get('uncertainty', 1)
        station = prediction.station if hasattr(prediction, 'station') else "unknown"
        puuid = prediction.prediction_uuid if hasattr(prediction, 'prediction_uuid') else ""

        # All must pass for elevated decision
        all_pass = all(t["passed"] for t in triggered)

        if not all_pass:
            level = DecisionLevel.CLEAR
        elif prob >= 0.90:
            level = DecisionLevel.CRITICAL
        elif prob >= 0.70:
            level = DecisionLevel.WARNING
        elif prob >= 0.40:
            level = DecisionLevel.WATCH
        else:
            level = DecisionLevel.CLEAR

        explanation = "; ".join(t["detail"] for t in triggered if not t["passed"]) or "All rules passed"

        decision = Decision(
            level=level.value,
            probability=round(prob, 4),
            confidence=round(1 - uncertainty, 4),
            uncertainty=round(uncertainty, 4),
            qc_score=round(qc_score, 4),
            station=station,
            triggered_rules=triggered,
            explanation=explanation,
            timestamp=ts,
            prediction_uuid=puuid,
        )

        # Audit
        self._audit(decision)
        return decision

    def _audit(self, decision: Decision):
        fp = os.path.join(self.audit_dir, f"decision_{decision.station}_{decision.decision_uuid}.json")
        with open(fp, "w") as f:
            json.dump(asdict(decision), f, indent=2)
        log.info("Decision %s: %s for %s", decision.decision_uuid, decision.level, decision.station)

    def list_decisions(self, station: str = "", limit: int = 50) -> list:
        import glob
        pattern = os.path.join(self.audit_dir, f"decision_{station}_*.json") if station else os.path.join(self.audit_dir, "decision_*.json")
        files = sorted(glob.glob(pattern))[-limit:]
        results = []
        for fp in files:
            with open(fp) as f:
                results.append(json.load(f))
        return results
