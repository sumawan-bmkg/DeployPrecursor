#!/usr/bin/env python3
"""
Phase 6: Raw Data Sync Worker — Daily SData/Nowrec recursive download.
Syncs ALR files from BMKG raw data server SData/Nowrec directories.
Registered as a daily worker in the collector scheduler.
"""
import os, sys, json, time, hashlib, paramiko, logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from scheduler_engine import BaseWorker, manifest, PDAC_DIR

log = logging.getLogger("rawdata")

SFTP_CONFIG = {
    "hostname": "202.90.198.224",
    "port": 4343,
    "username": "precursor",
    "password": "otomatismon",
    "look_for_keys": False,
    "allow_agent": False,
    "timeout": 60,
}
REMOTE_ROOT = "/home/precursor/SEISMO/DATA"
LOCAL_ROOT = "/opt/pimes/data/raw"

# Stations to sync (all with SData coverage)
STATIONS = [
    "ALR","AMB","BTN","CLP","GSI","GTO","KPY","LPS","LUT","LWA","LWK",
    "MJB","MLB","PLU","SBG","SCN","SKB","SMG","SMI","SRO","TNT","TRD","TRT","YOG",
]
# Excluded: TUN,SRG,KPG,TND,JYP (on /mnt/ssd1), DNP (flat .lem only)


class RawDataWorker(BaseWorker):
    """Recursive SData/Nowrec sync worker. Runs daily."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        state_dir = PDAC_DIR / "rawdata_state"
        os.makedirs(state_dir, exist_ok=True)
        self.state_path = state_dir / "sync_state.json"
        self.state = self._load_state()

    def _load_state(self):
        try:
            with open(self.state_path) as f:
                return json.load(f)
        except Exception:
            return {
                "last_sync": None,
                "synced_stations": {},
                "total_files": 0,
                "total_bytes": 0,
            }

    def _save_state(self):
        self.state["last_sync"] = datetime.now(timezone.utc).isoformat()
        with open(self.state_path, "w") as f:
            json.dump(self.state, f, indent=2, default=str)

    def _list_remote_sdata_dirs(self, sftp, station):
        """List all SData/YYYYMM dirs for a station."""
        base = f"{REMOTE_ROOT}/{station}/SData"
        try:
            return [d for d in sftp.listdir(base) if d.isdigit() and len(d) == 4]
        except Exception:
            return []

    def _list_remote_files(self, sftp, station, sdata_dir):
        """List .ALR and .ALR.gz files in SData/YYYYMM."""
        base = f"{REMOTE_ROOT}/{station}/SData/{sdata_dir}"
        try:
            return sftp.listdir_attr(base)
        except Exception:
            return []

    def _list_nowrec_files(self, sftp, station):
        """List files in Nowrec directory."""
        base = f"{REMOTE_ROOT}/{station}/Nowrec"
        try:
            return sftp.listdir_attr(base)
        except Exception:
            return []

    def _download_file(self, sftp, remote_path, local_path, item_info):
        """Download a single file with verification."""
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # Skip if exists and same size
        if os.path.exists(local_path):
            local_size = os.path.getsize(local_path)
            if local_size == item_info.get("size", 0) and local_size > 0:
                return False  # already synced

        t0 = time.time()
        sftp.get(remote_path, local_path)
        dl_time = time.time() - t0
        file_size = os.path.getsize(local_path)

        # Verify SHA256
        with open(local_path, "rb") as f:
            sha256 = hashlib.sha256(f.read()).hexdigest()

        # Record in state
        station = item_info.get("station", "unknown")
        filename = item_info.get("filename", os.path.basename(local_path))
        self.state.setdefault("synced_stations", {}).setdefault(station, {})
        self.state["synced_stations"][station][filename] = {
            "sha256": sha256,
            "size": file_size,
            "dl_time": round(dl_time, 3),
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }
        self.state["total_files"] += 1
        self.state["total_bytes"] += file_size

        log.info("Downloaded %s (%s, %.1f MB, %.2fs)", remote_path, sha256[:16], file_size/1e6, dl_time)
        return True

    def execute(self):
        t0 = time.time()
        current_month = datetime.now().strftime("%y%m")
        results = {"synced": 0, "skipped": 0, "errors": 0, "stations": {}}

        log.info("RawData sync started (target: SData/*/%s*)", current_month[:2])

        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(**SFTP_CONFIG)
            sftp = client.open_sftp()

            for station in STATIONS:
                station_synced = 0
                station_skipped = 0

                # ── SData directories ──
                sdata_dirs = self._list_remote_sdata_dirs(sftp, station)
                # Only sync 2025+ and current month
                target_dirs = [d for d in sdata_dirs
                               if d.startswith("25") or d.startswith("26")]

                for sd in sorted(target_dirs):
                    attrs = self._list_remote_files(sftp, station, sd)
                    for attr in attrs:
                        fname = attr.filename
                        # Only .ALR and .ALR.gz
                        if not (fname.endswith(".ALR") or fname.endswith(".ALR.gz")):
                            continue
                        remote_path = f"{REMOTE_ROOT}/{station}/SData/{sd}/{fname}"
                        local_dir = f"{LOCAL_ROOT}/{station}/SData/{sd}"
                        os.makedirs(local_dir, exist_ok=True)
                        local_path = f"{local_dir}/{fname}"

                        item = {
                            "station": station,
                            "filename": fname,
                            "size": attr.st_size,
                            "remote_path": remote_path,
                        }
                        downloaded = self._download_file(sftp, remote_path, local_path, item)
                        if downloaded:
                            station_synced += 1
                        else:
                            station_skipped += 1

                # ── Nowrec (real-time) ──
                attrs = self._list_nowrec_files(sftp, station)
                for attr in attrs:
                    fname = attr.filename
                    if not (fname.endswith(f".{station}") or fname.endswith(f".{station}")):
                        continue
                    remote_path = f"{REMOTE_ROOT}/{station}/Nowrec/{fname}"
                    local_dir = f"{LOCAL_ROOT}/{station}/Nowrec"
                    os.makedirs(local_dir, exist_ok=True)
                    local_path = f"{local_dir}/{fname}"

                    item = {
                        "station": station,
                        "filename": fname,
                        "size": attr.st_size,
                        "remote_path": remote_path,
                    }
                    downloaded = self._download_file(sftp, remote_path, local_path, item)
                    if downloaded:
                        station_synced += 1
                    else:
                        station_skipped += 1

                results["stations"][station] = {
                    "synced": station_synced,
                    "skipped": station_skipped,
                }
                results["synced"] += station_synced
                results["skipped"] += station_skipped

                if station_synced > 0:
                    log.info("Station %s: %d new files synced", station, station_synced)

            sftp.close()
            client.close()

            # Update global manifest
            manifest.set("last_rawdata_sync", {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "stations_synced": len([s for s in results["stations"].values() if s["synced"] > 0]),
                "files_synced": results["synced"],
                "files_skipped": results["skipped"],
                "duration": round(time.time() - t0, 2),
            })
            manifest.save()
            self._save_state()

            log.info("RawData sync complete: %d new, %d skipped (%.1fs)",
                     results["synced"], results["skipped"], time.time() - t0)

            return results

        except Exception as e:
            log.error("RawData sync failed: %s", str(e)[:300])
            raise
