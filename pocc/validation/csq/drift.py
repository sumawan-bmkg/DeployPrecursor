"""CSQ Drift Detection — Phase 4. EWMA + z-score + rolling stats."""
import json, math
from .config import DATA_DIR, EVIDENCE_DIR, THRESHOLDS
from .utils import sf, now_iso, log_entry

def ewma(values, alpha=0.3):
    """Exponentially weighted moving average."""
    if not values: return 0
    result = values[0]
    for v in values[1:]:
        result = alpha * v + (1 - alpha) * result
    return result

def z_score(value, mean, std):
    if std == 0: return 0
    return (value - mean) / std

def compute_stats(history):
    if not history: return {"mean": 0, "std": 0, "trend": 0, "drift": 0, "ewma": 0}
    n = len(history)
    mean = sum(history) / n
    std = (sum((x - mean)**2 for x in history) / n) ** 0.5
    trend = history[-1] - history[0] if n > 1 else 0
    drift = max(history) - min(history) if n > 1 else 0
    return {"mean": sf(mean), "std": sf(std), "trend": sf(trend),
            "drift": sf(drift), "ewma": sf(ewma(history))}

def detect_drift(stats, name):
    drift = abs(stats["trend"])
    warn = THRESHOLDS["drift_warning"]
    crit = THRESHOLDS["drift_critical"]
    if drift >= crit: status = "CRITICAL"
    elif drift >= warn: status = "WARNING"
    else: status = "STABLE"
    return {"name": name, "status": status, "trend": stats["trend"],
            "drift": stats["drift"], "ewma": stats["ewma"]}

def audit():
    history_file = DATA_DIR / "qualification_history.csv"
    scores = {"collector": [], "runtime": [], "prediction": [], "overall": []}

    if history_file.exists():
        lines = history_file.read_text(encoding="utf-8").strip().split("\n")
        for line in lines[1:]:  # skip header
            parts = line.split(",")
            if len(parts) >= 6:
                scores["collector"].append(sf(parts[1]))
                scores["runtime"].append(sf(parts[2]))
                scores["prediction"].append(sf(parts[3]))
                scores["overall"].append(sf(parts[5]))

    drifts = []
    for name, vals in scores.items():
        if len(vals) >= 2:
            stats = compute_stats(vals)
            drifts.append(detect_drift(stats, f"prediction_{name}"))

    overall_drift = all(d["status"] == "STABLE" for d in drifts) if drifts else True
    score = 100 if overall_drift else (60 if any(d["status"] == "WARNING" for d in drifts) else 20)

    result = {
        "ts": now_iso(), "score": score,
        "drifts": drifts, "history_points": len(scores["overall"]),
        "status": "STABLE" if overall_drift else "DRIFT_DETECTED",
    }
    (DATA_DIR / "drift_score.json").write_text(json.dumps(result, indent=2))
    (EVIDENCE_DIR / "drift_score.json").write_text(json.dumps(result, indent=2))
    log_entry(DATA_DIR / "audit_log.jsonl", "DRIFT", score, {"status": result["status"]})
    print(f"  Drift: {score:.1f}% ({result['status']}, {len(scores['overall'])} history points)")
    return result
