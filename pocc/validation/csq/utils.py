"""CSQ Shared utilities — SSH, JSON, hashing, safe_float."""
import json, hashlib, math, uuid
from datetime import datetime, timezone

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def now_utc():
    return datetime.now(timezone.utc)

def sf(v, default=0.0):
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f): return default
        return f
    except: return default

def sha256_str(s):
    if isinstance(s, str): s = s.encode()
    return hashlib.sha256(s).hexdigest()

def sha256_file(path):
    try:
        return hashlib.sha256(open(path, "rb").read()).hexdigest()
    except: return "N/A"

def new_uuid():
    return str(uuid.uuid4())

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

def remote_curl(cl, url):
    _, o, _ = cl.exec_command(f"curl -s {url}")
    return o.read().decode().strip()

def local_api(path):
    from .config import API_HOST
    import subprocess
    try:
        r = subprocess.run(["curl", "-s", f"http://{API_HOST}{path}"],
                           capture_output=True, text=True, timeout=10)
        return r.stdout
    except: return ""

def log_entry(log_path, event, score, details=None):
    entry = {"ts": now_iso(), "event": event, "score": sf(score), "details": details or {}}
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def ensure_dirs():
    from .config import DATA_DIR, REPORTS_DIR, EVIDENCE_DIR
    for d in [DATA_DIR, REPORTS_DIR, EVIDENCE_DIR]:
        d.mkdir(parents=True, exist_ok=True)
