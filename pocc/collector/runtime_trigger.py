#!/usr/bin/env python3
"""
Phase 8: Runtime Trigger — Auto-trigger RuntimeKernel after new data.
"""
import os, sys, json, time, subprocess, logging
from datetime import datetime, timezone
from pathlib import Path
from scheduler_engine import BaseWorker, manifest, PDAC_DIR

log = logging.getLogger("runtime_trigger")

RUNTIME_ROOT = "/opt/pimes/laws/runtime"
VENV_PYTHON = "/opt/pimes/laws/runtime/.venv/bin/python"

class RuntimeTriggerWorker(BaseWorker):
    """Triggers RuntimeKernel when new validated data arrives."""
    
    def execute(self):
        cert_dir = PDAC_DIR / "certificates"
        if not cert_dir.exists():
            return {"triggered": 0}
        
        triggered = 0
        for cert_path in sorted(cert_dir.glob("*.json")):
            try:
                with open(cert_path) as f:
                    cert = json.load(f)
                
                stn = cert.get("station", "unknown")
                filename = cert.get("filename", "")
                
                # Skip invalid data
                if not cert.get("quality", {}).get("is_valid", False):
                    log.warning("SKIP invalid: %s/%s", stn, filename)
                    continue
                
                # Trigger RuntimeKernel
                log.info("TRIGGER RuntimeKernel: %s/%s", stn, filename)
                result = self._run_pipeline(stn, filename)
                
                # Save trigger evidence
                trigger_dir = PDAC_DIR / "triggers"
                os.makedirs(str(trigger_dir), exist_ok=True)
                trigger_path = trigger_dir / f"{stn}_{filename.replace('.','_')}.json"
                with open(trigger_path, "w") as f:
                    json.dump({
                        "station": stn,
                        "filename": filename,
                        "triggered_at": datetime.now(timezone.utc).isoformat(),
                        "result": result,
                    }, f, indent=2)
                
                os.remove(cert_path)
                triggered += 1
                
            except Exception as e:
                log.error("Trigger error %s: %s", cert_path, str(e)[:200])
        
        if triggered:
            manifest.set("last_runtime_trigger", datetime.now(timezone.utc).isoformat())
            manifest.save()
        
        return {"triggered": triggered}
    
    def _run_pipeline(self, station: str, filename: str) -> dict:
        """Call PSEP dual_execution for this station."""
        try:
            cmd = [
                VENV_PYTHON, "-m", "validation.psep.dual_orchestrator",
                "--station", station,
                "--date", filename.replace(".", "").replace("S", "")[:6],  # S260611 → 260611
            ]
            # Parse date from filename S260611.ALR → 2026-06-11
            raw = filename.replace("S", "").split(".")[0]  # "260611"
            year = "20" + raw[:2]
            month = raw[2:4]
            day = raw[4:6]
            date_str = f"{year}-{month}-{day}"
            
            env = os.environ.copy()
            env["PYTHONPATH"] = "/opt/pimes/laws/runtime:/opt/pimes/laws/preprocessing_bundle/core"
            
            result = subprocess.run(
                [VENV_PYTHON, "-m", "validation.psep.dual_orchestrator",
                 "--station", station, "--date", date_str],
                capture_output=True, text=True, timeout=300, cwd=RUNTIME_ROOT, env=env
            )
            
            return {
                "stdout": result.stdout[-500:],
                "stderr": result.stderr[-200:],
                "returncode": result.returncode,
            }
        except Exception as e:
            return {"error": str(e)[:200]}
