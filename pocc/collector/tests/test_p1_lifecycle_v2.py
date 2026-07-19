#!/usr/bin/env python3
"""
LAWS V2 — P1 Test Suite.

Tests lifecycle_registry.py and artifact_manager.py.

Run:
    cd /opt/pimes/pocc
    python -m pytest tests/test_p1_lifecycle_v2.py -v

Or standalone:
    python collector/tests/test_p1_lifecycle_v2.py
"""

import json
import os
import sys
import tempfile
import uuid
from pathlib import Path

# Allow standalone execution
_POC_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_POC_ROOT / "collector"))

from lifecycle_registry import (
    LifecycleRegistry, ArtifactState, validate_transition,
    TransitionEvent, ArtifactRecord, _ALLOWED
)


class TestEnumStates:
    """All states use Enum — not strings."""

    def test_all_states_are_enums(self):
        for state in ArtifactState:
            assert isinstance(state, ArtifactState)
            assert isinstance(state.value, str)

    def test_state_string_representation(self):
        assert str(ArtifactState.NEW) == "NEW"
        assert str(ArtifactState.DOWNLOADED) == "DOWNLOADED"
        assert str(ArtifactState.QUARANTINE) == "QUARANTINE"

    def test_all_expected_states_present(self):
        expected = {
            "NEW", "DOWNLOADED", "VALIDATED", "PARSED",
            "HDF5_CREATED", "VERIFIED", "INFERENCE_DONE",
            "PURGED", "QUARANTINE"
        }
        actual = {s.value for s in ArtifactState}
        assert actual == expected

    def test_state_count(self):
        assert len(ArtifactState) == 9


class TestTransitionValidator:
    """State machine validation rules."""

    def test_happy_path_allowed(self):
        """Full pipeline: NEW → DOWNLOADED → VALIDATED → PARSED → HDF5_CREATED → VERIFIED → INFERENCE_DONE → PURGED."""
        steps = [
            ArtifactState.NEW, ArtifactState.DOWNLOADED,
            ArtifactState.VALIDATED, ArtifactState.PARSED,
            ArtifactState.HDF5_CREATED, ArtifactState.VERIFIED,
            ArtifactState.INFERENCE_DONE, ArtifactState.PURGED,
        ]
        for a, b in zip(steps, steps[1:]):
            assert validate_transition(a, b), f"{a} → {b} should be allowed"

    def test_quarantine_from_processing_states(self):
        """QUARANTINE is reachable from all non-terminal states."""
        quarantinable = [
            ArtifactState.DOWNLOADED, ArtifactState.VALIDATED,
            ArtifactState.PARSED, ArtifactState.HDF5_CREATED,
            ArtifactState.VERIFIED, ArtifactState.INFERENCE_DONE,
        ]
        for state in quarantinable:
            assert validate_transition(state, ArtifactState.QUARANTINE), \
                f"{state} → QUARANTINE should be allowed"

    def test_quarantine_from_new_rejected(self):
        """NEW → QUARANTINE is not allowed (no work done yet)."""
        assert not validate_transition(ArtifactState.NEW, ArtifactState.QUARANTINE)

    def test_new_to_purged_rejected(self):
        """NEW → PURGED must fail — skipping entire pipeline."""
        assert not validate_transition(ArtifactState.NEW, ArtifactState.PURGED)

    def test_parsed_to_new_rejected(self):
        """PARSED → NEW is going backwards."""
        assert not validate_transition(ArtifactState.PARSED, ArtifactState.NEW)

    def test_hdf5_created_to_downloaded_rejected(self):
        """HDF5_CREATED → DOWNLOADED — cannot go back to download stage."""
        assert not validate_transition(ArtifactState.HDF5_CREATED, ArtifactState.DOWNLOADED)

    def test_purged_has_no_transitions(self):
        """PURGED is terminal — no outgoing transitions."""
        assert validate_transition(ArtifactState.PURGED, ArtifactState.PURGED) is False
        for target in ArtifactState:
            if target != ArtifactState.PURGED:
                assert not validate_transition(ArtifactState.PURGED, target), \
                    f"PURGED → {target} should be rejected"

    def test_quarantine_has_no_transitions(self):
        """QUARANTINE is terminal — no outgoing transitions."""
        for target in ArtifactState:
            if target != ArtifactState.QUARANTINE:
                assert not validate_transition(ArtifactState.QUARANTINE, target), \
                    f"QUARANTINE → {target} should be rejected"

    def test_inference_done_to_purged_only(self):
        """INFERENCE_DONE only transitions to PURGED or QUARANTINE."""
        allowed = {ArtifactState.PURGED, ArtifactState.QUARANTINE}
        assert _ALLOWED[ArtifactState.INFERENCE_DONE] == allowed

    def test_downloaded_can_go_to_validated_or_quarantine(self):
        """DOWNLOADED → VALIDATED or QUARANTINE (never skip to PARSED)."""
        allowed = {ArtifactState.VALIDATED, ArtifactState.QUARANTINE}
        assert _ALLOWED[ArtifactState.DOWNLOADED] == allowed

    def test_no_skip_to_inference(self):
        """Cannot skip from DOWNLOADED directly to INFERENCE_DONE."""
        assert not validate_transition(ArtifactState.DOWNLOADED, ArtifactState.INFERENCE_DONE)


class TestRegistryTransitions:
    """Full lifecycle test through registry transitions."""

    def _make_registry(self, tmp):
        path = os.path.join(tmp, "test_registry.json")
        return LifecycleRegistry(path=path)

    def test_full_happy_path(self):
        """NEW → DOWNLOADED → VALIDATED → PARSED → HDF5_CREATED → VERIFIED → INFERENCE_DONE → PURGED."""
        with tempfile.TemporaryDirectory() as tmp:
            reg = self._make_registry(tmp)
            aid = reg.register("WAVEFORM", "ALR", "S260101.ALR")
            assert reg.get_state(aid) == ArtifactState.NEW

            for state in [ArtifactState.DOWNLOADED, ArtifactState.VALIDATED,
                          ArtifactState.PARSED, ArtifactState.HDF5_CREATED,
                          ArtifactState.VERIFIED, ArtifactState.INFERENCE_DONE,
                          ArtifactState.PURGED]:
                reg.transition(aid, state, worker="test", reason=f"→ {state.value}")
                assert reg.get_state(aid) == state

    def test_illegal_transition_rejected(self):
        """NEW → PURGED must raise ValueError."""
        with tempfile.TemporaryDirectory() as tmp:
            reg = self._make_registry(tmp)
            aid = reg.register("WAVEFORM", "ALR", "S260101.ALR")
            import pytest
            with pytest.raises(ValueError, match="Illegal transition"):
                reg.transition(aid, ArtifactState.PURGED, worker="test")

    def test_parsed_to_new_rejected(self):
        """PARSED → NEW must raise ValueError."""
        with tempfile.TemporaryDirectory() as tmp:
            reg = self._make_registry(tmp)
            aid = reg.register("WAVEFORM", "ALR", "S260101.ALR")
            reg.transition(aid, ArtifactState.DOWNLOADED)
            reg.transition(aid, ArtifactState.VALIDATED)
            reg.transition(aid, ArtifactState.PARSED)
            import pytest
            with pytest.raises(ValueError, match="Illegal transition"):
                reg.transition(aid, ArtifactState.NEW)

    def test_hdf5_to_downloaded_rejected(self):
        """HDF5_CREATED → DOWNLOADED must raise ValueError."""
        with tempfile.TemporaryDirectory() as tmp:
            reg = self._make_registry(tmp)
            aid = reg.register("WAVEFORM", "ALR", "S260101.ALR")
            for s in [ArtifactState.DOWNLOADED, ArtifactState.VALIDATED,
                      ArtifactState.PARSED, ArtifactState.HDF5_CREATED]:
                reg.transition(aid, s)
            import pytest
            with pytest.raises(ValueError, match="Illegal transition"):
                reg.transition(aid, ArtifactState.DOWNLOADED)

    def test_quarantine_is_terminal(self):
        """After QUARANTINE, no further transitions allowed."""
        with tempfile.TemporaryDirectory() as tmp:
            reg = self._make_registry(tmp)
            aid = reg.register("WAVEFORM", "ALR", "S260101.ALR")
            reg.transition(aid, ArtifactState.DOWNLOADED)
            reg.transition(aid, ArtifactState.QUARANTINE, reason="QC failed")
            assert reg.get_state(aid) == ArtifactState.QUARANTINE

            import pytest
            with pytest.raises(ValueError):
                reg.transition(aid, ArtifactState.VALIDATED)

    def test_event_log_recorded(self):
        """Each transition creates an event log entry."""
        with tempfile.TemporaryDirectory() as tmp:
            reg = self._make_registry(tmp)
            aid = reg.register("WAVEFORM", "ALR", "S260101.ALR")
            reg.transition(aid, ArtifactState.DOWNLOADED, worker="download")
            reg.transition(aid, ArtifactState.VALIDATED, worker="validator")

            events = reg.get_events(aid)
            # First event is registration, then 2 transitions
            assert len(events) >= 3

            # First real transition event
            dl_event = events[1]
            assert dl_event["from_state"] == "NEW"
            assert dl_event["to_state"] == "DOWNLOADED"
            assert dl_event["worker"] == "download"
            assert dl_event["timestamp"]

            val_event = events[2]
            assert val_event["from_state"] == "DOWNLOADED"
            assert val_event["to_state"] == "VALIDATED"
            assert val_event["worker"] == "validator"

    def test_event_log_includes_host_and_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = self._make_registry(tmp)
            aid = reg.register("WAVEFORM", "ALR", "S260101.ALR")
            reg.transition(aid, ArtifactState.DOWNLOADED,
                          worker="download", reason="checksum ok")
            events = reg.get_events(aid)
            ev = events[1]
            assert ev["worker"] == "download"
            assert ev["reason"] == "checksum ok"
            assert ev["host"]  # should be set

    def test_idempotent_transition(self):
        """Transition to same state is a no-op (idempotent)."""
        with tempfile.TemporaryDirectory() as tmp:
            reg = self._make_registry(tmp)
            aid = reg.register("WAVEFORM", "ALR", "S260101.ALR")
            reg.transition(aid, ArtifactState.DOWNLOADED)
            len_before = len(reg.get_events(aid))
            reg.transition(aid, ArtifactState.DOWNLOADED)  # no-op
            assert len(reg.get_events(aid)) == len_before
            assert reg.get_state(aid) == ArtifactState.DOWNLOADED


class TestDependencyGraph:
    """Dependency cascade: Waveform → HDF5 → Prediction → Alert."""

    def _make_registry(self, tmp):
        path = os.path.join(tmp, "test_registry.json")
        return LifecycleRegistry(path=path)

    def test_link_and_query_downstream(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = self._make_registry(tmp)
            wf = reg.register("WAVEFORM", "ALR", "S260101.ALR")
            h5 = reg.register("HDF5", "ALR", "S260101.h5")
            pred = reg.register("PREDICTION", "ALR", "S260101.json")

            reg.link(wf, h5)
            reg.link(h5, pred)

            downstream = reg.get_downstream(wf)
            assert len(downstream) == 1
            assert downstream[0].artifact_id == h5

            upstream = reg.get_upstream(h5)
            assert upstream.artifact_id == wf

    def test_cascade_quarantine(self):
        """When upstream quarantines, downstream quarantines too."""
        with tempfile.TemporaryDirectory() as tmp:
            reg = self._make_registry(tmp)
            wf = reg.register("WAVEFORM", "ALR", "S260101.ALR")
            h5 = reg.register("HDF5", "ALR", "S260101.h5")
            pred = reg.register("PREDICTION", "ALR", "S260101.json")

            reg.link(wf, h5)
            reg.link(h5, pred)

            reg.transition(wf, ArtifactState.DOWNLOADED)
            reg.transition(h5, ArtifactState.DOWNLOADED)
            reg.transition(pred, ArtifactState.DOWNLOADED)

            # Quarantine the waveform
            reg.transition(wf, ArtifactState.QUARANTINE, reason="binary corrupt")

            # Downstream must cascade to QUARANTINE
            assert reg.get_state(h5) == ArtifactState.QUARANTINE
            assert reg.get_state(pred) == ArtifactState.QUARANTINE

    def test_is_downstream_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = self._make_registry(tmp)
            wf = reg.register("WAVEFORM", "ALR", "S260101.ALR")
            h5 = reg.register("HDF5", "ALR", "S260101.h5")
            pred = reg.register("PREDICTION", "ALR", "S260101.json")

            reg.link(wf, h5)
            reg.link(h5, pred)

            # Move wf past NEW so it can go to QUARANTINE
            reg.transition(wf, ArtifactState.DOWNLOADED)

            assert reg.is_downstream_valid(pred) is True

            reg.transition(wf, ArtifactState.QUARANTINE, reason="fail")
            assert reg.is_downstream_valid(pred) is False


class TestCrashRecovery:
    """Verify registry survives crash and pending items are recoverable."""

    def _make_registry(self, tmp):
        path = os.path.join(tmp, "test_registry.json")
        return LifecycleRegistry(path=path)

    def test_get_pending_returns_unfinished(self):
        """Pending = not in terminal state (PURGED/QUARANTINE)."""
        with tempfile.TemporaryDirectory() as tmp:
            reg = self._make_registry(tmp)
            aid1 = reg.register("WAVEFORM", "ALR", "S260101.ALR")
            aid2 = reg.register("HDF5", "ALR", "S260101.h5")
            aid3 = reg.register("WAVEFORM", "SCN", "S260101.SCN")

            reg.transition(aid1, ArtifactState.DOWNLOADED)
            # HDF5 and WAVEFORM need DOWNLOADED first
            reg.transition(aid2, ArtifactState.DOWNLOADED)
            reg.transition(aid3, ArtifactState.DOWNLOADED)
            # Send SCN to QUARANTINE
            reg.transition(aid3, ArtifactState.QUARANTINE)

            pending = reg.get_pending()
            pending_ids = [p.artifact_id for p in pending]

            assert aid1 in pending_ids   # DOWNLOADED — still processing
            assert aid2 in pending_ids   # DOWNLOADED — still processing
            assert aid3 not in pending_ids  # QUARANTINE — terminal

    def test_get_pending_filtered_by_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = self._make_registry(tmp)
            aid1 = reg.register("WAVEFORM", "ALR", "S260101.ALR")
            aid2 = reg.register("HDF5", "ALR", "S260101.h5")
            reg.transition(aid1, ArtifactState.DOWNLOADED)
            reg.transition(aid2, ArtifactState.DOWNLOADED)

            pending_wf = reg.get_pending("WAVEFORM")
            pending_h5 = reg.get_pending("HDF5")
            assert len(pending_wf) == 1
            assert len(pending_h5) == 1

    def test_registry_persists_across_restart(self):
        """Save → load → state is preserved."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test_registry.json")
            reg1 = LifecycleRegistry(path=path)
            aid = reg1.register("WAVEFORM", "ALR", "S260101.ALR")
            reg1.transition(aid, ArtifactState.DOWNLOADED, worker="download")
            reg1.transition(aid, ArtifactState.VALIDATED, worker="validator")
            del reg1

            # Simulate restart: create new registry pointing to same file
            reg2 = LifecycleRegistry(path=path)
            assert reg2.get_state(aid) == ArtifactState.VALIDATED
            events = reg2.get_events(aid)
            assert len(events) >= 3  # registration + 2 transitions

    def test_corrupt_registry_recovers(self):
        """If registry JSON is corrupt, start fresh."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test_registry.json")
            with open(path, "w") as f:
                f.write("NOT VALID JSON {{{")
            reg = LifecycleRegistry(path=path)
            assert len(reg.get_pending()) == 0

    def test_event_log_completeness_after_crash(self):
        """Events recorded before 'crash' (save) are preserved."""
        with tempfile.TemporaryDirectory() as tmp:
            reg = self._make_registry(tmp)
            aid = reg.register("WAVEFORM", "ALR", "S260101.ALR")
            reg.transition(aid, ArtifactState.DOWNLOADED, worker="download")
            # Simulate crash — registry is on disk, state saved
            # Now continue
            reg.transition(aid, ArtifactState.VALIDATED, worker="validator")
            events = reg.get_events(aid)
            assert len(events) == 3  # registration + download + validation
            assert events[1]["worker"] == "download"
            assert events[2]["worker"] == "validator"


class TestDeduplication:
    """Idempotent registration prevents duplicate artifacts."""

    def test_duplicate_register_returns_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test_registry.json")
            reg = LifecycleRegistry(path=path)
            aid1 = reg.register("WAVEFORM", "ALR", "S260101.ALR")
            aid2 = reg.register("WAVEFORM", "ALR", "S260101.ALR")
            assert aid1 == aid2

    def test_different_type_allows_new(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test_registry.json")
            reg = LifecycleRegistry(path=path)
            aid1 = reg.register("WAVEFORM", "ALR", "S260101.ALR")
            aid2 = reg.register("HDF5", "ALR", "S260101.h5")
            assert aid1 != aid2


class TestTerminalStates:
    """PURGED and QUARANTINE have no outgoing transitions."""

    def _make_registry(self, tmp):
        path = os.path.join(tmp, "test_registry.json")
        return LifecycleRegistry(path=path)

    def test_purged_cannot_transition(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = self._make_registry(tmp)
            aid = reg.register("WAVEFORM", "ALR", "S260101.ALR")
            reg.transition(aid, ArtifactState.DOWNLOADED)
            reg.transition(aid, ArtifactState.VALIDATED)
            reg.transition(aid, ArtifactState.PARSED)
            reg.transition(aid, ArtifactState.HDF5_CREATED)
            reg.transition(aid, ArtifactState.VERIFIED)
            reg.transition(aid, ArtifactState.INFERENCE_DONE)
            reg.transition(aid, ArtifactState.PURGED)
            import pytest
            with pytest.raises(ValueError):
                reg.transition(aid, ArtifactState.NEW)
            with pytest.raises(ValueError):
                reg.transition(aid, ArtifactState.DOWNLOADED)

    def test_quarantined_cannot_transition(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = self._make_registry(tmp)
            aid = reg.register("WAVEFORM", "ALR", "S260101.ALR")
            reg.transition(aid, ArtifactState.DOWNLOADED)
            reg.transition(aid, ArtifactState.QUARANTINE)
            import pytest
            with pytest.raises(ValueError):
                reg.transition(aid, ArtifactState.DOWNLOADED)


class TestUUIDPermanence:
    """Every artifact gets a permanent UUID, not tied to filename."""

    def _make_registry(self, tmp):
        path = os.path.join(tmp, "test_registry.json")
        return LifecycleRegistry(path=path)

    def test_uuid_is_permanent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test_registry.json")
            reg = LifecycleRegistry(path=path)
            aid = reg.register("WAVEFORM", "ALR", "S260101.ALR")
            # UUID should be a valid UUID string
            uuid_obj = uuid.UUID(aid)  # raises if invalid
            assert uuid_obj.version == 4

    def test_uuid_unique_per_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test_registry.json")
            reg = LifecycleRegistry(path=path)
            aid1 = reg.register("WAVEFORM", "ALR", "S260101.ALR")
            aid2 = reg.register("WAVEFORM", "SCN", "S260101.SCN")
            assert aid1 != aid2

    def test_count_by_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = self._make_registry(tmp)
            aid = reg.register("WAVEFORM", "ALR", "S260101.ALR")
            reg.transition(aid, ArtifactState.DOWNLOADED)
            counts = reg.count()
            assert counts.get("DOWNLOADED", 0) == 1


def _run_standalone():
    """Run all tests when executed as script."""
    import traceback
    passed = 0
    failed = 0
    errors = []

    test_classes = [
        TestEnumStates, TestTransitionValidator, TestRegistryTransitions,
        TestDependencyGraph, TestCrashRecovery, TestDeduplication,
        TestTerminalStates, TestUUIDPermanence,
    ]

    for cls in test_classes:
        instance = cls()
        for method_name in sorted(dir(instance)):
            if not method_name.startswith("test_"):
                continue
            method = getattr(instance, method_name)
            try:
                method()
                passed += 1
                print(f"  ✓ {cls.__name__}.{method_name}")
            except Exception as e:
                failed += 1
                errors.append((cls.__name__, method_name, e))
                print(f"  ✗ {cls.__name__}.{method_name}: {e}")

    print(f"\n{'='*50}")
    print(f"Total: {passed + failed}  Passed: {passed}  Failed: {failed}")
    if errors:
        print("\nFailures:")
        for cls_name, method, err in errors:
            print(f"  {cls_name}.{method}: {err}")
    return failed == 0


if __name__ == "__main__":
    success = _run_standalone()
    sys.exit(0 if success else 1)
