"""QCOrchestrator - Coordinates QC evaluation, registry, quarantine, metrics, events."""
from __future__ import annotations
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from lifecycle_registry import (
    LifecycleRegistry, ArtifactState, StorageClass, EventCategory,
)
from scientific_qg import ScientificQG, QCResult, QCConfig
from decision_policy import DecisionPolicy, DEFAULT_DECISION_POLICY
from pipeline_decision import PipelineDecision, Action
from quarantine_manager import QuarantineManager
from qc_report import QCReport
from event_bus import EventBus, EventType
from operation_metrics import OperationMetrics

log = logging.getLogger("qc_orchestrator")


class QCOrchestrator:
    """Single coordinator for QC evaluation pipeline."""

    def __init__(self, registry=None, qg_config=None, quarantine_root="",
                 policy=None, event_bus=None, metrics=None):
        self.registry = registry or LifecycleRegistry()
        self.qg = ScientificQG(config=qg_config)
        self.quarantine = QuarantineManager(registry=self.registry, quarantine_root=quarantine_root)
        self.policy = policy or DEFAULT_DECISION_POLICY
        self.event_bus = event_bus or EventBus()
        self.metrics = metrics or OperationMetrics()

    def evaluate_and_decide(self, artifact_id, H, D, Z,
                            metadata=None, station="", utc="",
                            sampling_rate=1.0, pipeline_version="",
                            kp=None, dst=None):
        """Full orchestrator flow: evaluate -> decide -> act -> report."""
        t0 = datetime.now(timezone.utc)

        # 1. ScientificQG evaluation (pure)
        qc_result = self.qg.evaluate(
            H=H, D=D, Z=Z, metadata=metadata, station=station,
            utc=utc, sampling_rate=sampling_rate,
            pipeline_version=pipeline_version, kp=kp, dst=dst,
        )

        # 2. Decide via policy
        action = self.policy.decide(qc_result.severity, qc_result.score)
        decision = PipelineDecision(
            action=action,
            reason=self._format_reason(qc_result),
            qc_score=qc_result.score,
            qc_severity=qc_result.severity,
            artifact_id=artifact_id,
            decision_source=self.policy.name,
            policy_name=self.policy.name,
        )

        # Emit QC_COMPLETED
        self.event_bus.emit(EventType.QC_COMPLETED, {
            "artifact_id": artifact_id, "score": qc_result.score,
            "severity": qc_result.severity, "action": action,
        })

        # 3. Registry update (if artifact exists)
        rec = self.registry.get_record(artifact_id) if artifact_id else None
        if rec:
            self.registry.update_metadata(
                artifact_id,
                qc_score=qc_result.score,
                qc_severity=qc_result.severity,
                qc_action=decision.action,
                qc_timestamp=decision.timestamp,
                qc_metrics=qc_result.metrics,
                qc_policy=self.policy.name,
            )
            self.registry.add_event(
                artifact_id, EventCategory.INFO,
                "QC: score=%.3f severity=%s action=%s" % (
                    qc_result.score, qc_result.severity, decision.action),
                worker="qc_orchestrator",
            )

        # 4. Execute quarantine if needed
        quarantine_result = None
        quarantined = False
        if decision.is_quarantine():
            file_path = rec.file_path if rec else ""
            quarantine_result = self.quarantine.execute(
                decision, artifact_id=artifact_id, file_path=file_path,
            )
            if quarantine_result and quarantine_result.get("executed"):
                quarantined = True
                self.event_bus.emit(EventType.ARTIFACT_QUARANTINED, {
                    "artifact_id": artifact_id, "reason": decision.reason,
                    "score": qc_result.score,
                })
            else:
                decision.action = Action.PROCEED.value
                decision.reason += " (quarantine failed: %s)" % quarantine_result.get("reason", "unknown")

        # 5. QCReport
        report = QCReport.from_qc_result(
            qc_result,
            artifact_uuid=artifact_id,
            station=station,
            utc=utc,
            pipeline_version=pipeline_version,
            action_taken=decision.action,
            rule_set_version=self._rule_set_version(),
            decision_source=self.policy.name,
        )

        # 6. Emit accept/retry/review events
        if decision.action == Action.PROCEED.value:
            self.event_bus.emit(EventType.ARTIFACT_ACCEPTED, {
                "artifact_id": artifact_id, "score": qc_result.score,
            })
        elif decision.action == Action.RETRY.value:
            self.event_bus.emit(EventType.ARTIFACT_RETRY, {
                "artifact_id": artifact_id, "score": qc_result.score,
            })
        elif decision.action == Action.REVIEW.value:
            self.event_bus.emit(EventType.ARTIFACT_REVIEW, {
                "artifact_id": artifact_id, "score": qc_result.score,
            })

        # 7. Update metrics
        elapsed = (datetime.now(timezone.utc) - t0).total_seconds() * 1000
        self.metrics.record(
            passed=qc_result.passed,
            duration_ms=elapsed,
            score=qc_result.score,
            rule_fails=len(qc_result.failed_rules),
            quarantined=quarantined,
        )

        log.info("Orchestrator: %s -> %s (score=%.3f, %.1fms)",
                 artifact_id[:8], decision.action, qc_result.score, elapsed)

        return {
            "decision": decision,
            "qc_result": qc_result,
            "report": report,
            "quarantine": quarantine_result,
        }

    def evaluate_only(self, H, D, Z, **kwargs):
        """Pure evaluation without side effects."""
        qc_result = self.qg.evaluate(H=H, D=D, Z=Z, **kwargs)
        action = self.policy.decide(qc_result.severity, qc_result.score)
        decision = PipelineDecision(
            action=action, reason=self._format_reason(qc_result),
            qc_score=qc_result.score, qc_severity=qc_result.severity,
            decision_source=self.policy.name, policy_name=self.policy.name,
        )
        # Emit evaluated event (no side effects)
        self.event_bus.emit(EventType.QC_EVALUATED, {
            "score": qc_result.score,
            "severity": qc_result.severity,
            "action": action,
        })
        return qc_result, decision

    def get_metrics(self):
        return self.metrics.snapshot()

    def _rule_set_version(self):
        names = sorted(r.name for r in self.qg.rules)
        return "v1-%d" % len(names)

    def _format_reason(self, qc_result):
        if qc_result.passed:
            return "QC passed (score=%.3f)" % qc_result.score
        return "Failed rules: %s (score=%.3f)" % (
            ", ".join(qc_result.failed_rules), qc_result.score)
