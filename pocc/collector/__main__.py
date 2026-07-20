#!/usr/bin/env python3
"""
Production Collector Scheduler -- Main entry point.
Starts all workers and manages lifecycle.
"""
import os, sys, json, time, signal, logging, uuid
from datetime import datetime, timezone
from pathlib import Path

# Ensure collector package is on path
_COLLECTOR_DIR = Path(__file__).parent
sys.path.insert(0, str(_COLLECTOR_DIR.parent))  # /opt/pimes/pocc

from collector.scheduler_engine import manifest
from collector.discovery_worker import DiscoveryWorker
from collector.download_worker import DownloadWorker
from collector.validation_worker import ValidationWorker
from collector.inference_worker import InferenceWorker
from collector.evidence_builder import EvidenceBuilder
from collector.runtime_trigger import RuntimeTriggerWorker
from collector.audit_worker import AuditWorker
from collector.rawdata_worker import RawDataWorker

log = logging.getLogger("collector")

class CollectorScheduler:
    """Orchestrates all collector workers."""

    def __init__(self):
        self.workers = {}
        self.running = False

    def register(self, name: str, worker_class, interval: float):
        """Register a worker with its interval."""
        self.workers[name] = {"class": worker_class, "interval": interval, "instance": None}

    def start(self):
        self.running = True
        instances = []
        for name, cfg in self.workers.items():
            instance = cfg["class"](name, manifest, cfg["interval"])
            cfg["instance"] = instance
            instance.start()
            instances.append(instance)
            log.info("Started worker: %s (interval=%ds)", name, cfg["interval"])

        # Update manifest
        manifest.set("scheduler_uuid", manifest.get("scheduler_uuid", str(uuid.uuid4())))
        manifest.set("status", "running")
        manifest.set("started_at", datetime.now(timezone.utc).isoformat())
        manifest.save()

        # Wait for all
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            log.info("Shutting down...")
            for inst in instances:
                inst.stop()
            for inst in instances:
                inst.join(timeout=10)

        manifest.set("status", "stopped")
        manifest.save()
        log.info("Collector scheduler stopped.")

    def stop(self):
        self.running = False

# Main
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s")

    scheduler = CollectorScheduler()
    scheduler.register("discovery", DiscoveryWorker, 300)    # 5 min
    scheduler.register("download", DownloadWorker, 600)     # 10 min
    scheduler.register("validation", ValidationWorker, 60)  # 1 min
    scheduler.register("inference", InferenceWorker, 60)    # 1 min
    scheduler.register("runtime", RuntimeTriggerWorker, 60) # 1 min
    scheduler.register("audit", AuditWorker, 3600)          # 1 hour
    scheduler.register("evidence", EvidenceBuilder, 86400)   # daily (24h) — NEW
    scheduler.register("rawdata", RawDataWorker, 86400)     # daily (24h)

    scheduler.start()
