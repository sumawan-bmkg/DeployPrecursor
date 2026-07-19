"""CSQ Runtime Audit — Phase 2."""
import json
from .config import API_HOST, DATA_DIR, EVIDENCE_DIR
from .utils import sf, now_iso, local_api, log_entry

def audit():
    raw = local_api("/api/pipeline/stages")
    stages = json.loads(raw).get("stages", []) if raw else []

    healthy = 0
    total_score = 0
    stage_details = []
    for s in stages:
        status = s.get("status", "UNKNOWN")
        score = s.get("score", 0)
        if status in ("ACTIVE", "RUNNING", "COMPLETE", "PASSED"):
            healthy += 1
        total_score += score
        stage_details.append({
            "id": s.get("id"), "label": s.get("label"),
            "status": status, "score": sf(score),
            "category": s.get("category", ""),
        })

    avg = total_score / max(len(stages), 1)
    score = sf((healthy / max(len(stages), 1)) * avg)

    result = {
        "ts": now_iso(), "score": score,
        "stages_total": len(stages), "stages_healthy": healthy,
        "avg_stage_score": sf(avg), "stages": stage_details,
    }
    (DATA_DIR / "runtime_score.json").write_text(json.dumps(result, indent=2))
    (EVIDENCE_DIR / "runtime_score.json").write_text(json.dumps(result, indent=2))
    log_entry(DATA_DIR / "audit_log.jsonl", "RUNTIME", score, {"healthy": healthy, "total": len(stages)})
    print(f"  Runtime: {score:.1f}% ({healthy}/{len(stages)} stages)")
    return result
