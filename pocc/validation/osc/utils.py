"""OSC Utilities."""
import json, hashlib, math, uuid, subprocess
from datetime import datetime, timezone
from pathlib import Path

def now_iso(): return datetime.now(timezone.utc).isoformat()
def today(): return datetime.now(timezone.utc).strftime("%Y-%m-%d")
def sf(v, d=0.0):
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f): return d
        return f
    except: return d
def sha256_str(s): return hashlib.sha256(s.encode() if isinstance(s, str) else s).hexdigest()
def new_uuid(): return str(uuid.uuid4())

def api(path):
    from .config import API
    try:
        r = subprocess.run(["curl", "-s", f"{API}{path}"], capture_output=True, text=True, timeout=15)
        return json.loads(r.stdout) if r.stdout.strip().startswith("{") or r.stdout.strip().startswith("[") else {}
    except: return {}

def safe_json(path):
    try: return json.loads(open(path, encoding="utf-8").read())
    except: return {}

def ensure_dirs():
    from .config import OSC_DIR, REPORTS, DATA, BASELINE, FINAL_PACKAGE
    for d in [OSC_DIR, REPORTS, DATA, BASELINE, FINAL_PACKAGE,
              REPORTS / "daily", REPORTS / "weekly", REPORTS / "replay",
              DATA / "anomalies", DATA / "hourly"]:
        d.mkdir(parents=True, exist_ok=True)

def log_jsonl(path, entry):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
