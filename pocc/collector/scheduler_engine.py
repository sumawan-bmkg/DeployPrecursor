#!/usr/bin/env python3
"""
Phase 1: Collector Scheduler Engine — Main orchestration loop.
Production-grade scheduler. No cron dependency.
"""
import os, sys, json, time, uuid, hashlib, threading, logging, signal
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Optional

PDAC_DIR = Path("/opt/pimes/laws/runtime/validation/pdac")
COLLECTOR_DIR = Path("/opt/pimes/pocc/collector")
os.makedirs(PDAC_DIR, exist_ok=True)
os.makedirs(COLLECTOR_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(str(PDAC_DIR / "scheduler.log")),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("scheduler")

# ── Scheduler Manifest ───────────────────────────────────
class SchedulerManifest:
    """Single Source of Truth for all collector operations."""
    def __init__(self):
        self.path = PDAC_DIR / "collector_manifest.json"
        self.data = self._load()
    
    def _load(self) -> dict:
        try:
            with open(self.path) as f:
                return json.load(f)
        except:
            return {
                "scheduler_uuid": str(uuid.uuid4()),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "version": "2.0.0",
                "workers": {},
                "last_discovery": None,
                "last_download": None,
                "last_validation": None,
                "last_runtime_trigger": None,
                "remote": {},
                "local": {},
                "queue": {"waiting": 0, "running": 0, "success": 0,
                         "failed": 0, "retry": 0, "skipped": 0, "corrupted": 0},
                "health": {
                    "uptime": 0, "latency": 0, "download_speed": 0,
                    "retry_rate": 0, "failure_rate": 0, "bandwidth": 0,
                    "availability": 1.0
                }
            }
    
    def save(self):
        self.data["updated_at"] = datetime.now(timezone.utc).isoformat()
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2, default=str)
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def set(self, key, value):
        self.data[key] = value
    
    def worker_status(self, name: str) -> dict:
        w = self.data["workers"].setdefault(name, {
            "uuid": str(uuid.uuid4()),
            "status": "idle",
            "start_time": None,
            "end_time": None,
            "duration": 0,
            "heartbeat": None,
            "last_success": None,
            "last_error": None,
            "retry_count": 0,
        })
        return w
    
    def update_worker(self, name: str, **kwargs):
        w = self.worker_status(name)
        for k, v in kwargs.items():
            w[k] = v
        self.data["workers"][name] = w

# ── Base Worker ──────────────────────────────────────────
class BaseWorker(threading.Thread):
    """Reusable worker base with heartbeat, retry, status tracking."""
    def __init__(self, name: str, manifest: SchedulerManifest, interval: float = 300):
        super().__init__(daemon=True)
        self.name = name
        self.manifest = manifest
        self.interval = interval  # seconds between runs
        self._stop_event = threading.Event()
        self.log = logging.getLogger(name)
    
    def stop(self):
        self._stop_event.set()
    
    def run(self):
        self.log.info("%s started (interval=%ds)", self.name, self.interval)
        self.manifest.update_worker(self.name, status="running", start_time=datetime.now(timezone.utc).isoformat())
        self.manifest.save()
        
        while not self._stop_event.is_set():
            try:
                t0 = time.time()
                self.manifest.update_worker(self.name, status="running", heartbeat=datetime.now(timezone.utc).isoformat())
                
                # Execute task
                result = self.execute()
                
                duration = time.time() - t0
                self.manifest.update_worker(
                    self.name, status="idle", duration=duration,
                    last_success=datetime.now(timezone.utc).isoformat(),
                    end_time=datetime.now(timezone.utc).isoformat()
                )
                self.log.info("%s complete (%.2fs)", self.name, duration)
                
                if result:
                    self.manifest.set("last_" + self.name.split("_")[0], result)
                self.manifest.save()
                
            except Exception as e:
                self.log.error("%s failed: %s", self.name, str(e)[:200])
                self.manifest.update_worker(
                    self.name, status="error", last_error=str(e)[:200],
                    retry_count=self.manifest.worker_status(self.name).get("retry_count", 0) + 1
                )
                self.manifest.save()
            
            # Sleep with interrupt check
            for _ in range(int(self.interval)):
                if self._stop_event.is_set():
                    break
                time.sleep(1)
        
        self.log.info("%s stopped", self.name)
    
    def execute(self) -> Optional[dict]:
        """Override in subclass."""
        raise NotImplementedError

# ── Manifest singleton ──────────────────────────────────
manifest = SchedulerManifest()
