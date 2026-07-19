"""QuarantineManager - Executes quarantine decisions. No QC logic."""
from __future__ import annotations
import logging, shutil
from pathlib import Path
from lifecycle_registry import (
    LifecycleRegistry, ArtifactState, StorageClass, EventCategory,
)
from pipeline_decision import PipelineDecision

log = logging.getLogger("quarantine_manager")


class QuarantineManager:
    """Receives PipelineDecision, executes quarantine. No validation logic."""

    QUARANTINE_ROOT = "/opt/pimes/runtime/cache/quarantine"

    def __init__(self, registry=None, quarantine_root=""):
        self.registry = registry or LifecycleRegistry()
        self.quarantine_root = Path(quarantine_root or self.QUARANTINE_ROOT)
        self.quarantine_root.mkdir(parents=True, exist_ok=True)

    def execute(self, decision: PipelineDecision, artifact_id: str, file_path: str = ""):
        """Execute quarantine action from decision. No QC computation."""
        if not decision.is_quarantine():
            log.info("Non-quarantine action: %s for %s", decision.action, artifact_id)
            return {"executed": False, "reason": "not_quarantine", "decision": decision.action}

        # 1. Verify artifact exists
        rec = self.registry.get_record(artifact_id)
        if not rec:
            log.warning("Quarantine: artifact %s not found in registry", artifact_id)
            return {"executed": False, "reason": "not_in_registry"}

        state = self.registry.get_state(artifact_id)
        terminal = {ArtifactState.PURGED, ArtifactState.QUARANTINED, ArtifactState.CANCELLED,
                    ArtifactState.EXPIRED, ArtifactState.ARCHIVED}
        if state in terminal:
            log.info("Quarantine: %s already terminal (%s)", artifact_id, state.value)
            return {"executed": False, "reason": "already_terminal", "state": state.value}

        # 2. Transition through DOWNLOADED if still NEW
        if state == ArtifactState.NEW:
            self.registry.transition(artifact_id, ArtifactState.DOWNLOADED,
                                     worker="quarantine_manager", reason="pre-quarantine")

        # 3. Move file to quarantine directory if it exists
        src = rec.file_path
        if src and Path(src).exists():
            station = rec.station
            reason_dir = decision.reason.replace(" ", "_").replace("/", "_")[:50]
            dst_dir = self.quarantine_root / reason_dir / station
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst = dst_dir / rec.filename
            shutil.move(src, str(dst))
            self.registry.set_file_path(artifact_id, str(dst))
            log.info("Quarantine: moved %s -> %s", src, dst)

        # 4. Transition to QUARANTINED
        self.registry.transition(
            artifact_id, ArtifactState.QUARANTINED,
            worker="quarantine_manager",
            reason="%s: %s" % (decision.action, decision.reason),
            category=EventCategory.ERROR,
        )

        # 5. Set storage class
        self.registry.set_storage_class(artifact_id, StorageClass.QUARANTINED)

        # 6. Update metadata
        self.registry.update_metadata(
            artifact_id,
            quarantine_action=decision.action,
            quarantine_reason=decision.reason,
            quarantine_score=decision.qc_score,
            quarantine_severity=decision.qc_severity,
            quarantine_timestamp=decision.timestamp,
        )

        log.info("Quarantined %s: %s (score=%.3f)", artifact_id, decision.reason, decision.qc_score)
        return {
            "executed": True,
            "artifact_id": artifact_id,
            "state": ArtifactState.QUARANTINED.value,
            "storage_class": StorageClass.QUARANTINED.value,
            "file_path": rec.file_path,
        }

    def is_quarantined(self, artifact_id):
        rec = self.registry.get_record(artifact_id)
        return rec and rec.state == ArtifactState.QUARANTINED.value
