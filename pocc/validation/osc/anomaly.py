"""OSC Phase 5 — Anomaly Register."""
import json
from .config import DATA
from .utils import now_iso, new_uuid, sf, log_jsonl

def register(subsystem, severity, root_cause, evidence, recovery="auto"):
    entry = {
        "uuid": new_uuid(), "ts": now_iso(),
        "subsystem": subsystem, "severity": severity,
        "root_cause": root_cause, "evidence": evidence,
        "recovery": recovery, "recovery_time_s": 0,
        "corrective_action": "pending",
    }
    log_jsonl(DATA / "anomalies" / "anomaly_register.jsonl", entry)
    print(f"  Anomaly: [{severity}] {subsystem} — {root_cause}")
    return entry

def scan_for_anomalies(snapshot):
    """Auto-detect anomalies from hourly snapshot."""
    anomalies = []

    # Health dropped significantly
    health = sf(snapshot.get("overall", 0))
    if health < 10:
        anomalies.append(register("runtime", "CRITICAL",
            f"Overall health critically low: {health:.1f}%",
            f"score={health:.1f}%"))

    # RAM high
    ram = sf(snapshot.get("infrastructure", {}).get("ram_used_pct", 0))
    if ram > 90:
        anomalies.append(register("infrastructure", "WARNING",
            f"RAM usage high: {ram:.1f}%", f"ram={ram}%"))

    # Pipeline stages missing
    total = snapshot.get("pipeline_total", 0)
    healthy = snapshot.get("pipeline_healthy", 0)
    if total > 0 and healthy / total < 0.5:
        anomalies.append(register("pipeline", "WARNING",
            f"Less than half pipeline healthy: {healthy}/{total}",
            f"healthy={healthy} total={total}"))

    # Collector failures
    collector = snapshot.get("collector", {})
    if collector.get("failed", 0) > 100:
        anomalies.append(register("collector", "WARNING",
            f"High collector failures: {collector.get('failed', 0)}",
            f"failures={collector.get('failed', 0)}"))

    return anomalies
