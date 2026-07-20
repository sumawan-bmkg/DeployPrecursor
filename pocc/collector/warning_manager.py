#!/usr/bin/env python3
"""
warning_manager.py — Warning lifecycle management.

Warnings are tied to events and have a lifecycle:
  NEW → ACTIVE → UPDATED → EXPIRED → VERIFIED

Each state change is audited.
"""
import json, os, time, logging, hashlib
from enum import Enum
from typing import Optional, List
from pathlib import Path

log = logging.getLogger("warning_manager")

WARNING_DIR = "/opt/pimes/laws/runtime/validation/pdac/warnings"
os.makedirs(WARNING_DIR, exist_ok=True)


class WarningState(str, Enum):
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    UPDATED = "UPDATED"
    EXPIRED = "EXPIRED"
    VERIFIED = "VERIFIED"
    RETRACTED = "RETRACTED"


class Warning:
    def __init__(self, warning_id: str, event_id: str, level: str, probability: float, stations: list):
        self.warning_id = warning_id
        self.event_id = event_id
        self.state = WarningState.NEW
        self.level = level  # WATCH / WARNING / CRITICAL
        self.probability = probability
        self.stations = stations
        self.issued_at = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        self.updated_at = self.issued_at
        self.expired_at = None
        self.audit_log = []

    def transition(self, new_state: str, reason: str = ""):
        ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        entry = {
            "from": self.state.value,
            "to": new_state,
            "timestamp": ts,
            "reason": reason,
        }
        self.audit_log.append(entry)
        self.state = WarningState(new_state)
        self.updated_at = ts
        if new_state in ("EXPIRED", "RETRACTED"):
            self.expired_at = ts
        log.info("Warning %s: %s → %s (%s)", self.warning_id, entry["from"], new_state, reason)

    def to_dict(self):
        return {
            "warning_id": self.warning_id,
            "event_id": self.event_id,
            "state": self.state.value,
            "level": self.level,
            "probability": self.probability,
            "stations": self.stations,
            "issued_at": self.issued_at,
            "updated_at": self.updated_at,
            "expired_at": self.expired_at,
            "audit_log": self.audit_log,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Warning":
        w = cls(d["warning_id"], d["event_id"], d["level"], d["probability"], d.get("stations", []))
        w.state = WarningState(d.get("state", "NEW"))
        w.issued_at = d.get("issued_at", "")
        w.updated_at = d.get("updated_at", "")
        w.expired_at = d.get("expired_at")
        w.audit_log = d.get("audit_log", [])
        return w


class WarningManager:
    """
    Creates and manages warnings linked to events.

    - Translates Decision → Warning
    - Prevents duplicate warnings for same event
    - Tracks distribution (dashboard, future: email/tg)
    - Full audit trail
    """

    def __init__(self, data_dir: str = WARNING_DIR):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def issue_warning(self, event_id: str, level: str, probability: float, stations: list,
                      reason: str = "") -> Optional[Warning]:
        """Create new warning for an event."""
        # Check if active warning already exists for this event
        existing = self._find_active_by_event(event_id)
        if existing:
            existing.transition(WarningState.UPDATED.value, reason or f"Updated P={probability:.4f}")
            existing.probability = probability
            existing.level = level
            self._persist(existing)
            return existing

        wid = "WRN-" + hashlib.md5(f"{event_id}{time.time_ns()}".encode()).hexdigest()[:10]
        warning = Warning(wid, event_id, level, probability, stations)
        self._persist(warning)
        log.info("New warning %s for event %s: %s P=%.4f", wid, event_id, level, probability)
        return warning

    def expire_warning(self, warning_id: str, reason: str = "Auto-expired"):
        w = self._load(warning_id)
        if w:
            w.transition(WarningState.EXPIRED.value, reason)
            self._persist(w)

    def verify_warning(self, warning_id: str, matched: bool, reason: str = ""):
        w = self._load(warning_id)
        if w:
            w.transition(WarningState.VERIFIED.value, reason or ("TP confirmed" if matched else "FP confirmed"))
            self._persist(w)

    def retract_warning(self, warning_id: str, reason: str = "Manual retraction"):
        w = self._load(warning_id)
        if w:
            w.transition(WarningState.RETRACTED.value, reason)
            self._persist(w)

    def expire_stale(self, max_age_hours: float = 48.0):
        """Auto-expire old warnings."""
        import glob
        now = time.time()
        for fp in glob.glob(os.path.join(self.data_dir, "WRN-*.json")):
            try:
                with open(fp) as f:
                    d = json.load(f)
                if d.get("state") in ("EXPIRED", "RETRACTED", "VERIFIED"):
                    continue
                issued = d.get("issued_at", "")
                if issued:
                    from datetime import datetime
                    it = datetime.fromisoformat(issued.replace("Z", "+00:00")).timestamp()
                    if (now - it) / 3600 > max_age_hours:
                        self.expire_warning(d["warning_id"], f"Auto-expired after {max_age_hours:.0f}h")
            except:
                pass

    def _find_active_by_event(self, event_id: str) -> Optional[Warning]:
        import glob
        for fp in glob.glob(os.path.join(self.data_dir, "WRN-*.json")):
            try:
                with open(fp) as f:
                    d = json.load(f)
                if d.get("event_id") == event_id and d.get("state") in ("NEW", "ACTIVE", "UPDATED"):
                    return Warning.from_dict(d)
            except:
                pass
        return None

    def _load(self, warning_id: str) -> Optional[Warning]:
        fp = os.path.join(self.data_dir, f"{warning_id}.json")
        if os.path.exists(fp):
            with open(fp) as f:
                return Warning.from_dict(json.load(f))
        return None

    def _persist(self, warning: Warning):
        fp = os.path.join(self.data_dir, f"{warning.warning_id}.json")
        with open(fp, "w") as f:
            json.dump(warning.to_dict(), f, indent=2)

    def list_warnings(self, state: str = "", limit: int = 50) -> list:
        import glob
        files = sorted(glob.glob(os.path.join(self.data_dir, "WRN-*.json")))[-limit:]
        results = []
        for fp in files:
            with open(fp) as f:
                d = json.load(f)
                if state and d.get("state") != state:
                    continue
                results.append(d)
        return results

    def get_warning(self, warning_id: str) -> Optional[dict]:
        w = self._load(warning_id)
        return w.to_dict() if w else None
