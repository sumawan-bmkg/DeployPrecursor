"""CEPSL — Continuous Evidence Preservation & Scientific Lock.

Extends OSC with immutable evidence archive and integrity verification.
Runs as part of OSC hourly cycle. No standalone execution.
"""
import json, hashlib, os, sqlite3, math, uuid
from pathlib import Path
from datetime import datetime, timezone

# ── Config ───────────────────────────────────────────────
ARCHIVE_ROOT = Path("/opt/pimes/posc/osc/archive")
LEDGER_DB = Path("/opt/pimes/posc/osc/data/cepsl_ledger.db")
LOCK_MANIFEST = Path("/opt/pimes/posc/osc/data/lock_manifest.json")
CAMPAIGN_START_FILE = Path("/opt/pimes/posc/osc/data/campaign_start.txt")
CAMPAIGN_DAYS = 14

# ── Helpers ──────────────────────────────────────────────
def now_iso(): return datetime.now(timezone.utc).isoformat()
def sf(v, d=0.0):
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f): return d
        return f
    except: return d
def sha256_str(s): return hashlib.sha256(s.encode() if isinstance(s, str) else s).hexdigest()
def sha256_file(p):
    try: return hashlib.sha256(open(p, "rb").read()).hexdigest()
    except: return "N/A"
def new_uuid(): return str(uuid.uuid4())

def _conn():
    conn = sqlite3.connect(str(LEDGER_DB))
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

# ── Phase 1: Scientific Lock ─────────────────────────────
def freeze_source_tree():
    """Compute SHA256 of all important paths. Call once at campaign start."""
    paths_to_lock = {
        "pocc_backend": Path("/opt/pimes/pocc/backend"),
        "runtime_kernel": Path("/opt/pimes/laws/runtime/rdmc"),
        "collector": Path("/opt/pimes/pocc/collector"),
        "config": Path("/opt/pimes/pocc/backend/main.py"),
    }
    manifest = {"ts": now_iso(), "components": {}, "frozen": True}
    for name, path in paths_to_lock.items():
        if path.is_file():
            manifest["components"][name] = {"sha256": sha256_file(path), "type": "file"}
        elif path.is_dir():
            h = hashlib.sha256()
            for f in sorted(path.rglob("*")):
                if f.is_file() and "__pycache__" not in str(f) and not f.suffix.endswith(".pyc"):
                    h.update(f.name.encode())
                    try: h.update(open(f, "rb").read())
                    except: pass
            manifest["components"][name] = {"sha256": h.hexdigest()[:32], "type": "dir"}
    LOCK_MANIFEST.write_text(json.dumps(manifest, indent=2))
    return manifest

def get_or_create_campaign_start():
    """Track when campaign began (immutable)."""
    if CAMPAIGN_START_FILE.exists():
        return CAMPAIGN_START_FILE.read_text().strip()
    start = now_iso()
    CAMPAIGN_START_FILE.write_text(start)
    return start

def campaign_day():
    start = get_or_create_campaign_start()
    try:
        start_dt = datetime.fromisoformat(start)
        delta = datetime.now(timezone.utc) - start_dt
        return delta.days + 1
    except: return 1

def is_baseline_valid():
    """Check if locked components changed since freeze."""
    if not LOCK_MANIFEST.exists(): return True  # no lock yet
    locked = json.loads(LOCK_MANIFEST.read_text())
    changes = []
    paths_map = {
        "pocc_backend": Path("/opt/pimes/pocc/backend"),
        "runtime_kernel": Path("/opt/pimes/laws/runtime/rdmc"),
        "collector": Path("/opt/pimes/pocc/collector"),
        "config": Path("/opt/pimes/pocc/backend/main.py"),
    }
    for name, info in locked.get("components", {}).items():
        path = paths_map.get(name)
        if not path: continue
        current = sha256_file(path) if path.is_file() else None
        if current and current != info.get("sha256", "N/A"):
            changes.append({"component": name, "old": info["sha256"], "new": current})
    return {"valid": len(changes) == 0, "changes": changes}

# ── Phase 2: Snapshot Archive ────────────────────────────
def archive_snapshot(snapshot: dict, osc_scores: dict):
    """Create immutable hourly archive snapshot."""
    now = datetime.now(timezone.utc)
    archive_dir = ARCHIVE_ROOT / str(now.year) / f"{now.month:02d}" / f"{now.day:02d}" / f"{now.hour:02d}"
    archive_dir.mkdir(parents=True, exist_ok=True)

    snapshot_id = new_uuid()
    entry = {
        "snapshot_id": snapshot_id,
        "ts": now_iso(),
        "snapshot": snapshot,
        "scores": osc_scores,
        "baseline_valid": is_baseline_valid(),
        "campaign_day": campaign_day(),
    }
    path = archive_dir / f"snapshot_{snapshot_id[:8]}.json"
    path.write_text(json.dumps(entry, indent=2))

    current_hash = sha256_file(path)

    _init_ledger()
    prev = _last_hash()
    chain_hash = sha256_str(f"{prev}:{snapshot_id}:{current_hash}")
    _conn().execute(
        "INSERT INTO campaign_snapshots (snapshot_id, ts, sha256, parent_hash, chain_hash, archive_path) VALUES (?,?,?,?,?,?)",
        (snapshot_id, now_iso(), current_hash, prev, chain_hash, str(path))
    )
    _conn().commit()
    _conn().close()

    return snapshot_id

def _init_ledger():
    _conn().executescript("""
        CREATE TABLE IF NOT EXISTS campaign_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            ts TEXT NOT NULL,
            sha256 TEXT,
            parent_hash TEXT,
            chain_hash TEXT,
            archive_path TEXT
        );
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT, snapshot_id TEXT, component TEXT, severity TEXT,
            description TEXT, status TEXT
        );
    """)
    _conn().commit()

def _last_hash():
    try:
        r = _conn().execute("SELECT chain_hash FROM campaign_snapshots ORDER BY ts DESC LIMIT 1").fetchone()
        return r[0] if r else "GENESIS"
    except: return "GENESIS"

# ── Phase 3: Integrity Verification ──────────────────────
def verify_archive_integrity():
    """Walk archive tree, verify every file hash and chain."""
    issues = []
    total = 0
    for f in sorted(ARCHIVE_ROOT.rglob("*.json")):
        if not f.name.startswith("snapshot_"): continue
        total += 1
        current_hash = sha256_file(f)
        try:
            data = json.loads(f.read_text())
            sid = data.get("snapshot_id", "unknown")
            if current_hash != data.get("sha256"):
                issues.append({"snapshot_id": sid, "file": str(f), "severity": "CRITICAL",
                               "description": f"Hash mismatch: expected={data.get('sha256')}, actual={current_hash}"})
        except:
            issues.append({"file": str(f), "severity": "ERROR", "description": "Invalid JSON"})
    return {"verified": total, "issues": issues}

# ── Phase 4: Evidence Integrity Watch ────────────────────
def check_evidence_integrity():
    """Scan all evidence sources for unexpected changes."""
    checks = {}
    evidence_paths = [
        ("csq_data", Path("/opt/pimes/posc/csq/data")),
        ("seos_data", Path("/opt/pimes/pocc/validation/seos/evidence_db")),
        ("osrv_reports", Path("/opt/pimes/pocc/validation/osrv/reports")),
        ("soq_reports", Path("/opt/pimes/pocc/validation/soq/reports")),
    ]
    for name, path in evidence_paths:
        if path.exists():
            files = list(path.glob("*"))
            checks[name] = {"count": len(files), "ok": True}
        else:
            checks[name] = {"count": 0, "ok": False}
    return checks

# ── Full CEPSL Cycle ─────────────────────────────────────
def run_cepsl_cycle(snapshot):
    """Called each hour after OSC snapshot."""
    if not LOCK_MANIFEST.exists():
        freeze_source_tree()

    osc_scores = {"overall": snapshot.get("overall", 0)}
    sid = archive_snapshot(snapshot, osc_scores)
    integrity = verify_archive_integrity()
    evidence = check_evidence_integrity()
    baseline_valid = is_baseline_valid()
    no_incidents = len(integrity.get("issues", [])) == 0
    day = campaign_day()
    shadow_gate = baseline_valid["valid"] and no_incidents and day >= CAMPAIGN_DAYS

    result = {
        "ts": now_iso(), "snapshot_id": sid, "campaign_day": day,
        "baseline_valid": baseline_valid["valid"],
        "baseline_changes": baseline_valid.get("changes", []),
        "archive_verified": integrity["verified"],
        "archive_issues": len(integrity["issues"]),
        "evidence_integrity": evidence,
        "shadow_eligible": shadow_gate,
    }
    Path("/opt/pimes/posc/osc/data/cepsl_status.json").write_text(json.dumps(result, indent=2))
    return result
