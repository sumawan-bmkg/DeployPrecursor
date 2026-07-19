#!/usr/bin/env python3
"""LAWS V2 CacheManager v2.1 - ARCHIVED for archive, PURGED only from INFERENCE_DONE."""
from __future__ import annotations
import hashlib, logging, os, shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from lifecycle_registry import (
    LifecycleRegistry, ArtifactState, ArtifactType, StorageClass,
    EventCategory, DEFAULT_REGISTRY_PATH,
)
log = logging.getLogger("cache_manager")


class CacheManager:
    DEFAULT_CACHE_ROOT = "/opt/pimes/runtime/cache/raw"
    DEFAULT_TTL_HOURS = 24

    def __init__(self, registry=None, cache_root="", default_ttl_hours=24):
        self.registry = registry or LifecycleRegistry(DEFAULT_REGISTRY_PATH)
        self.cache_root = Path(cache_root or self.DEFAULT_CACHE_ROOT)
        self.default_ttl_hours = default_ttl_hours

    def reserve(self, artifact_type, station, filename, metadata=None):
        type_str = str(artifact_type.value) if hasattr(artifact_type, 'value') else artifact_type
        cache_path = self.cache_root / station / filename
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=self.default_ttl_hours)
        meta = {"reserved_at": now.isoformat(), "expires_at": expires.isoformat(), "ttl_hours": self.default_ttl_hours, "cache_root": str(self.cache_root), "source": "cache_manager.reserve"}
        if metadata: meta.update(metadata)
        aid = self.registry.register(artifact_type=type_str, station=station, filename=filename, file_path=str(cache_path), metadata=meta, storage_class=StorageClass.CACHE)
        self.registry.set_file_path(aid, str(cache_path))
        return aid

    def verify(self, aid, expected_sha256=None):
        r = self.registry.get_record(aid)
        if not r: raise KeyError(f"Not found: {aid}")
        fp = r.file_path
        if not fp or not os.path.exists(fp): raise FileNotFoundError(f"File not found: {fp}")
        with open(fp, "rb") as f: data = f.read()
        computed = hashlib.sha256(data).hexdigest()
        if expected_sha256 and computed != expected_sha256:
            self.registry.add_event(aid, EventCategory.ERROR, "SHA256 mismatch")
            raise ValueError(f"SHA256 mismatch: expected {expected_sha256[:16]}...")
        self.registry.set_sha256(aid, computed)
        self.registry.set_file_size(aid, len(data))
        return computed

    def commit(self, aid, worker="cache_manager"):
        r = self.registry.get_record(aid)
        if not r: raise KeyError(f"Not found: {aid}")
        if not r.file_path or not os.path.exists(r.file_path): raise FileNotFoundError(f"No file at {r.file_path}")
        if not r.sha256: self.verify(aid)
        state = self.registry.get_state(aid)
        if state == ArtifactState.NEW:
            self.registry.transition(aid, ArtifactState.DOWNLOADED, worker=worker, reason="cache commit", category=EventCategory.INFO)
        elif state != ArtifactState.DOWNLOADED:
            raise ValueError(f"Commit failed: unexpected state {state}")

    def release(self, aid, worker="cache_manager"):
        self.registry.unlock(aid, worker=worker)

    def exists(self, aid): return self.registry.get_record(aid) is not None
    def lock(self, aid, worker="", ttl=600): return self.registry.lock(aid, worker=worker, ttl=ttl)
    def is_locked(self, aid): return self.registry.is_locked(aid)

    def touch(self, aid):
        r = self.registry.get_record(aid)
        if not r: raise KeyError(f"Not found: {aid}")
        now = datetime.now(timezone.utc)
        r.metadata["expires_at"] = (now + timedelta(hours=self.default_ttl_hours)).isoformat()
        r.metadata["last_touched_at"] = now.isoformat()
        r.updated_at = now.isoformat()
        self.registry._save()

    def purge(self, aid, reason=""):
        """Operational purge. PURGED only from INFERENCE_DONE. Otherwise CANCELLED."""
        r = self.registry.get_record(aid)
        if not r: raise KeyError(f"Not found: {aid}")
        state = self.registry.get_state(aid)
        terminal = {ArtifactState.PURGED, ArtifactState.QUARANTINED, ArtifactState.CANCELLED, ArtifactState.EXPIRED, ArtifactState.ARCHIVED}
        if state in terminal: return
        if state == ArtifactState.INFERENCE_DONE:
            self.registry.transition(aid, ArtifactState.PURGED, worker="cache_manager", reason=reason or "cache purge", category=EventCategory.PURGE)
        else:
            self.registry.transition(aid, ArtifactState.CANCELLED, worker="cache_manager", reason=reason or "cache purge", category=EventCategory.PURGE)
        self.registry.set_storage_class(aid, StorageClass.ARCHIVE)

    def quarantine(self, aid, reason="", detail=""):
        r = self.registry.get_record(aid)
        if not r: raise KeyError(f"Not found: {aid}")
        state = self.registry.get_state(aid)
        if state in (ArtifactState.PURGED, ArtifactState.QUARANTINED, ArtifactState.CANCELLED, ArtifactState.EXPIRED, ArtifactState.ARCHIVED): return
        if state == ArtifactState.NEW:
            self.registry.transition(aid, ArtifactState.DOWNLOADED, worker="cache_manager", reason="pre-quarantine", category=EventCategory.INFO)
        if r.file_path and os.path.exists(r.file_path):
            qdir = Path(r.metadata.get("cache_root", str(self.cache_root))).parent / "quarantine" / reason
            qdir.mkdir(parents=True, exist_ok=True)
            dst = qdir / r.filename
            shutil.move(r.file_path, str(dst))
            self.registry.set_file_path(aid, str(dst))
        self.registry.transition(aid, ArtifactState.QUARANTINED, worker="cache_manager", reason=f"{reason}: {detail}" if detail else reason, category=EventCategory.ERROR)
        self.registry.set_storage_class(aid, StorageClass.QUARANTINED)

    def get_manifest(self, aid):
        r = self.registry.get_record(aid)
        if not r: raise KeyError(f"Not found: {aid}")
        return {"uuid": aid, "station": r.station, "filename": r.filename, "type": r.artifact_type, "state": r.state, "storage_class": r.storage_class, "size": r.file_size, "sha256": r.sha256, "expires": r.metadata.get("expires_at", ""), "retry": r.retry_count, "path": r.file_path, "created_at": r.created_at, "updated_at": r.updated_at, "locked_by": r.metadata.get("locked_by", "")}

    def get_path(self, aid):
        r = self.registry.get_record(aid)
        if not r: raise KeyError(f"Not found: {aid}")
        return r.file_path
