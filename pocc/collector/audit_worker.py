#!/usr/bin/env python3
"""
Phase 9+10+14: Audit Worker — Hourly/daily/weekly reports and health metrics.
"""
import os, sys, json, time, logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collector.scheduler_engine import BaseWorker, manifest, PDAC_DIR

log = logging.getLogger("audit")

class AuditWorker(BaseWorker):
    """Hourly audit: compares remote vs local, generates reports."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_hourly = None
        self.last_daily = None
    
    def execute(self):
        now = datetime.now(timezone.utc)
        hour_key = now.strftime("%Y-%m-%d-%H")
        day_key = now.strftime("%Y-%m-%d")
        
        result = {}
        
        # Hourly audit
        if hour_key != self.last_hourly:
            result["hourly"] = self._hourly_audit()
            self.last_hourly = hour_key
        
        # Daily audit
        if day_key != self.last_daily and now.hour == 0 and now.minute < 15:
            result["daily"] = self._daily_report()
            self.last_daily = day_key
        
        # Weekly audit (Sunday)
        if now.weekday() == 6 and now.hour == 1 and self.last_daily != day_key:
            result["weekly"] = self._weekly_report()
        
        # Health metrics
        result["health"] = self._update_health()
        
        return result
    
    def _hourly_audit(self):
        """Compare remote vs local inventory."""
        remote_path = PDAC_DIR / "remote_manifest.json"
        report = {"remote_files": 0, "local_files": 0, "missing": 0, "stations": {}}
        
        if not remote_path.exists():
            return report
        
        with open(remote_path) as f:
            remote = json.load(f)
        
        for stn in remote.get("stations", {}):
            local_dir = os.path.join("/opt/pimes/data/raw", stn)
            local_files = set(os.listdir(local_dir)) if os.path.exists(local_dir) else set()
            remote_files = {f["name"] for f in remote["stations"][stn].get("files", [])}
            missing = remote_files - local_files
            
            report["stations"][stn] = {
                "remote": len(remote_files),
                "local": len(local_files),
                "missing": len(missing),
                "missing_files": list(missing)[:10],
            }
            report["remote_files"] += len(remote_files)
            report["local_files"] += len(local_files)
            report["missing"] += len(missing)
        
        # Save
        path = PDAC_DIR / "hourly_audit.json"
        with open(path, "w") as f:
            json.dump(report, f, indent=2)
        
        # Update manifest
        manifest.set("health", manifest.get("health", {}))
        manifest.get("health", {})["missing_files"] = report["missing"]
        manifest.save()
        
        log.info("Hourly audit: %d remote, %d local, %d missing",
                report["remote_files"], report["local_files"], report["missing"])
        return report
    
    def _daily_report(self):
        """Generate daily collector report."""
        report = {
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "queue_stats": manifest.get("queue", {}),
            "health": manifest.get("health", {}),
            "remote": manifest.get("remote", {}),
        }
        
        path = PDAC_DIR / f"daily_{report['date']}.json"
        with open(path, "w") as f:
            json.dump(report, f, indent=2)
        
        # Generate markdown report
        md_path = PDAC_DIR / f"COLLECTOR_REPORT_{report['date']}.md"
        with open(md_path, "w") as f:
            f.write(f"# Collector Report — {report['date']}\n\n")
            f.write(f"## Queue Status\n")
            for k, v in report["queue_stats"].items():
                f.write(f"- **{k}**: {v}\n")
            f.write(f"\n## Health\n")
            for k, v in report["health"].items():
                f.write(f"- **{k}**: {v}\n")
        
        log.info("Daily report generated: %s", report["date"])
        return report
    
    def _weekly_report(self):
        """Weekly collector health summary."""
        report = {
            "week": datetime.now(timezone.utc).strftime("%Y-W%V"),
            "availability": manifest.get("health", {}).get("availability", 1.0),
            "total_downloads": manifest.get("queue", {}).get("success", 0),
            "total_failures": manifest.get("queue", {}).get("failed", 0),
        }
        
        path = PDAC_DIR / f"weekly_{report['week']}.json"
        with open(path, "w") as f:
            json.dump(report, f, indent=2)
        
        log.info("Weekly report: %s", report["week"])
        return report
    
    def _update_health(self):
        """Update collector health metrics."""
        health = manifest.get("health", {})
        
        # Calculate availability from queue stats
        queue = manifest.get("queue", {})
        total = sum(queue.values()) if any(q > 0 for q in queue.values()) else 1
        failed = queue.get("FAILED", 0) + queue.get("CORRUPTED", 0)
        health["failure_rate"] = round(failed / total, 4) if total > 0 else 0
        health["availability"] = round(1 - health["failure_rate"], 4)
        
        manifest.save()
        return health
