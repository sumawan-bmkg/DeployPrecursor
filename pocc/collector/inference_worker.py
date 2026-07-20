#!/usr/bin/env python3
"""
inference_worker.py — LAWS V2 Inference Worker.

Reads trigger results (from RuntimeTriggerWorker preprocessing),
runs LAWS V9.5 predict → DecisionEngine → StationFusion →
EventManager → WarningManager → PostgreSQL.

Idempotent: uses `.inferred` sidecar flags.
Scheduler: runs every 60s.
"""
import os, sys, json, time, logging, subprocess, glob
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

from collector.scheduler_engine import BaseWorker, manifest, PDAC_DIR
from collector.laws_predictor import LAWSRealPredictor
from collector.decision_engine import DecisionEngine
from collector.station_fusion import StationFusion, StationPrediction
from collector.event_manager import EventManager
from collector.warning_manager import WarningManager
from collector.predictor_base import Prediction
from collector.db import (
    save_prediction, save_decision, save_fused_event,
    save_event, save_warning,
    start_pipeline_run, finish_pipeline_run, audit_log, get_pool
)

log = logging.getLogger("inference")

VENV = "/opt/pimes/laws/runtime/.venv/bin/python"
LAWS_CLI = "/opt/pimes/laws/predict_cli.py"
RUNTIME_ROOT = "/opt/pimes/laws/runtime"
SCALOGRAM_DIR = "/opt/pimes/2026/scalogram"


class InferenceWorker(BaseWorker):
    """Convert valid certificates to stored predictions + events + warnings."""

    def __init__(self, name: str, manifest, interval: float = 60):
        super().__init__(name, manifest, interval)
        self.predictor = LAWSRealPredictor()
        self.decision_engine = DecisionEngine(
            audit_dir=str(PDAC_DIR / "decisions")
        )
        self.station_fusion = StationFusion(
            data_dir=str(PDAC_DIR / "events")
        )

    def execute(self) -> dict:
        run_id = start_pipeline_run("inference")
        t0 = time.time()
        processed = 0
        failed = 0

        try:
            triggers_dir = PDAC_DIR / "triggers"
            if not triggers_dir.exists():
                return {"processed": 0}

            # 1. Collect all unprocessed trigger results
            for trigger_path in sorted(triggers_dir.glob("*.json")):
                inferred_flag = trigger_path.with_suffix(".inferred")
                if inferred_flag.exists():
                    continue

                try:
                    result = self._process_trigger(trigger_path)
                    if result:
                        processed += 1
                    else:
                        failed += 1
                    # Mark inferred regardless (no retry storm)
                    inferred_flag.write_text(
                        json.dumps({"processed_at": datetime.now(timezone.utc).isoformat()})
                    )
                except Exception as e:
                    log.error("Trigger %s failed: %s", trigger_path.name, str(e)[:200])
                    failed += 1

            # 2. Run fusion on all recent predictions
            self._run_fusion_cycle()

            # 3. Housekeeping: expire old events
            self._housekeeping()

        except Exception as e:
            log.error("Inference cycle failed: %s", str(e)[:200])
            failed += 1

        duration_ms = round((time.time() - t0) * 1000, 1)
        finish_pipeline_run(
            run_id, "SUCCESS" if failed == 0 else "PARTIAL",
            processed, failed, duration_ms
        )

        return {"processed": processed, "failed": failed, "duration_ms": duration_ms}

    def _process_trigger(self, trigger_path: Path) -> bool:
        """Process one trigger result through the full pipeline."""
        with open(trigger_path) as f:
            trigger = json.load(f)

        station = trigger.get("station", "")
        filename = trigger.get("filename", "")
        result = trigger.get("result", {})

        if not station or not filename:
            log.warning("Invalid trigger: %s", trigger_path.name)
            return False

        # Parse date from filename (S260611.ALR → 260611)
        raw = filename.replace("S", "").split(".")[0]  # "260611"
        if len(raw) >= 6:
            h5_date = f"20{raw[:2]}-{raw[2:4]}-{raw[4:6]}"
        else:
            h5_date = datetime.now().strftime("%Y-%m-%d")

        log.info("Processing station=%s file=%s date=%s", station, filename, h5_date)

        # 2. Run LAWS V9.5 prediction
        pred = self._predict(station, h5_date)
        if not pred:
            return False

        # 3. Save prediction to PG
        save_prediction(pred)
        log.info("Prediction %s saved: P=%.4f U=%.4f",
                 pred.prediction_uuid[:8], pred.probability, pred.uncertainty)

        # 4. DecisionEngine
        qc_score = trigger.get("qc_score", 0.5)
        decision = self.decision_engine.evaluate(pred, qc_score=qc_score)
        # Link decision to prediction
        decision.prediction_uuid = pred.prediction_uuid
        save_decision(decision)
        log.info("Decision %s: %s for %s", decision.decision_uuid[:8], decision.level, station)

        # 5. Audit
        audit_log("inference", "prediction", {
            "station": station, "file": filename,
            "prediction_uuid": pred.prediction_uuid,
            "decision_uuid": decision.decision_uuid,
            "probability": pred.probability,
            "level": decision.level,
        })

        return True

    def _predict(self, station: str, h5_date: str) -> Optional[Prediction]:
        """Run LAWS V9.5 prediction. Returns Prediction or None."""
        try:
            # Build context-like object
            class Ctx:
                station = station
                h5_date = h5_date
                h5_dir = SCALOGRAM_DIR

            return self.predictor.predict(Ctx())
        except Exception as e:
            log.error("Predict error %s/%s: %s", station, h5_date, str(e)[:200])
            return None

    def _run_fusion_cycle(self):
        """Fuse recent predictions into events and warnings."""
        # Read recent predictions from PG
        try:
            from collector.db import list_predictions, list_decisions
            from collector.db import list_fused_events, get_pool

            pool = get_pool()
            if not pool:
                return

            # Get predictions from last 2 hours
            import psycopg2.extras
            with pool.getconn() as conn:
                try:
                    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                        cur.execute("""
                            SELECT p.*, d.level as decision_level
                            FROM predictions p
                            LEFT JOIN decisions d ON d.prediction_uuid = p.prediction_uuid
                            WHERE p.timestamp >= NOW() - INTERVAL '2 hours'
                            ORDER BY p.timestamp DESC
                        """)
                        rows = cur.fetchall()
                finally:
                    pool.putconn(conn)

            if not rows:
                return

            # Build StationPrediction list
            sp_list = []
            for r in rows:
                sp_list.append(StationPrediction(
                    station=r["station"],
                    probability=r["probability"] or 0.0,
                    confidence=r["confidence"] or 0.0,
                    uncertainty=r["uncertainty"] or 0.0,
                    qc_score=0.5,  # default
                    timestamp=r["timestamp"].isoformat() if hasattr(r["timestamp"], 'isoformat') else str(r.get("timestamp", "")),
                    prediction_uuid=r["prediction_uuid"],
                ))

            if not sp_list:
                return

            # Fuse
            fused_events = self.station_fusion.fuse(sp_list)

            # Save fused events + create/update events + warnings
            event_manager = EventManager(data_dir=str(PDAC_DIR / "events"))
            warning_manager = WarningManager(data_dir=str(PDAC_DIR / "warnings"))

            for fe in fused_events:
                # Save fused event
                save_fused_event(fe)

                # Create/update event
                event = event_manager.process_fused_event(fe)
                if event:
                    save_event(event)

                    # Issue warning if probability high
                    if fe.fused_probability >= 0.70:
                        level = "WARNING" if fe.fused_probability >= 0.70 else "WATCH"
                        if fe.fused_probability >= 0.90:
                            level = "CRITICAL"
                        warning = warning_manager.issue_warning(
                            event.event_id, level, fe.fused_probability, fe.stations
                        )
                        if warning:
                            save_warning(warning)
                            log.info("Warning %s: %s (P=%.4f)", warning.warning_id[:8], level, fe.fused_probability)

            log.info("Fusion cycle: %d predictions -> %d fused events", len(sp_list), len(fused_events))

        except Exception as e:
            log.error("Fusion cycle error: %s", str(e)[:200])

    def _housekeeping(self):
        """Close old events."""
        try:
            from collector.db import get_pool
            import psycopg2.extras
            pool = get_pool()
            if not pool:
                return
            with pool.getconn() as conn:
                try:
                    with conn.cursor() as cur:
                        # Close events older than 24h
                        cur.execute("""
                            UPDATE events SET state='CLOSED', updated_at=NOW()
                            WHERE state NOT IN ('CLOSED', 'EXPIRED')
                            AND updated_at < NOW() - INTERVAL '24 hours'
                        """)
                        if cur.rowcount:
                            log.info("Closed %d stale events", cur.rowcount)
                        conn.commit()
                finally:
                    pool.putconn(conn)
        except Exception as e:
            log.warning("Housekeeping: %s", str(e)[:100])
