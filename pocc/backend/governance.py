"""
BOCC Governance Layer — Command State Machine, RBAC, Verification, Audit, Evidence.
Offline-built for one-shot deploy when server returns.
"""
import json, os, uuid, time, subprocess, hashlib, shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import deque

# ── Paths ───────────────────────────────────────────────
PDAC_DIR = Path("/opt/pimes/laws/runtime/validation/pdac")
GOV_DIR = PDAC_DIR / "governance"
EVIDENCE_DIR = GOV_DIR / "evidence"
os.makedirs(GOV_DIR, exist_ok=True)
os.makedirs(EVIDENCE_DIR, exist_ok=True)

# ── Command State Machine ──────────────────────────────
COMMAND_STATES = [
    "REQUESTED", "AUTHORIZED", "QUEUED", "RUNNING",
    "VERIFYING", "SUCCESS", "FAILED", "REJECTED", "CANCELLED"
]

VERIFIABLE_ACTIONS = ["discover", "download", "validate", "trigger",
                       "pause", "resume", "stop", "restart", "retry",
                       "shadow_start", "shadow_stop"]

# ── Roles ──────────────────────────────────────────────
ROLES = {
    "viewer":        ["list", "read"],
    "operator":      ["list", "read", "request"],
    "supervisor":    ["list", "read", "request", "approve", "reject"],
    "administrator": ["list", "read", "request", "approve", "reject",
                       "execute", "emergency", "delete"],
    "ev_reviewer":   ["list", "read", "verify", "evidence"],
    "release_mgr":   ["list", "read", "approve", "reject",
                       "release", "evidence"],
}

DEFAULT_ROLE = "viewer"
SESSIONS = {}  # token -> {role, name}

# ── Command Record ─────────────────────────────────────
class Command:
    def __init__(self, action: str, operator: str = "dashboard",
                 role: str = "administrator", params: dict = None,
                 reason: str = "", ticket: str = ""):
        self.uuid = str(uuid.uuid4())[:12]
        self.action = action
        self.operator = operator
        self.role = role
        self.state = "REQUESTED"
        self.params = params or {}
        self.reason = reason
        self.ticket = ticket
        self.pid = None
        self.timestamps = {"REQUESTED": datetime.now(timezone.utc).isoformat()}
        self.duration = 0
        self.exit_code = None
        self.logs = ""
        self.verification = {}
        self.host = "pocc"
        self.pipeline_uuid = str(uuid.uuid4())[:8]
    
    def transition(self, new_state: str):
        if new_state in COMMAND_STATES:
            self.state = new_state
            self.timestamps[new_state] = datetime.now(timezone.utc).isoformat()
            if new_state in ("SUCCESS", "FAILED"):
                t0 = datetime.fromisoformat(self.timestamps.get("RUNNING",
                    self.timestamps["REQUESTED"]))
                self.duration = (datetime.now(timezone.utc) - t0).total_seconds()
    
    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}
    
    def save(self):
        path = GOV_DIR / f"cmd_{self.uuid}.json"
        path.write_text(json.dumps(self.to_dict(), indent=2, default=str))

# ── Governance Engine ──────────────────────────────────
class GovernanceEngine:
    def __init__(self):
        self.commands: dict = {}  # uuid -> Command
        self._load()
    
    def _load(self):
        for f in sorted(GOV_DIR.glob("cmd_*.json")):
            try:
                d = json.loads(f.read_text())
                cmd = Command.__new__(Command)
                cmd.__dict__.update(d)
                self.commands[cmd.uuid] = cmd
            except: pass
    
    def request(self, action: str, operator: str = "dashboard",
                role: str = "administrator", params: dict = None,
                reason: str = "", ticket: str = "") -> tuple:
        """Returns (command, requires_approval)."""
        cmd = Command(action, operator, role, params, reason, ticket)
        requires = action in ("restart", "stop", "shadow_start", "shadow_stop")
        cmd.state = "REQUESTED" if requires else "AUTHORIZED"
        cmd.timestamps[cmd.state] = datetime.now(timezone.utc).isoformat()
        self.commands[cmd.uuid] = cmd
        cmd.save()
        self._save_index()
        return cmd, requires
    
    def approve(self, cmd_uuid: str, approver: str = "supervisor"):
        cmd = self.commands.get(cmd_uuid)
        if not cmd: return None
        cmd.transition("AUTHORIZED")
        cmd.save()
        self._save_index()
        return cmd
    
    def reject(self, cmd_uuid: str, reason: str = ""):
        cmd = self.commands.get(cmd_uuid)
        if not cmd: return None
        cmd.transition("REJECTED")
        cmd.save()
        self._save_index()
        return cmd
    
    def execute(self, cmd_uuid: str) -> dict:
        cmd = self.commands.get(cmd_uuid)
        if not cmd: return {"error": "not found"}
        if cmd.state not in ("AUTHORIZED", "QUEUED"):
            return {"error": f"invalid state: {cmd.state}"}
        
        cmd.transition("QUEUED")
        result = self._run(cmd)
        return result
    
    def _run(self, cmd: Command) -> dict:
        cmd.transition("RUNNING")
        cmd.save()
        
        PYTHON = "/opt/pimes/laws/runtime/.venv/bin/python"
        COLLECTOR = "/opt/pimes/pocc/collector"
        result = {"action": cmd.action, "uuid": cmd.uuid, "exit_code": -1}
        
        try:
            if cmd.action == "discover":
                p = subprocess.run([PYTHON,"-c",
                    'import sys;sys.path.insert(0,"/opt/pimes/pocc/collector");'
                    'from discovery_worker import DiscoveryWorker;'
                    'from scheduler_engine import manifest;'
                    'DiscoveryWorker("gov",manifest,1).execute()'],
                    capture_output=True, text=True, timeout=120)
            elif cmd.action == "download":
                p = subprocess.run([PYTHON,"-c",
                    'import sys;sys.path.insert(0,"/opt/pimes/pocc/collector");'
                    'from download_worker import DownloadWorker;'
                    'from scheduler_engine import manifest;'
                    'DownloadWorker("gov",manifest,1).execute()'],
                    capture_output=True, text=True, timeout=300)
            elif cmd.action == "validate":
                p = subprocess.run([PYTHON,"-c",
                    'import sys;sys.path.insert(0,"/opt/pimes/pocc/collector");'
                    'from validation_worker import ValidationWorker;'
                    'from scheduler_engine import manifest;'
                    'ValidationWorker("gov",manifest,1).execute()'],
                    capture_output=True, text=True, timeout=120)
            elif cmd.action == "trigger":
                p = subprocess.run([PYTHON,"-c",
                    'import sys;sys.path.insert(0,"/opt/pimes/pocc/collector");'
                    'from runtime_trigger import RuntimeTriggerWorker;'
                    'from scheduler_engine import manifest;'
                    'RuntimeTriggerWorker("gov",manifest,1).execute()'],
                    capture_output=True, text=True, timeout=300)
            elif cmd.action == "pause":
                (PDAC_DIR/".paused").write_text(datetime.now(timezone.utc).isoformat())
                p = type('p',(),{'returncode':0,'stdout':'','stderr':''})()
            elif cmd.action == "resume":
                (PDAC_DIR/".paused").unlink(missing_ok=True)
                p = type('p',(),{'returncode':0,'stdout':'','stderr':''})()
            elif cmd.action == "stop":
                subprocess.run(["pkill","-f","_run_scheduler"],capture_output=True,timeout=10)
                subprocess.run(["pkill","-f","CollectorScheduler"],capture_output=True,timeout=10)
                p = type('p',(),{'returncode':0,'stdout':'','stderr':''})()
            elif cmd.action == "restart":
                subprocess.run(["pkill","-f","_run_scheduler"],capture_output=True,timeout=5)
                subprocess.run(["pkill","-f","CollectorScheduler"],capture_output=True,timeout=5)
                time.sleep(2)
                subprocess.Popen(["nohup",PYTHON,"-u",str(COLLECTOR/"_run_scheduler.py")],
                    stdout=open(str(PDAC_DIR/"scheduler.log"),"a"),
                    stderr=subprocess.STDOUT, cwd="/opt/pimes/pocc")
                p = type('p',(),{'returncode':0,'stdout':'','stderr':''})()
            elif cmd.action == "retry":
                qp = PDAC_DIR / "download_queue.json"
                if qp.exists():
                    qd = json.loads(qp.read_text())
                    for item in qd.get("items",[]):
                        if item.get("status")=="RETRY":
                            item["status"]="WAITING"; item["retries"]=0
                    qp.write_text(json.dumps(qd,indent=2,default=str))
                p = type('p',(),{'returncode':0,'stdout':'','stderr':''})()
            else:
                result["error"] = f"unknown action: {cmd.action}"
                cmd.transition("FAILED")
                cmd.save()
                self._save_index()
                return result
            
            exit_code = p.returncode if hasattr(p,'returncode') else 0
            cmd.exit_code = exit_code
            cmd.logs = (p.stdout or "")[:2000] + "\n" + (p.stderr or "")[:500]
            
            if exit_code == 0:
                cmd.transition("VERIFYING")
                self._verify(cmd)
            else:
                cmd.transition("FAILED")
        
        except subprocess.TimeoutExpired:
            cmd.exit_code = -10
            cmd.logs = "TIMEOUT after 120-300s"
            cmd.transition("FAILED")
        except Exception as e:
            cmd.exit_code = -1
            cmd.logs = str(e)[:500]
            cmd.transition("FAILED")
        
        cmd.save()
        self._save_index()
        self._generate_evidence(cmd)
        return cmd.to_dict()
    
    def _verify(self, cmd: Command):
        """Post-execution verification checks."""
        cmd.verification = {"checks": [], "passed": True}
        
        if cmd.action in ("restart", "resume", "start"):
            # Check scheduler process
            try:
                r = subprocess.run(["ps","aux"],capture_output=True,text=True,timeout=5)
                alive = "_run_scheduler" in r.stdout or "CollectorScheduler" in r.stdout
                cmd.verification["alive"] = alive
                cmd.verification["checks"].append({
                    "name": "scheduler_process", "passed": alive})
                if not alive: cmd.verification["passed"] = False
            except: cmd.verification["checks"].append({"name":"scheduler_process","passed":False})
        
        # Check POCC API
        try:
            r = subprocess.run(["curl","-s","-o","/dev/null","-w","%{http_code}",
                "http://127.0.0.1:8500/api/health"],capture_output=True,text=True,timeout=5)
            ok = r.stdout.strip() == "200"
            cmd.verification["api_health"] = ok
            cmd.verification["checks"].append({"name":"api_health","passed":ok})
            if not ok: cmd.verification["passed"] = False
        except: cmd.verification["checks"].append({"name":"api_health","passed":False})
        
        if cmd.verification["passed"]:
            cmd.transition("SUCCESS")
        else:
            cmd.transition("FAILED")
    
    def _generate_evidence(self, cmd: Command):
        """Create evidence package for this command."""
        ev_dir = EVIDENCE_DIR / f"ev_{cmd.uuid}"
        os.makedirs(ev_dir, exist_ok=True)
        
        # command.json
        (ev_dir/"command.json").write_text(
            json.dumps(cmd.to_dict(), indent=2, default=str))
        
        # verification.json
        (ev_dir/"verification.json").write_text(
            json.dumps(cmd.verification, indent=2))
        
        # runtime_snapshot.json
        snapshot = {"timestamp": datetime.now(timezone.utc).isoformat()}
        # Try to get scheduler log tail
        log_path = PDAC_DIR / "scheduler.log"
        if log_path.exists():
            try:
                lines = log_path.read_text().splitlines()
                snapshot["log_tail"] = "\n".join(lines[-20:])
            except: pass
        # Manifest ref
        mf_path = PDAC_DIR / "collector_manifest.json"
        if mf_path.exists():
            try: snapshot["manifest"] = json.loads(mf_path.read_text())
            except: pass
        (ev_dir/"runtime_snapshot.json").write_text(
            json.dumps(snapshot, indent=2, default=str))
        
        # manifest_reference.json (stub)
        (ev_dir/"manifest_reference.json").write_text(
            json.dumps({"evidence_uuid": cmd.uuid, "pipeline_uuid": cmd.pipeline_uuid}))
    
    def _save_index(self):
        idx = {uid: cmd.to_dict() for uid, cmd in self.commands.items()
               if cmd.state not in ("SUCCESS", "FAILED")}
        (GOV_DIR/"index.json").write_text(
            json.dumps(idx, indent=2, default=str))
    
    def get_command(self, uuid: str) -> dict:
        cmd = self.commands.get(uuid)
        return cmd.to_dict() if cmd else None
    
    def list_commands(self, limit: int = 50) -> list:
        all_cmds = sorted(self.commands.values(),
            key=lambda c: c.timestamps.get("REQUESTED",""), reverse=True)
        return [c.to_dict() for c in all_cmds[:limit]]

# ── Singleton ──────────────────────────────────────────
engine = GovernanceEngine()
