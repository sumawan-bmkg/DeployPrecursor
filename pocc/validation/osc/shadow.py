"""OSC Phase 9 — Shadow Readiness Gate."""
import json
from .config import OSC_DIR, DATA, REPORTS
from .utils import now_iso, today, sf, ensure_dirs

def evaluate(readings: list):
    """Evaluate shadow readiness from accumulated evidence."""
    ensure_dirs()
    now = now_iso()

    if not readings:
        return {"decision": "NOT READY", "reason": "No operational data"}

    # Compute stats from readings
    healths = [sf(r.get("overall", 0)) for r in readings]
    pipelines = [sf(r.get("pipeline_healthy", 0)) for r in readings]
    pipeline_totals = [sf(r.get("pipeline_total", 15)) for r in readings]
    rams = [sf(r.get("infrastructure", {}).get("ram_used_pct", 0)) for r in readings]

    avg_health = sum(healths) / len(healths)
    health_stability = max(healths) - min(healths) if len(healths) > 1 else 0
    avg_pipeline = sum(pipelines) / max(sum(pipeline_totals), 1)
    avg_ram = sum(rams) / len(rams)
    uptime_pct = len(readings) / max(1, (len(readings) * 1)) * 100  # all readings = running
    data_days = len(set(r["ts"][:10] for r in readings))

    # Readiness factors
    factors = {
        "health_score": avg_health,
        "health_stability": max(0, 100 - health_stability * 10),
        "pipeline_availability": avg_pipeline * 100,
        "infrastructure": max(0, 100 - avg_ram),
        "uptime": min(100, uptime_pct),
        "data_completeness": min(100, data_days * 10),
    }
    overall = sum(factors.values()) / len(factors)

    # Decision
    if overall >= 70 and avg_health >= 50 and data_days >= 7:
        decision = "READY FOR SHADOW"
    elif overall >= 60 and data_days >= 3:
        decision = "READY FOR RC1"
    elif overall >= 50:
        decision = "READY FOR ERB"
    else:
        decision = "NOT READY"

    result = {
        "ts": now, "decision": decision, "overall": sf(overall),
        "factors": {k: sf(v) for k, v in factors.items()},
        "stats": {
            "avg_health": sf(avg_health), "health_stability": sf(health_stability),
            "avg_pipeline": sf(avg_pipeline * 100), "avg_ram": sf(avg_ram),
            "readings": len(readings), "data_days": data_days,
        },
    }

    (DATA / "shadow_readiness.json").write_text(json.dumps(result, indent=2))
    print(f"  Shadow readiness: {decision} ({overall:.1f}%)")
    return result
