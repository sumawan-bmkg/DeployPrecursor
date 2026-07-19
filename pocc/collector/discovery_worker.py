#!/usr/bin/env python3
"""
Phase 2+3: Discovery Worker — Remote server inventory.
Scans SFTP server every 5 minutes. Does NOT download.
"""
import os, sys, json, time, hashlib, paramiko, logging
from datetime import datetime, timezone
from pathlib import Path
from collector.scheduler_engine import BaseWorker, manifest, PDAC_DIR

log = logging.getLogger("discovery")

SFTP_CONFIG = {
    "hostname": "202.90.198.224",
    "port": 4343,
    "username": "precursor",
    "password": "otomatismon",
    "look_for_keys": False,
    "allow_agent": False,
    "timeout": 15,
}
REMOTE_ROOT = "/home/precursor/SEISMO/DATA"

class DiscoveryWorker(BaseWorker):
    """Recursive remote scanner. Updates remote_manifest.json."""
    
    def execute(self):
        t0 = time.time()
        result = {"timestamp": datetime.now(timezone.utc).isoformat(), "stations": {}}
        
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(**SFTP_CONFIG)
            sftp = client.open_sftp()
            
            # List stations
            stations = sftp.listdir(REMOTE_ROOT)
            total_files = 0
            total_size = 0
            
            for stn in sorted(stations):
                stn_path = f"{REMOTE_ROOT}/{stn}"
                try:
                    stn_files = sftp.listdir_attr(stn_path)
                    files_info = []
                    for attr in stn_files:
                        # Skip subdirectories (Nowrec, SData, Format IAGA etc.)
                        if attr.longname.startswith('d'):
                            continue
                        files_info.append({
                            "name": attr.filename,
                            "size": attr.st_size,
                            "mtime": datetime.fromtimestamp(attr.st_mtime).isoformat() if attr.st_mtime else None,
                        })
                        total_files += 1
                        total_size += attr.st_size
                    
                    result["stations"][stn] = {
                        "files_count": len(files_info),
                        "total_size": sum(f["size"] for f in files_info),
                        "latest_file": max(files_info, key=lambda f: f["mtime"]) if files_info else None,
                        "oldest_file": min(files_info, key=lambda f: f["mtime"]) if files_info else None,
                        "files": files_info,
                    }
                except Exception as e:
                    log.warning("  SKIP %s: %s", stn, str(e)[:80])
            
            sftp.close()
            client.close()
            
            result["total_stations"] = len(result["stations"])
            result["total_files"] = total_files
            result["total_size_gb"] = round(total_size / 1e9, 2)
            result["latency"] = round(time.time() - t0, 3)
            
            # Save manifest
            path = PDAC_DIR / "remote_manifest.json"
            with open(path, "w") as f:
                json.dump(result, f, indent=2, default=str)
            
            # Update global manifest
            manifest.set("remote", {
                "stations": result["total_stations"],
                "files": total_files,
                "size_gb": result["total_size_gb"],
                "last_discovery": result["timestamp"],
                "latency": result["latency"],
            })
            manifest.set("last_discovery", result)
            manifest.save()
            
            log.info("Discovered %d stations, %d files, %.1f GB (%.2fs)",
                     result["total_stations"], total_files, result["total_size_gb"], result["latency"])
            return result
            
        except Exception as e:
            log.error("Discovery failed: %s", str(e)[:200])
            raise
    
    def stop(self):
        super().stop()
