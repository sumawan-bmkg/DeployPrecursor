"""SEOS Shared Utilities."""
import json, hashlib, math, uuid, sqlite3
from datetime import datetime, timezone
from pathlib import Path

def now_iso(): return datetime.now(timezone.utc).isoformat()

def sf(v, d=0.0):
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f): return d
        return f
    except: return d

def sha256_str(s):
    return hashlib.sha256(s.encode() if isinstance(s, str) else s).hexdigest()

def new_uuid(): return str(uuid.uuid4())

def ssh_client():
    import paramiko
    cl = paramiko.SSHClient()
    cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    from .config import SSH_HOST, SSH_USER, SSH_PASS
    cl.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
    return cl

def remote_cat(cl, path):
    _, o, _ = cl.exec_command(f"cat {path} 2>/dev/null || echo MISSING")
    return o.read().decode().strip()

def remote_cmd(cl, cmd):
    _, o, _ = cl.exec_command(cmd)
    return o.read().decode().strip()

def local_curl(path):
    import subprocess
    from .config import API_HOST
    try:
        r = subprocess.run(["curl", "-s", f"http://{API_HOST}{path}"],
                           capture_output=True, text=True, timeout=10)
        return r.stdout
    except: return ""

def ensure_dirs():
    from .config import DATA_DIR, LEDGER_DIR, PROVENANCE_DIR, REPORTS_DIR
    for d in [DATA_DIR, LEDGER_DIR, PROVENANCE_DIR, REPORTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def log_append(log_path, entry):
    """Append one JSON line. Never overwrites."""
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
