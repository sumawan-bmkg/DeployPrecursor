"""CSQ Prediction Audit — Phase 3."""
import json
from .config import API_HOST, DATA_DIR, EVIDENCE_DIR
from .utils import sf, now_iso, local_api, log_entry

def audit():
    hm = json.loads(local_api("/api/health-model")) or {}
    oi = json.loads(local_api("/api/oi/health")) or {}
    alerts = json.loads(local_api("/api/oi/alerts")) or []

    comps = hm.get("components", {})
    sci = sf(comps.get("scientific", {}).get("score", 0))
    runtime = sf(comps.get("runtime", {}).get("score", 0))
    unresolved = sum(1 for a in (alerts if isinstance(alerts, list) else [])
                     if isinstance(a, dict) and a.get("status") != "resolved")

    score = sf(sci * 0.6 + runtime * 0.4)

    result = {
        "ts": now_iso(), "score": score,
        "scientific_score": sci, "runtime_score": runtime,
        "unresolved_alerts": unresolved,
        "note": "Real metrics (RMSE, F1, etc.) populate during Shadow Mode",
    }
    (DATA_DIR / "prediction_score.json").write_text(json.dumps(result, indent=2))
    (EVIDENCE_DIR / "prediction_score.json").write_text(json.dumps(result, indent=2))
    log_entry(DATA_DIR / "audit_log.jsonl", "PREDICTION", score, {"sci": sci, "alerts": unresolved})
    print(f"  Prediction: {score:.1f}% (sci={sci:.1f}%, runtime={runtime:.1f}%)")
    return result
