#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
acceptance_test.py — Gate 1-4 Acceptance Test for LAWS V2 Operational Pipeline.

Run on Ubuntu server:
    /opt/pimes/laws/runtime/.venv/bin/python acceptance_test.py

Tests:
  Gate 1: Real LAWS inference (checkpoint + predict_cli)
  Gate 2: End-to-end pipeline (mock data -> warning)
  Gate 3: Decision Engine scenarios (3 cases)
  Gate 4: Dashboard API verification
"""
import json, sys, os, time, subprocess

LAWS_VENV = "/opt/pimes/laws/runtime/.venv/bin/python"
POCC_DIR = "/opt/pimes/pocc"
LAWS_DIR = "/opt/pimes/laws"
PASS = 0
FAIL = 0

# Ensure collector package importable
sys.path.insert(0, POCC_DIR)

def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print("  [PASS] %s" % name)
    else:
        FAIL += 1
        print("  [FAIL] %s" % name)
        if detail:
            print("         - %s" % detail)

def gate1_real_laws_inference():
    print("")
    print("=" * 60)
    print("GATE 1 - Real LAWS Inference")
    print("=" * 60)

    # Check checkpoint exists
    ckpt = os.path.join(LAWS_DIR, "checkpoints", "v95_pimes_champion.pth")
    exists = os.path.exists(ckpt)
    size = os.path.getsize(ckpt) if exists else 0
    test("checkpoint ditemukan", exists, ckpt)
    test("checkpoint size valid (>30MB)", size > 30_000_000, "size=%d" % size)

    # Check predict_cli.py exists
    cli = os.path.join(LAWS_DIR, "predict_cli.py")
    test("predict_cli.py exists", os.path.exists(cli))

    # Try running predict_cli with --help
    try:
        r = subprocess.run(
            [LAWS_VENV, cli, "--help"],
            capture_output=True, text=True, timeout=15
        )
        test("predict_cli berhasil dipanggil", r.returncode == 0,
             r.stderr[:200] if r.returncode != 0 else "")
    except Exception as e:
        test("predict_cli berhasil dipanggil", False, str(e)[:200])
        return

    # Check LAWSRealPredictor can load
    try:
        from collector.laws_predictor import LAWSRealPredictor
        p = LAWSRealPredictor()
        info = p.get_model_info()
        test("LAWSRealPredictor loads", True)
        test("status=loaded", info.get("status") == "loaded",
             "status=%s" % info.get("status"))
        test("fallback hanya saat exception",
             "mock" not in info.get("fallback", "").lower() or info.get("status") == "loaded",
             "fallback=%s" % info.get("fallback"))

        print("")
        print("  [LAWSPredictor]")
        print("  Backend: " + info.get("model_name"))
        print("  Status:  " + info.get("status"))
        print("  Fallback:" + info.get("fallback"))
    except Exception as e:
        test("LAWSRealPredictor loads", False, str(e)[:200])

    # Check torch available in LAWS venv
    try:
        r = subprocess.run(
            [LAWS_VENV, "-c", "import torch; print(torch.__version__)"],
            capture_output=True, text=True, timeout=10
        )
        test("torch available in LAWS venv", r.returncode == 0,
             r.stdout.strip())
    except Exception as e:
        test("torch available in LAWS venv", False, str(e)[:100])


def gate2_end_to_end():
    print("")
    print("=" * 60)
    print("GATE 2 - End-to-End Pipeline")
    print("=" * 60)

    # Test decision_engine
    try:
        from collector.decision_engine import DecisionEngine
        from collector.predictor_base import Prediction

        engine = DecisionEngine(audit_dir="/tmp/test_decisions")
        pred = Prediction(
            probability=0.65, confidence=0.7, uncertainty=0.3,
            station="ALR", timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
            model_version="test", backend="test"
        )
        decision = engine.evaluate(pred, qc_score=0.75)
        test("DecisionEngine produces decision", decision is not None)
        test("decision level valid",
             decision.level in ("CLEAR", "WATCH", "WARNING", "CRITICAL"))
        test("decision has UUID", len(decision.decision_uuid) > 0)
        print("     Level: %s, P=%.4f" % (decision.level, decision.probability))
    except Exception as e:
        test("DecisionEngine", False, str(e)[:200])

    # Test station_fusion
    try:
        from collector.station_fusion import StationFusion, StationPrediction
        fusion = StationFusion(data_dir="/tmp/test_events")

        # Two close stations (AMB, ALR ~140km apart)
        preds = [
            StationPrediction("AMB", 0.75, 0.8, 0.2, 0.7),
            StationPrediction("ALR", 0.72, 0.75, 0.25, 0.65),
        ]
        events = fusion.fuse(preds)
        test("StationFusion produces events", len(events) > 0)
        if events:
            test("fused_probability valid", 0 < events[0].fused_probability < 1)
            test("n_stations >= 2", events[0].n_stations >= 2)
            print("     Event: %s, P=%.4f, N=%d" % (
                events[0].event_id, events[0].fused_probability,
                events[0].n_stations))
    except Exception as e:
        test("StationFusion", False, str(e)[:200])

    # Test event_manager
    try:
        from collector.event_manager import EventManager
        mgr = EventManager(data_dir="/tmp/test_events")
        if events:
            evt = mgr.process_fused_event(events[0])
            test("EventManager creates event", evt is not None)
            test("event has state",
                 evt.state.value in ("NEW", "ACTIVE", "PEAK", "DECAY", "CLOSED"))
            print("     Event state: %s" % evt.state.value)
    except Exception as e:
        test("EventManager", False, str(e)[:200])

    # Test warning_manager
    try:
        from collector.warning_manager import WarningManager
        wm = WarningManager(data_dir="/tmp/test_warnings")
        if events:
            w = wm.issue_warning(
                event_id=events[0].event_id,
                level="WARNING",
                probability=events[0].fused_probability,
                stations=events[0].stations,
                reason="Test acceptance"
            )
            test("WarningManager creates warning", w is not None)
            test("warning has state",
                 w.state.value in ("NEW", "ACTIVE", "UPDATED"))
            print("     Warning: %s, state=%s" % (w.warning_id, w.state.value))
    except Exception as e:
        test("WarningManager", False, str(e)[:200])


def gate3_decision_engine_scenarios():
    print("")
    print("=" * 60)
    print("GATE 3 - Decision Engine Scenarios")
    print("=" * 60)

    from collector.decision_engine import DecisionEngine
    from collector.predictor_base import Prediction

    engine = DecisionEngine(audit_dir="/tmp/test_gate3")

    # Case 1: Low probability -> CLEAR (NO WARNING)
    print("")
    print("  Case 1: P=0.20 -> CLEAR")
    pred1 = Prediction(probability=0.20, confidence=0.9, uncertainty=0.1,
                       station="ALR", timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"))
    d1 = engine.evaluate(pred1, qc_score=0.80)
    test("Case 1: level=CLEAR", d1.level == "CLEAR", "got=%s" % d1.level)
    print("     Result: %s - %s" % (d1.level, d1.explanation))

    # Case 2: High P but low QC -> REJECTED (CLEAR)
    print("")
    print("  Case 2: P=0.85, QC=0.20 -> CLEAR (rejected)")
    pred2 = Prediction(probability=0.85, confidence=0.8, uncertainty=0.2,
                       station="AMB", timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"))
    d2 = engine.evaluate(pred2, qc_score=0.20)
    test("Case 2: level=CLEAR (QC rejects)", d2.level == "CLEAR",
         "got=%s" % d2.level)
    print("     Result: %s - %s" % (d2.level, d2.explanation))

    # Case 3: High P, high QC, low U -> WARNING
    print("")
    print("  Case 3: P=0.88, QC=0.90, U=0.12 -> WARNING")
    pred3 = Prediction(probability=0.88, confidence=0.88, uncertainty=0.12,
                       station="KPY", timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"))
    d3 = engine.evaluate(pred3, qc_score=0.90)
    test("Case 3: level=WARNING or CRITICAL",
         d3.level in ("WARNING", "CRITICAL"), "got=%s" % d3.level)
    print("     Result: %s - %s" % (d3.level, d3.explanation))

    # Check all 3 rules passed for Case 3
    all_pass = all(t["passed"] for t in d3.triggered_rules)
    test("Case 3: all rules passed", all_pass)
    for t in d3.triggered_rules:
        status = "PASS" if t["passed"] else "FAIL"
        print("     Rule %s: %s - %s" % (t["rule"], status, t["detail"]))


def gate4_dashboard_api():
    print("")
    print("=" * 60)
    print("GATE 4 - Dashboard API Verification")
    print("=" * 60)

    import urllib.request

    base = "http://localhost:8500"
    endpoints = [
        "/api/overview",
        "/api/predictor",
        "/api/events",
        "/api/warnings",
        "/api/decisions",
        "/api/fused-events",
        "/api/collector",
        "/api/health-model",
    ]

    for ep in endpoints:
        try:
            url = base + ep
            req = urllib.request.urlopen(url, timeout=5)
            data = json.loads(req.read())
            test("GET %s -> 200" % ep, True)
            # Show key data
            if "events" in data:
                print("     events: %d" % data.get("total", 0))
            elif "warnings" in data:
                print("     warnings: %d" % data.get("total", 0))
            elif "decisions" in data:
                print("     decisions: %d" % data.get("total", 0))
            elif "status" in data:
                print("     status: %s" % data.get("status"))
            elif "events" in data:
                print("     events: %d" % data.get("total", 0))
        except Exception as e:
            test("GET %s -> 200" % ep, False, str(e)[:100])

    # Check HTML pages
    pages = ["/events", "/warnings", "/dashboard"]
    for pg in pages:
        try:
            url = base + pg
            req = urllib.request.urlopen(url, timeout=5)
            test("GET %s -> HTML" % pg, req.status == 200)
        except Exception as e:
            test("GET %s -> HTML" % pg, False, str(e)[:100])


def main():
    print("=" * 60)
    print("LAWS V2 ACCEPTANCE TEST - Gates 1-4")
    print("=" * 60)

    gate1_real_laws_inference()
    gate2_end_to_end()
    gate3_decision_engine_scenarios()
    gate4_dashboard_api()

    print("")
    print("=" * 60)
    print("RESULTS: %d passed, %d failed" % (PASS, FAIL))
    print("=" * 60)

    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
