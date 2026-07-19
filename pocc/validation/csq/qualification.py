"""CSQ Qualification Engine — Phase 5: weighted scoring + history."""
import csv, json
from .config import WEIGHTS, DATA_DIR, EVIDENCE_DIR, HISTORY_CSV
from .utils import sf, now_iso, log_entry

def compute_overall(scores: dict) -> float:
    """Weighted average of all component scores."""
    total_w = 0
    total_s = 0
    for k, w in WEIGHTS.items():
        s = scores.get(k, 0)
        total_w += w
        total_s += s * w
    return sf(total_s / max(total_w, 1))

def run(scores: dict):
    overall = compute_overall(scores)
    now = now_iso()

    # Append to history CSV (append-only, never overwrite)
    write_header = not HISTORY_CSV.exists()
    with open(HISTORY_CSV, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(["timestamp", "collector", "runtime", "prediction", "drift",
                         "overall", "score_data"])
        w.writerow([
            now,
            sf(scores.get("collector", 0)),
            sf(scores.get("runtime", 0)),
            sf(scores.get("prediction", 0)),
            sf(scores.get("drift", 0)),
            sf(overall),
            json.dumps(scores),
        ])

    # Write current scores
    result = {
        "ts": now, "overall": sf(overall), "components": scores,
        "weights": WEIGHTS,
    }
    (DATA_DIR / "qualification_current.json").write_text(json.dumps(result, indent=2))
    (EVIDENCE_DIR / "qualification_current.json").write_text(json.dumps(result, indent=2))
    log_entry(DATA_DIR / "audit_log.jsonl", "QUALIFICATION", overall, scores)
    print(f"  Qualification: {overall:.1f}%")
    return result
