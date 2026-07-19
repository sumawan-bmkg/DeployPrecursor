#!/usr/bin/env python3
"""LAWS V2 ArtifactManager v2.1 - ARCHIVED state, transactional delete, backend abstraction."""
from __future__ import annotations
import hashlib, logging, os, shutil, time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from lifecycle_registry import (
    LifecycleRegistry, ArtifactState, ArtifactType, StorageClass,
    EventCategory, DEFAULT_REGISTRY_PATH,
)
log = logging.getLogger("artifact_manager")


class ArtifactBackend(ABC):
    """Abstract storage backend. LocalFilesystemBackend, S3Backend, etc."""
    @abstractmethod
    def exists(self, path): ...
    @abstractmethod
    def move(self, src, dst): ...
    @abstractmethod
    def remove(self, path): ...
    @abstractmethod
    def sha256(self, path): ...
    @abstractmethod
    def file_size(self, path): ...


class LocalFilesystemBackend(ArtifactBackend):
    def exists(self, path): return os.path.exists(path)
    def move(self, src, dst):
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.move(src, str(dst))
        return str(dst)
    def remove(self, path):
        if os.path.exists(path): os.remove(path); return True
        return False
    def sha256(self, path):
        with open(path, "rb") as f: return hashlib.sha256(f.read()).hexdigest()
    def file_size(self, path): return os.path.getsize(path)


class ArtifactManager:
    ARTIFACT_ROOTS = {
        "waveform": "/opt/pimes/runtime/cache/raw",
        "hdf5": "/opt/pimes/data/hdf5",
        "prediction": "/opt/pimes/data/predictions",
        "alert": "/opt/pimes/data/alerts",
        "log": "/opt/pimes/data/logs",
        "qc": "/opt/pimes/data/qc",
        "audit": "/opt/pimes/data/audit",
    }

    def __init__(self, registry=None, backend=None):
        self.registry = registry or LifecycleRegistry(DEFAULT_REGISTRY_PATH)
        self.backend = backend or LocalFilesystemBackend()

    def register(self, artifact_type, station, filename, upstream=None, metadata=None, storage_class=StorageClass.CACHE):
        return self.registry.register(artifact_type=artifact_type, station=station, filename=filename, upstream=upstream, metadata=metadata or {}, storage_class=storage_class)

    def exists(self, aid):
        return self.registry.get_record(aid) is not None

    def file_exists(self, aid):
        r = self.registry.get_record(aid)
        return bool(r and r.file_path and self.backend.exists(r.file_path))

    def move(self, aid, dest):
        r = self.registry.get_record(aid)
        if not r: raise KeyError(f"Not found: {aid}")
        src = r.file_path
        if not src or not self.backend.exists(src):
            self.registry.set_file_path(aid, dest)
            return dest
        result = self.backend.move(src, dest)
        self.registry.set_file_path(aid, result)
        return result

    def verify(self, aid, expected=None):
        r = self.registry.get_record(aid)
        if not r: raise KeyError(f"Not found: {aid}")
        fp = r.file_path
        if not fp or not self.backend.exists(fp): raise FileNotFoundError(f"File not found: {fp}")
        c = self.backend.sha256(fp)
        if expected and c != expected:
            self.registry.add_event(aid, EventCategory.ERROR, "SHA256 mismatch")
            raise ValueError(f"SHA256 mismatch for {aid}")
        self.registry.set_sha256(aid, c)
        self.registry.set_file_size(aid, self.backend.file_size(fp))
        return c

    def archive(self, aid, archive_root=""):
        """Move to archive. State -> ARCHIVED. StorageClass -> ARCHIVE."""
        r = self.registry.get_record(aid)
        if not r: raise KeyError(f"Not found: {aid}")
        state = self.registry.get_state(aid)
        if state == ArtifactState.NEW:
            self.registry.transition(aid, ArtifactState.DOWNLOADED, worker="artifact_manager", reason="pre-archive")
        src = r.file_path
        if not src or not self.backend.exists(src):
            log.warning("Archive %s: no file", aid)
            self.registry.transition(aid, ArtifactState.ARCHIVED, worker="artifact_manager", reason="no file to archive", category=EventCategory.ARCHIVE)
            self.registry.set_storage_class(aid, StorageClass.ARCHIVE)
            return ""
        ar = archive_root or "/opt/pimes/data/archive"
        dst = Path(ar) / r.artifact_type / r.station / r.filename
        self.backend.move(src, str(dst))
        self.registry.set_file_path(aid, str(dst))
        self.registry.set_storage_class(aid, StorageClass.ARCHIVE)
        self.registry.transition(aid, ArtifactState.ARCHIVED, worker="artifact_manager", reason="archived", category=EventCategory.ARCHIVE)
        return str(dst)

    def restore(self, aid, dest=""):
        r = self.registry.get_record(aid)
        if not r: raise KeyError(f"Not found: {aid}")
        src = r.file_path
        if not src or not self.backend.exists(src): raise FileNotFoundError(f"Not found: {src}")
        if not dest:
            root = self.ARTIFACT_ROOTS.get(r.artifact_type, "/opt/pimes/data/restored")
            dest = str(Path(root) / r.station / r.filename)
        result = self.backend.move(src, dest)
        self.registry.set_file_path(aid, result)
        self.registry.set_storage_class(aid, StorageClass.CACHE)
        return result

    def delete(self, aid, force=False):
        """Transactional delete: Candidate -> Verify -> Lock -> Delete -> Verify Missing -> Audit -> Unlock."""
        r = self.registry.get_record(aid)
        if not r: raise KeyError(f"Not found: {aid}")

        # 1. Precondition check
        if not force:
            if self.registry.is_locked(aid): raise PermissionError("Delete denied: locked")
            if not self.registry.is_downstream_valid(aid): raise PermissionError("Delete denied: upstream failures")

        fp = r.file_path

        # 2. Acquire lock
        locked = self.registry.lock(aid, worker="delete_worker", ttl=300)
        if not locked:
            raise PermissionError(f"Delete denied: could not lock {aid}")

        try:
            # 3. Delete file
            deleted = False
            if fp:
                deleted = self.backend.remove(fp)

            # 4. Verify missing
            if fp and deleted and self.backend.exists(fp):
                self.registry.add_event(aid, EventCategory.DELETE, f"DELETE FAILED: file still exists at {fp}", worker="delete_worker")
                raise RuntimeError(f"Delete failed: file still exists at {fp}")

            # 5. Registry update
            self.registry.update_metadata(aid,
                deleted_at=datetime.now(timezone.utc).isoformat(),
                deleted_by="delete_worker",
                file_existed=deleted,
            )

            # 6. Audit log
            self.registry.add_event(aid, EventCategory.DELETE,
                f"Transactional delete: file_existed={deleted}, path={fp}",
                worker="delete_worker")
            log.info("Deleted %s: file_existed=%s, path=%s", aid, deleted, fp)

        finally:
            # 7. Always unlock
            self.registry.unlock(aid, worker="delete_worker")

    def lock(self, aid, worker="", ttl=600):
        return self.registry.lock(aid, worker=worker, ttl=ttl)

    def unlock(self, aid, worker=""):
        return self.registry.unlock(aid, worker=worker)

    def metadata(self, aid, key, value):
        self.registry.update_metadata(aid, **{key: value})

    def get_metadata(self, aid, key=""):
        r = self.registry.get_record(aid)
        if not r: raise KeyError(f"Not found: {aid}")
        return r.metadata.get(key) if key else dict(r.metadata)

    def get_size(self, aid):
        r = self.registry.get_record(aid)
        if not r: raise KeyError(f"Not found: {aid}")
        return r.file_size

    def get_path(self, aid):
        r = self.registry.get_record(aid)
        if not r: raise KeyError(f"Not found: {aid}")
        return r.file_path

    def link(self, up, down):
        self.registry.link(up, down)
