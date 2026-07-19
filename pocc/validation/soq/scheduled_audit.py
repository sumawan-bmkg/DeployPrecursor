"""
Daily Scientific Audit — runs hourly via cron.
Appends to audit_log.jsonl, generates daily report.

Crontab: 0 * * * * cd /opt/pimes/pocc && /opt/pimes/laws/runtime/.venv/bin/python validation/soq/scheduled_audit.py
"""
import json, os, sys, hashlib
from pathlib import Path
from datetime import datetime, timezone

# Paths
BASE = Path("/opt/pimes/pocc")
SOQ_DIR = BASE / "validation" / "soq"
AUDIT_LOG = SOQ_DIR / "audit_log.jsonl"
REPORTS_DIR = SOQ_DIR / "reports"
EVIDENCE_DIR = SOQ_DIR / "evidence"

HOST = "127.0.0.1"

def now(): return datetime.now(timezone.utc).isoformat()

def log_entry(event, score, details):
    entry = {"ts": now(), "event": event, "score": score, "details": details}
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def run():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    
    ts = now()
    print(f"[{ts}] Scheduled audit starting...")
    
    # Collect all metrics via local curl
    import subprocess
    
    def local_curl(url):
        try:
            r = subprocess.run(["curl", "-s", url], capture_output=True, text=True, timeout=10)
            return r.stdout
        except: return ""
    
    def local_cat(path):
        try: return Path(path).read_text(encoding="utf-8")
        except: return "MISSING"
    
    results = {}
    
    # Q1: Data
    mf = json.loads(local_cat("/opt/pimes/laws/runtime/validation/pdac/collector_manifest.json"))
    q = mf.get("queue", {})
    total = sum(q.values())
    sr = q.get("SUCCESS", 0) / max(total, 1) * 100
    results["q1_data"] = {"total": total, "success_rate": sr, "failed": q.get("FAILED", 0)}
    log_entry("AUDIT_Q1", sr, results["q1_data"])
    
    # Q2: Pipeline
    pipe_raw = local_curl(f"http://{HOST}:8500/api/pipeline/stages")
    try:
        stages = json.loads(pipe_raw).get("stages", [])
        healthy = sum(1 for s in stages if s.get("status") in ("ACTIVE", "RUNNING", "COMPLETE"))
        results["q2_pipeline"] = {"stages": len(stages), "healthy": healthy}
    except:
        results["q2_pipeline"] = {"stages": 0, "healthy": 0}
    log_entry("AUDIT_Q2", results["q2_pipeline"]["healthy"] / max(results["q2_pipeline"]["stages"], 1) * 100, results["q2_pipeline"])
    
    # Q3: Prediction
    hm_raw = local_curl(f"http://{HOST}:8500/api/health-model")
    try:
        hm = json.loads(hm_raw)
        sci = hm.get("components", {}).get("scientific", {}).get("score", 0)
        runtime = hm.get("components", {}).get("runtime", {}).get("score", 0)
        results["q3_prediction"] = {"scientific": sci, "runtime": runtime}
    except:
        results["q3_prediction"] = {"scientific": 0, "runtime": 0}
    log_entry("AUDIT_Q3", results["q3_prediction"]["scientific"], results["q3_prediction"])
    
    # Q5: Infrastructure
    infra_raw = local_curl(f"http://{HOST}:8500/api/infrastructure")
    try:
        infra = json.loads(infra_raw)
        results["q5_infra"] = {
            "cpu": infra.get("cpu", {}).get("usage_pct", 0),
            "ram": infra.get("memory", {}).get("usage_pct", 0),
        }
    except:
        results["q5_infra"] = {"cpu": 0, "ram": 0}
    log_entry("AUDIT_Q5", 100 - results["q5_infra"]["ram"], results["q5_infra"])
    
    # Q8: Acceptance (all pages)
    pages = ["/", "/engineering", "/scientific-ops", "/pipeline-runtime",
             "/alert-center", "/evidence-center", "/release-center",
             "/executive-center", "/digitaltwin", "/governance", "/api/health"]
    up = 0
    for p in pages:
        code = local_curl(f"http://{HOST}:8500{p}")
        try:
            if code.strip() in ("200", "201"): up += 1
        except: pass
    results["q8_acceptance"] = {"tested": len(pages), "up": up}
    log_entry("AUDIT_Q8", up / max(len(pages), 1) * 100, results["q8_acceptance"])
    
    # Overall
    scores = [
        results["q1_data"]["success_rate"],
        results["q2_pipeline"]["healthy"] / max(results["q2_pipeline"]["stages"], 1) * 100,
        results["q3_prediction"]["scientific"],
        100 - results["q5_infra"]["ram"],
        up / max(len(pages), 1) * 100,
    ]
    overall = sum(scores) / len(scores)
    log_entry("AUDIT_OVERALL", overall, {"scores": scores})
    
    print(f"[{ts}] Audit complete. Overall: {overall:.1f}%")
    print(f"  Q1 Data: {results['q1_data']['success_rate']:.1f}%")
    print(f"  Q2 Pipeline: {results['q2_pipeline']['healthy']}/{results['q2_pipeline']['stages']}")
    print(f"  Q3 Prediction: {results['q3_prediction']['scientific']:.1f}%")
    print(f"  Q5 Infra: CPU={results['q5_infra']['cpu']}% RAM={results['q5_infra']['ram']}%")
    print(f"  Q8 Pages: {up}/{len(pages)}")
    
    # Daily report generation
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    daily_path = REPORTS_DIR / f"daily_audit_{today}.md"
    
    lines = [f"# Daily Scientific Audit — {today}\n"]
    lines.append(f"Generated: {ts}\n")
    lines.append("## Audit Log\n")
    lines.append("| Timestamp | Event | Score | Details |")
    lines.append("|-----------|-------|-------|---------|")
    
    if AUDIT_LOG.exists():
        for line in AUDIT_LOG.read_text(encoding="utf-8").strip().split("\n"):
            try:
                e = json.loads(line)
                if e["ts"].startswith(today):
                    lines.append(f"| {e['ts'][:19]} | {e['event']} | {e['score']:.1f}% | {json.dumps(e.get('details',{}))[:60]} |")
            except: pass
    
    lines.append(f"\n## Overall Score: {overall:.1f}%\n")
    
    daily_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Daily report: {daily_path}")

if __name__ == "__main__":
    run()
