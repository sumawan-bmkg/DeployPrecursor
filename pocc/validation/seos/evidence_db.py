"""SEOS Evidence Database — structured evidence with UUID + SHA256."""
import json
from .config import DATA_DIR
from .utils import now_iso, new_uuid, sha256_str
from . import ledger

def record_evidence(event_type: str, component: str, score: float,
                    status: str, severity: str = "INFO", details: dict = None):
    """Record one evidence entry in both JSON and ledger."""
    uid = new_uuid()
    manifest_hash = sha256_str(json.dumps(details or {}))

    # JSON file (human-readable)
    ev = {
        "id": uid, "ts": now_iso(), "event_type": event_type,
        "component": component, "score": score,
        "status": status, "severity": severity,
        "manifest_hash": manifest_hash, "details": details or {},
    }
    path = DATA_DIR / f"ev_{uid[:8]}.json"
    path.write_text(json.dumps(ev, indent=2), encoding="utf-8")

    # Ledger (append-only)
    ledger.insert("evidence", {
        "event_type": event_type, "component": component, "score": score,
        "status": status, "severity": severity,
        "details": json.dumps(details or {}), "manifest_hash": manifest_hash,
    })

    return uid

def build_from_csq():
    """Import CSQ scores as evidence."""
    from .config import CSQ_DATA
    files = {
        "collector_score.json": "collector",
        "runtime_score.json": "runtime",
        "prediction_score.json": "prediction",
        "drift_score.json": "drift",
        "dashboard_score.json": "dashboard",
        "qualification_current.json": "qualification",
        "erb_manifest.json": "erb",
        "shadow_readiness.json": "shadow",
    }
    imported = 0
    for fname, component in files.items():
        fpath = CSQ_DATA / fname
        if fpath.exists():
            try:
                data = json.loads(fpath.read_text(encoding="utf-8"))
                score = data.get("score", data.get("overall", 0))
                status = "COLLECTED"
                record_evidence("CSQ_IMPORT", component, score, status, details=data)
                imported += 1
            except: pass
    return imported

def summary() -> dict:
    """Get evidence summary."""
    json_files = list(DATA_DIR.glob("ev_*.json"))
    ledger_count = ledger.count("evidence")
    return {
        "json_files": len(json_files),
        "ledger_entries": ledger_count,
        "total": len(json_files) + ledger_count,
    }
