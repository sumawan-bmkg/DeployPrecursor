"""
Operational Playbook Engine — Sprint 3
Diagnosis → Evidence → Causes → Recommendations → Verification.
"""
import json, uuid, time, re
from pathlib import Path
from datetime import datetime, timezone
from collections import deque

PDAC = Path("/opt/pimes/laws/runtime/validation/pdac")
OIE_DIR = PDAC / "operational_intelligence"

# ── Playbook Rules ──────────────────────────────────────
PLAYBOOKS = {
    "collector_queue_high": {
        "name": "Collector Queue Buildup",
        "severity": ["HIGH", "WARNING"],
        "diagnosis": "Download queue growing faster than processing rate",
        "evidence_keys": ["queue_length", "retry_count", "worker_latency"],
        "possible_causes": [
            "Remote server latency increase",
            "FTP/SFTP connection degraded",
            "Worker thread stalled",
            "Bandwidth saturation",
            "Too many retry jobs",
        ],
        "verification_steps": [
            "Check remote server ping latency",
            "Verify FTP credentials on remote_manifest",
            "Check worker heartbeat timestamps",
            "Review scheduler.log for timeout errors",
        ],
        "recommended_actions": [
            ("Restart Download Worker", "restart"),
            ("Retry Failed Jobs", "retry"),
            ("Verify Remote Connectivity", "validate"),
            ("Increase Worker Interval", "configure"),
        ],
        "expected_result": "Queue drains within 2 cycles",
        "risk": "LOW - Download will resume automatically",
        "rollback": "Resume normal schedule",
    },
    "scheduler_not_running": {
        "name": "Scheduler Process Down",
        "severity": ["CRITICAL"],
        "diagnosis": "Collector scheduler process not detected in process table",
        "evidence_keys": ["process_check", "last_heartbeat"],
        "possible_causes": [
            "Process crashed (OOM or signal)",
            "Python runtime error",
            "Log file write failure",
            "Manual kill not restored",
        ],
        "verification_steps": [
            "Check process table for python",
            "Inspect scheduler.log tail for crash",
            "Verify disk space on PDAC",
            "Check OOM killer logs (dmesg)",
        ],
        "recommended_actions": [
            ("Restart Scheduler", "restart"),
            ("Check System Logs", "system"),
            ("Verify Python Environment", "validate"),
            ("Monitor Next 5 Minutes", "configure"),
        ],
        "expected_result": "Scheduler resumes and workers start within 30s",
        "risk": "HIGH - No data collection while down",
        "rollback": "Manual restart via terminal",
    },
    "runtime_stale": {
        "name": "Runtime Pipeline Stalled",
        "severity": ["HIGH", "CRITICAL"],
        "diagnosis": "No recent activity in runtime pipeline",
        "evidence_keys": ["last_log_time", "rdmc_log_age"],
        "possible_causes": [
            "Pipeline blocked at inference stage",
            "Tensor computation timeout",
            "Memory exhaustion in runtime",
            "File descriptor leak",
        ],
        "verification_steps": [
            "Check rdmc.log timestamp",
            "Verify runtime process alive",
            "Check memory usage (free -m)",
            "Check file descriptors (lsof)",
        ],
        "recommended_actions": [
            ("Restart Runtime Pipeline", "restart"),
            ("Monitor Memory Usage", "system"),
            ("Check Tensor Flow", "validate"),
            ("Review Inference Logs", "system"),
        ],
        "expected_result": "Pipeline processing resumes",
        "risk": "HIGH - Affects all downstream",
        "rollback": "Restart from checkpoint",
    },
    "memory_growth": {
        "name": "Memory Usage Trend Up",
        "severity": ["WARNING", "HIGH"],
        "diagnosis": "Memory consumption increasing across burn-in cycles",
        "evidence_keys": ["memory_trend", "memory_current", "memory_peak"],
        "possible_causes": [
            "Gradual memory leak in runtime",
            "Tensor cache not clearing",
            "Too many open file handles",
            "Python object accumulation",
        ],
        "verification_steps": [
            "Compare memory across last 5 burn-in cycles",
            "Check per-process RSS (ps aux)",
            "Verify GC is running (gc.get_count)",
            "Check for unclosed file handles",
        ],
        "recommended_actions": [
            ("Restart Runtime to Clear Memory", "restart"),
            ("Monitor Memory Trend", "system"),
            ("Verify GC Configuration", "configure"),
            ("Schedule Maintenance Window", "configure"),
        ],
        "expected_result": "Memory stabilizes after restart",
        "risk": "MEDIUM - System crash if memory exhausted",
        "rollback": "Restart with memory limit",
    },
    "scientific_drift": {
        "name": "Scientific Score Degradation",
        "severity": ["HIGH"],
        "diagnosis": "Scientific equivalence score decreasing over time",
        "evidence_keys": ["score_current", "score_trend", "hash_comparison"],
        "possible_causes": [
            "Tensor computation precision drift",
            "Pipeline hash mismatch",
            "Data preprocessing variation",
            "Model checkpoint inconsistency",
        ],
        "verification_steps": [
            "Compare latest 3 PSEP scores",
            "Verify pipeline fingerprints match",
            "Check tensor hash consistency",
            "Review scientific certificate chain",
        ],
        "recommended_actions": [
            ("Run PSEP Full Validation", "validate"),
            ("Compare Pipeline Fingerprint", "validate"),
            ("Review Scientific Certificates", "evidence"),
            ("Escalate to Science Team", "configure"),
        ],
        "expected_result": "Score stabilizes or root cause identified",
        "risk": "HIGH - Affects RC certification",
        "rollback": "Revert to previous checkpoint",
    },
}


class PlaybookEngine:
    """Operational Playbook — anomaly to action."""
    
    def __init__(self):
        self.decisions = deque(maxlen=500)
        self._load()
    
    def _load(self):
        dp = OIE_DIR / "decisions.json"
        if dp.exists():
            try: self.decisions = deque(json.loads(dp.read_text()), maxlen=500)
            except: pass
    
    def _save(self):
        (OIE_DIR / "decisions.json").write_text(
            json.dumps(list(self.decisions)[-100:], indent=2, default=str))
    
    def diagnose(self, anomaly: dict) -> dict:
        """Match anomaly to playbook and return full diagnosis."""
        title = anomaly.get("title", "")
        component = anomaly.get("component", "")
        
        # Find matching playbook
        matched = None
        for key, playbook in PLAYBOOKS.items():
            if key in title.lower().replace(" ", "_") or component in key:
                matched = playbook
                break
        
        if not matched:
            matched = {
                "name": f"Unknown: {title}",
                "severity": [anomaly.get("severity", "INFO")],
                "diagnosis": "No matching playbook",
                "possible_causes": ["Unknown cause - manual investigation required"],
                "verification_steps": ["Check system logs manually"],
                "recommended_actions": [("Manual Investigation", "system")],
                "expected_result": "Investigation needed",
                "risk": "UNKNOWN",
                "rollback": "Manual rollback",
            }
        
        # Build evidence summary
        evidence = {}
        for key in matched.get("evidence_keys", []):
            if key in anomaly:
                evidence[key] = anomaly[key]
        
        # Collect live data for evidence
        if "queue_length" in matched.get("evidence_keys", []):
            try:
                mf = PDAC / "collector_manifest.json"
                if mf.exists():
                    d = json.loads(mf.read_text())
                    q = d.get("queue", {})
                    evidence["queue_length"] = sum(q.values())
                    evidence["retry_count"] = q.get("RETRY", 0)
            except: pass
        
        if "process_check" in matched.get("evidence_keys", []):
            import subprocess
            try:
                r = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=5)
                evidence["scheduler_alive"] = "_run_scheduler" in r.stdout or "CollectorScheduler" in r.stdout
            except: evidence["scheduler_alive"] = False
        
        entry = {
            "uuid": str(uuid.uuid4())[:12],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "anomaly_uuid": anomaly.get("uuid", ""),
            "playbook": matched["name"],
            "diagnosis": matched["diagnosis"],
            "evidence": evidence,
            "possible_causes": matched["possible_causes"],
            "verification_steps": matched["verification_steps"],
            "recommended_actions": matched["recommended_actions"],
            "expected_result": matched["expected_result"],
            "risk": matched["risk"],
            "rollback": matched["rollback"],
            "operator_action": None,
            "operator_notes": "",
            "status": "OPEN",
        }
        
        self.decisions.append(entry)
        self._save()
        return entry
    
    def act(self, decision_uuid: str, action: str, operator: str = "dashboard") -> dict:
        """Record operator action for a decision."""
        for d in self.decisions:
            if d.get("uuid") == decision_uuid:
                d["operator_action"] = action
                d["operator_name"] = operator
                d["status"] = "ACTIONED"
                d["actioned_at"] = datetime.now(timezone.utc).isoformat()
                break
        self._save()
        return {"status": "recorded"}
    
    def resolve(self, decision_uuid: str, notes: str = "") -> dict:
        for d in self.decisions:
            if d.get("uuid") == decision_uuid:
                d["status"] = "RESOLVED"
                d["operator_notes"] = notes
                d["resolved_at"] = datetime.now(timezone.utc).isoformat()
                break
        self._save()
        return {"status": "resolved"}
    
    def list(self, limit: int = 50) -> list:
        return list(self.decisions)[-limit:]


playbook = PlaybookEngine()
