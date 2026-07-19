#!/usr/bin/env python3
"""LAWS V2 LifecycleRegistry v2.2 - ARCHIVED state added."""
from __future__ import annotations
import json, logging, os, time, uuid as _uuid
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional

log = logging.getLogger("lifecycle_registry")
DEFAULT_REGISTRY_PATH = "/opt/pimes/pocc/runtime/lifecycle_registry.json"


class ArtifactState(Enum):
    NEW = "NEW"
    DOWNLOADED = "DOWNLOADED"
    VALIDATED = "VALIDATED"
    PARSED = "PARSED"
    HDF5_CREATED = "HDF5_CREATED"
    VERIFIED = "VERIFIED"
    INFERENCE_DONE = "INFERENCE_DONE"
    ARCHIVED = "ARCHIVED"
    PURGED = "PURGED"
    QUARANTINED = "QUARANTINED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"

    def __str__(self):
        return self.value


class ArtifactType(Enum):
    WAVEFORM = "waveform"
    HDF5 = "hdf5"
    PREDICTION = "prediction"
    ALERT = "alert"
    LOG = "log"
    QC = "qc"
    AUDIT = "audit"

    def __str__(self):
        return self.value


class StorageClass(Enum):
    CACHE = "cache"
    LEGACY = "legacy"
    QUARANTINED = "quarantine"
    ARCHIVE = "archive"
    PERMANENT = "permanent"

    def __str__(self):
        return self.value


class EventCategory(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    RECOVERY = "recovery"
    PURGE = "purge"
    LOCK = "lock"
    DELETE = "delete"
    ARCHIVE = "archive"

    def __str__(self):
        return self.value


_ALLOWED = {
    ArtifactState.NEW:             {ArtifactState.DOWNLOADED, ArtifactState.EXPIRED, ArtifactState.CANCELLED},
    ArtifactState.DOWNLOADED:      {ArtifactState.VALIDATED, ArtifactState.QUARANTINED, ArtifactState.CANCELLED},
    ArtifactState.VALIDATED:       {ArtifactState.PARSED, ArtifactState.QUARANTINED, ArtifactState.CANCELLED},
    ArtifactState.PARSED:          {ArtifactState.HDF5_CREATED, ArtifactState.QUARANTINED, ArtifactState.CANCELLED},
    ArtifactState.HDF5_CREATED:    {ArtifactState.VERIFIED, ArtifactState.QUARANTINED, ArtifactState.CANCELLED},
    ArtifactState.VERIFIED:        {ArtifactState.INFERENCE_DONE, ArtifactState.QUARANTINED, ArtifactState.CANCELLED},
    ArtifactState.INFERENCE_DONE:  {ArtifactState.PURGED, ArtifactState.QUARANTINED, ArtifactState.ARCHIVED},
    ArtifactState.ARCHIVED:        {ArtifactState.PURGED},
    ArtifactState.PURGED:          set(),
    ArtifactState.QUARANTINED:     set(),
    ArtifactState.CANCELLED:       set(),
    ArtifactState.EXPIRED:         set(),
}


def validate_transition(from_state, to_state):
    return to_state in _ALLOWED.get(from_state, set())


@dataclass
class TransitionEvent:
    timestamp: str = ""
    from_state: str = ""
    to_state: str = ""
    worker: str = ""
    reason: str = ""
    category: str = EventCategory.INFO.value
    duration_ms: float = 0.0
    host: str = ""


@dataclass
class ArtifactRecord:
    artifact_id: str = ""
    artifact_type: str = ""
    station: str = ""
    filename: str = ""
    state: str = ArtifactState.NEW.value
    storage_class: str = StorageClass.CACHE.value
    upstream: Optional[str] = None
    downstream: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    events: list = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    file_path: str = ""
    sha256: str = ""
    file_size: int = 0
    retry_count: int = 0


class LifecycleRegistry:
    def __init__(self, path=None):
        self.path = Path(path or DEFAULT_REGISTRY_PATH)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data = {}
        self._load()

    def register(self, artifact_type, station, filename, metadata=None, upstream=None, file_path="", storage_class=StorageClass.CACHE):
        type_str = str(artifact_type.value) if hasattr(artifact_type, 'value') else artifact_type
        for rec in self._data.values():
            if (rec.artifact_type == type_str and rec.station == station and rec.filename == filename
                    and rec.state not in (ArtifactState.PURGED.value, ArtifactState.QUARANTINED.value, ArtifactState.CANCELLED.value, ArtifactState.EXPIRED.value)):
                return rec.artifact_id
        aid = str(_uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        sc = str(storage_class.value) if hasattr(storage_class, 'value') else storage_class
        initial = asdict(TransitionEvent(timestamp=now, from_state="", to_state=ArtifactState.NEW.value, worker="system", reason="Artifact registered", category=EventCategory.INFO.value, host=self._host()))
        rec = ArtifactRecord(artifact_id=aid, artifact_type=type_str, station=station, filename=filename, state=ArtifactState.NEW.value, storage_class=sc, upstream=upstream, metadata=metadata or {}, events=[initial], created_at=now, updated_at=now, file_path=file_path)
        self._data[aid] = rec
        self._save()
        return aid

    def transition(self, aid, to_state, worker="", reason="", category=None):
        rec = self._get(aid)
        from_state = ArtifactState(rec.state)
        if from_state == to_state:
            return rec
        if not validate_transition(from_state, to_state):
            raise ValueError(f"Illegal transition: {from_state} -> {to_state} for {rec.artifact_type} {rec.station}/{rec.filename}")
        if category is None:
            category = EventCategory.INFO
        t0 = time.perf_counter()
        cat = str(category.value) if hasattr(category, 'value') else category
        ev = asdict(TransitionEvent(timestamp=datetime.now(timezone.utc).isoformat(), from_state=from_state.value, to_state=to_state.value, worker=worker or "unknown", reason=reason, category=cat, host=self._host()))
        rec.events.append(ev)
        rec.state = to_state.value
        rec.updated_at = ev["timestamp"]
        rec.metadata["last_transition"] = ev["timestamp"]
        # Cascade QUARANTINED
        if to_state == ArtifactState.QUARANTINED:
            terminal = {ArtifactState.PURGED.value, ArtifactState.QUARANTINED.value, ArtifactState.CANCELLED.value, ArtifactState.EXPIRED.value, ArtifactState.ARCHIVED.value}
            for did in rec.downstream:
                down = self._data.get(did)
                if down and down.state not in terminal:
                    try:
                        self.transition(did, ArtifactState.QUARANTINED, worker="system", reason=f"Cascade from {aid}: {reason}", category=EventCategory.ERROR)
                    except ValueError:
                        pass
        self._save()
        elapsed = (time.perf_counter() - t0) * 1000
        rec.events[-1]["duration_ms"] = round(elapsed, 1)
        self._save()
        return rec

    def get_state(self, aid):
        return ArtifactState(self._get(aid).state)

    def get_type(self, aid):
        return ArtifactType(self._get(aid).artifact_type)

    def get_storage_class(self, aid):
        return StorageClass(self._get(aid).storage_class)

    def get_record(self, aid):
        return self._data.get(aid)

    def get_events(self, aid, category=None, limit=0):
        rec = self._get(aid)
        events = list(rec.events)
        if category:
            cat_str = str(category.value) if hasattr(category, 'value') else category
            events = [e for e in events if e.get("category") == cat_str]
        if limit > 0:
            events = events[-limit:]
        return events

    def find(self, artifact_type=None, station=None, state=None, storage_class=None, limit=100):
        results = []
        for rec in self._data.values():
            if artifact_type:
                at = str(artifact_type.value) if hasattr(artifact_type, 'value') else artifact_type
                if rec.artifact_type != at: continue
            if station and rec.station != station: continue
            if state and rec.state != state.value: continue
            if storage_class:
                sc = str(storage_class.value) if hasattr(storage_class, 'value') else storage_class
                if rec.storage_class != sc: continue
            results.append(rec)
            if len(results) >= limit: break
        return results

    def get_pending(self, artifact_type=None):
        terminal = {ArtifactState.PURGED.value, ArtifactState.QUARANTINED.value, ArtifactState.CANCELLED.value, ArtifactState.EXPIRED.value}
        return [r for r in self._data.values() if r.state not in terminal and (artifact_type is None or r.artifact_type == (str(artifact_type.value) if hasattr(artifact_type, 'value') else artifact_type))]

    def count(self):
        from collections import Counter
        return dict(Counter(r.state for r in self._data.values()))

    def link(self, up, down):
        up_r = self._get(up)
        dn_r = self._get(down)
        if down not in up_r.downstream: up_r.downstream.append(down)
        dn_r.upstream = up
        self._save()

    def get_downstream(self, aid):
        rec = self._get(aid)
        return [self._data[d] for d in rec.downstream if d in self._data]

    def get_upstream(self, aid):
        rec = self._get(aid)
        return self._data.get(rec.upstream) if rec.upstream else None

    def is_downstream_valid(self, aid):
        checked = set()
        current = aid
        while current and current not in checked:
            checked.add(current)
            rec = self._data.get(current)
            if not rec: break
            if rec.state == ArtifactState.QUARANTINED.value: return False
            current = rec.upstream
        return True

    def update_metadata(self, aid, **kw):
        rec = self._get(aid)
        rec.metadata.update(kw)
        rec.updated_at = datetime.now(timezone.utc).isoformat()
        self._save()

    def set_sha256(self, aid, v):
        rec = self._get(aid); rec.sha256 = v; rec.updated_at = self._now(); self._save()

    def set_file_path(self, aid, v):
        rec = self._get(aid); rec.file_path = v; rec.updated_at = self._now(); self._save()

    def set_file_size(self, aid, v):
        rec = self._get(aid); rec.file_size = v; rec.updated_at = self._now(); self._save()

    def set_storage_class(self, aid, sc):
        rec = self._get(aid); rec.storage_class = str(sc.value) if hasattr(sc, 'value') else sc; rec.updated_at = self._now(); self._save()

    def increment_retry(self, aid):
        rec = self._get(aid); rec.retry_count += 1; rec.updated_at = self._now(); self._save()
        return rec.retry_count

    def get_retry_count(self, aid):
        return self._get(aid).retry_count

    def lock(self, aid, worker="", ttl=600):
        rec = self._get(aid)
        now = datetime.now(timezone.utc)
        until_str = rec.metadata.get("locked_until")
        if until_str:
            try:
                if datetime.fromisoformat(until_str) > now and rec.metadata.get("locked_by") not in (None, "", worker):
                    return False
            except ValueError: pass
        rec.metadata["locked_by"] = worker or "unknown"
        rec.metadata["locked_at"] = now.isoformat()
        rec.metadata["locked_until"] = (now + timedelta(seconds=ttl)).isoformat()
        rec.metadata["lock_ttl"] = ttl
        self._save()
        return True

    def unlock(self, aid, worker=""):
        rec = self._get(aid)
        if self.is_locked(aid) and rec.metadata.get("locked_by") not in (None, "", worker):
            return False
        for k in ("locked_by", "locked_at", "locked_until", "lock_ttl"):
            rec.metadata.pop(k, None)
        self._save()
        return True

    def is_locked(self, aid):
        rec = self._get(aid)
        until_str = rec.metadata.get("locked_until")
        if until_str:
            try:
                if datetime.fromisoformat(until_str) <= datetime.now(timezone.utc): return False
            except ValueError: pass
            return True
        return bool(rec.metadata.get("locked_by"))

    def add_event(self, aid, category, message, worker=""):
        rec = self._get(aid)
        cat = str(category.value) if hasattr(category, 'value') else category
        rec.events.append({"timestamp": self._now(), "from_state": rec.state, "to_state": rec.state, "worker": worker or "unknown", "reason": message, "category": cat, "duration_ms": 0.0, "host": self._host()})
        rec.updated_at = self._now()
        self._save()

    # Legacy compat
    def mark_done(self, aid, worker="legacy"):
        rec = self._get(aid)
        from_state = ArtifactState(rec.state)
        forward = [s for s in _ALLOWED.get(from_state, set()) if s not in (ArtifactState.QUARANTINED, ArtifactState.CANCELLED, ArtifactState.EXPIRED)]
        if forward: self.transition(aid, forward[0], worker=worker, reason="mark_done legacy")

    def set_status(self, aid, status, worker="legacy"):
        s = status.upper()
        try: self.transition(aid, ArtifactState(s), worker=worker, reason="set_status legacy"); return
        except ValueError: pass
        m = {"READY": ArtifactState.HDF5_CREATED, "DONE": ArtifactState.INFERENCE_DONE, "ERROR": ArtifactState.QUARANTINED, "FAILED": ArtifactState.QUARANTINED, "COMPLETE": ArtifactState.INFERENCE_DONE, "PROCESSED": ArtifactState.PARSED, "ARCHIVED": ArtifactState.ARCHIVED}
        if s in m: self.transition(aid, m[s], worker=worker, reason=f"legacy_map({status})")

    def get_status(self, aid):
        return self.get_state(aid).value

    # Internal
    def _get(self, aid):
        if aid not in self._data: raise KeyError(f"Artifact not found: {aid}")
        return self._data[aid]
    def _now(self): return datetime.now(timezone.utc).isoformat()
    def _host(self): return os.uname().nodename if hasattr(os, 'uname') else "localhost"
    def _serialize(self):
        return {"schema_version": "2.2", "updated_at": self._now(), "artifacts": {a: asdict(r) for a, r in self._data.items()}}
    def _save(self):
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "w") as f: json.dump(self._serialize(), f, indent=2, default=str)
        tmp.replace(self.path)
    def _load(self):
        if not self.path.exists(): return
        try:
            with open(self.path) as f: raw = json.load(f)
            for aid, data in raw.get("artifacts", {}).items():
                self._data[aid] = ArtifactRecord(**data)
        except Exception:
            self._data = {}
    def clear(self): self._data = {}; self._save()
