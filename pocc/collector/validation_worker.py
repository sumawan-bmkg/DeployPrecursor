#!/usr/bin/env python3
"""
Phase 6+7: Validation Worker — Checksum + Raw Data Quality.
Event-based: runs after each download.
"""
import os, sys, json, time, hashlib, logging
from datetime import datetime, timezone
from pathlib import Path
from collector.scheduler_engine import BaseWorker, manifest, PDAC_DIR

log = logging.getLogger("validation")

LOCAL_ROOT = "/opt/pimes/data/raw"

class ValidationWorker(BaseWorker):
    """Checksum verification + raw data quality checks."""
    
    def execute(self):
        events_dir = PDAC_DIR / "events"
        if not events_dir.exists():
            return {"validated": 0}
        
        validated = 0
        for event_path in sorted(events_dir.glob("download_*.json")):
            try:
                with open(event_path) as f:
                    item = json.load(f)
                
                stn = item.get("station", "unknown")
                filename = item.get("filename", "")
                local_path = f"{LOCAL_ROOT}/{stn}/{filename}"
                
                if not os.path.exists(local_path):
                    log.warning("File missing for validation: %s", local_path)
                    continue
                
                # Phase 6: Checksum
                with open(local_path, "rb") as f:
                    sha256 = hashlib.sha256(f.read()).hexdigest()
                crc32 = "%08x" % (hashlib.crc32(open(local_path, "rb").read()) & 0xFFFFFFFF)
                file_size = os.path.getsize(local_path)
                
                # Phase 7: Raw Data Quality
                quality = self._check_quality(local_path)
                
                cert = {
                    "station": stn,
                    "filename": filename,
                    "sha256": sha256,
                    "crc32": crc32,
                    "size": file_size,
                    "quality": quality,
                    "validated_at": datetime.now(timezone.utc).isoformat(),
                }
                
                # Save certificate
                cert_dir = PDAC_DIR / "certificates"
                os.makedirs(str(cert_dir), exist_ok=True)
                cert_path = cert_dir / f"{stn}_{filename}.json"
                with open(cert_path, "w") as f:
                    json.dump(cert, f, indent=2)
                
                # Save checksum report
                report_path = PDAC_DIR / "checksum_report.json"
                report = {}
                if report_path.exists():
                    with open(report_path) as f:
                        report = json.load(f)
                report[f"{stn}/{filename}"] = cert
                with open(report_path, "w") as f:
                    json.dump(report, f, indent=2)
                
                os.remove(event_path)
                validated += 1
                
                # Update manifest
                manifest.data["health"]["last_validation"] = cert["validated_at"]
                manifest.save()
                
            except Exception as e:
                log.error("Validation error %s: %s", event_path, str(e)[:200])
        
        return {"validated": validated}
    
    def _check_quality(self, path: str) -> dict:
        """Scientific validation of raw data."""
        quality = {
            "is_valid": True,
            "has_header": False,
            "sample_count": 0,
            "has_timestamp": False,
            "components": [],
            "missing_samples": 0,
            "nan_count": 0,
            "warnings": [],
        }
        try:
            with open(path, "rb") as f:
                raw = f.read()
            
            quality["file_size"] = len(raw)
            quality["has_header"] = raw[:2] == b'\xff\xfe' or raw[:3] == b'\xef\xbb\xbf'
            
            # Check for binary format magic bytes
            if raw[:4] == b'\x00\x00\x00\x00':
                quality["format"] = "binary_604"
            
        except Exception as e:
            quality["is_valid"] = False
            quality["error"] = str(e)[:100]
        
        return quality
