"""SOAP Shared Utilities."""
import json, math, uuid, hashlib
from datetime import datetime, timezone

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

def local_curl(path):
    import subprocess
    from .config import API_HOST
    try:
        r = subprocess.run(["curl", "-s", f"http://{API_HOST}{path}"], capture_output=True, text=True, timeout=10)
        return r.stdout
    except: return ""

def ensure_dirs():
    from .config import REGISTRY_DIR, REPORTS_DIR, ACCREDITATION_DIR
    for d in [REGISTRY_DIR, REPORTS_DIR, ACCREDITATION_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def safe_read_json(path):
    try: return json.loads(open(path, encoding="utf-8").read())
    except: return {}
