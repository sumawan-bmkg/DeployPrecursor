"""OSC Phase 2 — Hourly Monitoring. Collects live evidence every cycle."""
import json
from .config import OSC_DIR, DATA
from .utils import api, safe_json, now_iso, sf, log_jsonl, ensure_dirs

def collect_hourly():
    ensure_dirs()
    ts = now_iso()
    print(f"  Collecting hourly snapshot ({ts[:19]})...")

    # Live API data
    pipeline = api("/api/pipeline/stages")
    health = api("/api/health")
    infra = api("/api/infrastructure")
    hm = api("/api/health-model")

    stages = pipeline.get("stages", []) if pipeline else []
    stage_summary = {s["id"]: {"status": s.get("status"), "score": s.get("score", 0)} for s in stages}

    snapshot = {
        "ts": ts,
        "health_score": health.get("score", 0),
        "stages": stage_summary,
        "pipeline_healthy": sum(1 for s in stages if s.get("status") in ("ACTIVE", "RUNNING", "COMPLETE")),
        "pipeline_total": len(stages),
        "infrastructure": {
            "cpu_cores": infra.get("cpu", {}).get("cores", 0),
            "ram_used_pct": infra.get("memory", {}).get("usage_pct", 0),
        },
    }

    # Collector data
    try:
        cm = json.loads(open("/opt/pimes/laws/runtime/validation/pdac/collector_manifest.json").read())
        q = cm.get("queue", {})
        snapshot["collector"] = {
            "success": q.get("SUCCESS", 0), "failed": q.get("FAILED", 0),
            "total": sum(q.values()),
        }
    except: snapshot["collector"] = {}

    # Drift
    hm_comps = hm.get("components", {}) if hm else {}
    snapshot["scores"] = {k: v.get("score", 0) for k, v in hm_comps.items()}
    snapshot["overall"] = hm.get("score", 0)

    # Save hourly snapshot
    today = ts[:10]
    hourly_log = DATA / "hourly" / f"snapshots_{today}.jsonl"
    log_jsonl(hourly_log, snapshot)

    # Current snapshot
    (DATA / "hourly" / "current.json").write_text(json.dumps(snapshot, indent=2))

    print(f"  Snapshot: health={snapshot['overall']:.1f}% pipeline={snapshot['pipeline_healthy']}/{snapshot['pipeline_total']} ram={snapshot['infrastructure']['ram_used_pct']}%")
    return snapshot
