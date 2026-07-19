"""CSQ Collector Audit — Phase 1."""
import json
from .config import PDAC, DATA_DIR, REPORTS_DIR, EVIDENCE_DIR
from .utils import sf, now_iso, ssh_client, remote_cat, log_entry

def audit():
    cl = ssh_client()
    mf = json.loads(remote_cat(cl, str(PDAC / "collector_manifest.json")))
    rm = json.loads(remote_cat(cl, str(PDAC / "remote_manifest.json")))
    cl.close()

    q = mf.get("queue", {})
    v = mf.get("validation", {})
    total = sum(q.values())
    sr = q.get("SUCCESS", 0) / max(total, 1) * 100
    fr = q.get("FAILED", 0) / max(total, 1) * 100
    completeness = v.get("validated", 0) / max(v.get("total", 1), 1) * 100
    stations = rm.get("stations", []) if isinstance(rm.get("stations"), list) else []
    online = rm.get("online", 0)

    score = sf(sr * 0.3 + completeness * 0.4 + max(0, 100 - fr * 10) * 0.3)

    result = {
        "ts": now_iso(), "score": score,
        "total_files": total, "success_rate": sf(sr), "fail_rate": sf(fr),
        "completeness": sf(completeness), "stations_total": len(stations),
        "stations_online": online,
    }
    # Write outputs
    (DATA_DIR / "collector_score.json").write_text(json.dumps(result, indent=2))
    (EVIDENCE_DIR / "collector_score.json").write_text(json.dumps(result, indent=2))
    log_entry(DATA_DIR / "audit_log.jsonl", "COLLECTOR", score, result)
    print(f"  Collector: {score:.1f}% (files={total}, sr={sr:.1f}%, completeness={completeness:.1f}%)")
    return result
