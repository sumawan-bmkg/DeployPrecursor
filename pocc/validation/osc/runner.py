"""OSC Runner — orchestrates all phases.

Usage:
  python -m validation.osc              # run once (hourly cycle)
  python -m validation.osc --baseline   # freeze baseline only
  python -m validation.osc --daily      # generate daily report
  python -m validation.osc --status     # show current status
"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from validation.osc.baseline import freeze as baseline_freeze
from validation.osc.hourly import collect_hourly
from validation.osc.daily import generate_daily
from validation.osc.anomaly import scan_for_anomalies
from validation.osc.shadow import evaluate as shadow_evaluate
from validation.osc.cepsl import run_cepsl_cycle
from validation.osc.config import DATA, OSC_DIR
from validation.osc.utils import ensure_dirs, now_iso, today

def run_once():
    ensure_dirs()
    ts = now_iso()
    print(f"\n{'='*55}")
    print(f"OSC v1.0 — Operational Scientific Campaign")
    print(f"Cycle: {ts[:19]}")
    print(f"{'='*55}\n")

    # Phase 2: Hourly snapshot
    snapshot = collect_hourly()

    # Phase 5: Anomaly scan
    print("\nScanning for anomalies...")
    anomalies = scan_for_anomalies(snapshot)

    # Phase 1-10: CEPSL — Evidence Preservation
    print("\nRunning CEPSL cycle...")
    try:
        cepsl = run_cepsl_cycle(snapshot)
        print(f"  CEPSL: day={cepsl['campaign_day']} baseline={'VALID' if cepsl['baseline_valid'] else 'COMPROMISED'} "
              f"archive={cepsl['archive_verified']} issues={cepsl['archive_issues']} "
              f"shadow_eligible={'YES' if cepsl['shadow_eligible'] else 'NO'}")
    except Exception as e:
        print(f"  CEPSL: FAILED — {e}")

    # Phase 1-10: CEPSL — Evidence Preservation
    print("\nRunning CEPSL cycle...")
    try:
        cepsl = run_cepsl_cycle(snapshot)
        print(f"  CEPSL: day={cepsl['campaign_day']} baseline={'VALID' if cepsl['baseline_valid'] else 'COMPROMISED'} "
              f"archive={cepsl['archive_verified']} issues={cepsl['archive_issues']} "
              f"shadow_eligible={'YES' if cepsl['shadow_eligible'] else 'NO'}")
    except Exception as e:
        print(f"  CEPSL: FAILED — {e}")

    # Phase 9: Readiness evaluation
    print("\nEvaluating shadow readiness...")
    readings = []
    hourly_dir = DATA / "hourly"
    for f in sorted(hourly_dir.glob("snapshots_*.jsonl"))[-7:]:
        for line in f.read_text(encoding="utf-8").strip().split("\n"):
            try: readings.append(json.loads(line))
            except: pass
    shadow = shadow_evaluate(readings[-50:])  # last 50 readings

    print(f"\n{'='*55}")
    print(f"OSC COMPLETE")
    print(f"  Health: {snapshot.get('overall', 0):.1f}%")
    print(f"  Anomalies: {len(anomalies)}")
    print(f"  Shadow: {shadow.get('decision', '?')}")
    print(f"{'='*55}\n")

def run_daily():
    generate_daily()

def run_baseline():
    baseline_freeze()

def show_status():
    current = {}
    try:
        current = json.loads((DATA / "hourly" / "current.json").read_text())
    except: pass
    readiness = {}
    try:
        readiness = json.loads((DATA / "shadow_readiness.json").read_text())
    except: pass
    print(f"\nOSC Status:")
    print(f"  Last snapshot: {current.get('ts', 'N/A')[:19]}")
    print(f"  Health: {current.get('overall', 0):.1f}%")
    print(f"  Pipeline: {current.get('pipeline_healthy', 0)}/{current.get('pipeline_total', 0)}")
    print(f"  Shadow: {readiness.get('decision', 'N/A')} ({readiness.get('overall', 0):.1f}%)")
    print()

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--baseline" in args: run_baseline()
    elif "--daily" in args: run_daily()
    elif "--status" in args: show_status()
    else: run_once()
