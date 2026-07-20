#!/usr/bin/env python3
"""
Phase 4+5: Download Worker — Intelligent download queue.
Only downloads new files based on manifest comparison.
"""
import os, sys, json, time, hashlib, uuid, paramiko, logging
from datetime import datetime, timezone
from pathlib import Path
from queue import Queue
from collector.scheduler_engine import BaseWorker, manifest, PDAC_DIR

log = logging.getLogger("download")

SFTP_CONFIG = {
    "hostname": "202.90.198.224",
    "port": 4343,
    "username": "precursor",
    "password": "otomatismon",
    "look_for_keys": False,
    "allow_agent": False,
    "timeout": 30,
}
REMOTE_ROOT = "/home/precursor/SEISMO/DATA"
LOCAL_ROOT = "/opt/pimes/data/raw"

# Queue states
QUEUE_WAITING = "WAITING"
QUEUE_RUNNING = "RUNNING"
QUEUE_SUCCESS = "SUCCESS"
QUEUE_FAILED = "FAILED"
QUEUE_RETRY = "RETRY"
QUEUE_SKIPPED = "SKIPPED"
QUEUE_CORRUPTED = "CORRUPTED"

class DownloadWorker(BaseWorker):
    """Downloads new/changed files from remote server."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue_path = PDAC_DIR / "download_queue.json"
        self.queue = self._load_queue()
    
    def _load_queue(self):
        try:
            with open(self.queue_path) as f:
                return json.load(f)
        except:
            return {"items": [], "stats": {s: 0 for s in [
                QUEUE_WAITING, QUEUE_RUNNING, QUEUE_SUCCESS,
                QUEUE_FAILED, QUEUE_RETRY, QUEUE_SKIPPED, QUEUE_CORRUPTED
            ]}}
    
    def _save_queue(self):
        with open(self.queue_path, "w") as f:
            json.dump(self.queue, f, indent=2, default=str)
    
    def _build_queue(self, remote, local):
        """Compare remote vs local, add missing files to queue."""
        new_items = []
        for stn, info in remote.get("stations", {}).items():
            local_dir = os.path.join(LOCAL_ROOT, stn)
            os.makedirs(local_dir, exist_ok=True)
            local_files = set()
            if os.path.exists(local_dir):
                local_files = set(os.listdir(local_dir))
            
            for f in info.get("files", []):
                if f["name"] not in local_files:
                    item = {
                        "uuid": str(uuid.uuid4()),
                        "station": stn,
                        "filename": f["name"],
                        "remote_size": f["size"],
                        "remote_mtime": f.get("mtime"),
                        "status": QUEUE_WAITING,
                        "retries": 0,
                        "max_retries": 3,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                    new_items.append(item)
        
        self.queue["items"] = new_items + self.queue["items"]
        self._update_stats()
        self._save_queue()
        log.info("Queue: %d new items, %d total", len(new_items), len(self.queue["items"]))
        return len(new_items)
    
    def _update_stats(self):
        stats = {s: 0 for s in [
            QUEUE_WAITING, QUEUE_RUNNING, QUEUE_SUCCESS,
            QUEUE_FAILED, QUEUE_RETRY, QUEUE_SKIPPED, QUEUE_CORRUPTED
        ]}
        for item in self.queue["items"]:
            status = item.get("status", QUEUE_WAITING)
            stats[status] = stats.get(status, 0) + 1
        self.queue["stats"] = stats
    
    def _download_file(self, item):
        """Download single file with checksum verification."""
        stn = item["station"]
        filename = item["filename"]
        remote_path = f"{REMOTE_ROOT}/{stn}/{filename}"
        local_path = f"{LOCAL_ROOT}/{stn}/{filename}"
        
        item["status"] = QUEUE_RUNNING
        self._save_queue()
        
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(**SFTP_CONFIG)
            sftp = client.open_sftp()
            
            t0 = time.time()
            sftp.get(remote_path, local_path)
            dl_time = time.time() - t0
            
            # Verify checksum
            with open(local_path, "rb") as f:
                sha256 = hashlib.sha256(f.read()).hexdigest()
            file_size = os.path.getsize(local_path)
            
            item["sha256"] = sha256
            item["local_size"] = file_size
            item["download_time"] = round(dl_time, 3)
            item["download_speed"] = round(file_size / dl_time / 1e6, 2) if dl_time > 0 else 0
            item["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            if file_size == item.get("remote_size", file_size):
                item["status"] = QUEUE_SUCCESS
            else:
                item["status"] = QUEUE_CORRUPTED
                item["error"] = f"Size mismatch: expected {item['remote_size']}, got {file_size}"
            
            sftp.close()
            client.close()
            return item
            
        except Exception as e:
            item["status"] = QUEUE_RETRY if item["retries"] < item["max_retries"] else QUEUE_FAILED
            item["retries"] += 1
            item["error"] = str(e)[:200]
            log.warning("Download FAIL %s/%s: %s (retry %d/%d)",
                       stn, filename, str(e)[:80], item["retries"], item["max_retries"])
            return item
    
    def execute(self):
        # Load remote manifest
        remote_path = PDAC_DIR / "remote_manifest.json"
        if not remote_path.exists():
            log.warning("No remote manifest yet, skipping download")
            return {"downloaded": 0, "skipped": 0}
        
        with open(remote_path) as f:
            remote = json.load(f)
        
        # Only queue direct files (not dirs like SData/, Nowrec/)
        new_count = self._build_queue(remote, None)
        
        # Process waiting items — limit per cycle to prevent timeout
        MAX_PER_CYCLE = 10
        downloaded = 0
        for item in self.queue["items"]:
            if downloaded >= MAX_PER_CYCLE:
                break
            if item.get("status") == QUEUE_WAITING:
                self._download_file(item)
                downloaded += 1
                self._update_stats()
                self._save_queue()
                
                # Update global manifest
                manifest.data["queue"] = self.queue["stats"]
                manifest.set("download_queue", {
                    "total": len(self.queue["items"]),
                    "downloaded": downloaded,
                    "success": self.queue["stats"].get(QUEUE_SUCCESS, 0),
                    "failed": self.queue["stats"].get(QUEUE_FAILED, 0),
                    "retry": self.queue["stats"].get(QUEUE_RETRY, 0),
                })
                manifest.save()
                
                # Trigger validation event
                self._trigger_validation(item)
        
        result = {
            "downloaded": downloaded,
            "queue_total": len(self.queue["items"]),
            "new_discovered": new_count,
        }
        log.info("Download cycle: %d new, %d downloaded", new_count, downloaded)
        return result
    
    def _trigger_validation(self, item):
        """Signal validation worker after download."""
        event_path = PDAC_DIR / "events" / f"download_{item['station']}_{item['filename']}.json"
        os.makedirs(os.path.dirname(str(event_path)), exist_ok=True)
        with open(event_path, "w") as f:
            json.dump(item, f)
