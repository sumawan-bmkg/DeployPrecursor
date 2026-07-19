#!/usr/bin/env python3
"""P7B — Replay Engine: re-run any date with any predictor backend."""
import os, sys, json, time
sys.path.insert(0, r'd:\opt\pimes\pocc\collector')
sys.path.insert(0, r'd:\opt\pimes\1dep_ready\laws\preprocessing_bundle\data_fetching')

from read_mdata import read_604rcsv_new_python
from mock_predictor import MockPredictor
from laws_adapter import LAWSPredictor, EnsemblePredictor
from predictor_base import PredictionAudit, Prediction, PredictorInterface
from metrics_engine import MetricsEngine
from drift_monitor import DriftMonitor
from ground_truth import GroundTruthCollector


class ReplayEngine:
    """Replay one or more days through the pipeline for evaluation."""

    def __init__(self, output_dir: str, predictor: PredictorInterface = None):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.predictor = predictor or MockPredictor(mode="deterministic")
        self.audit = PredictionAudit(audit_dir=os.path.join(output_dir, "audit"))
        self.metrics = MetricsEngine(output_dir=os.path.join(output_dir, "metrics"))
        self.drift = DriftMonitor(output_dir=os.path.join(output_dir, "drift"))
        self.gt = GroundTruthCollector(min_magnitude=4.0)

    def run(self, year: int, month: int, day: int, stations: list[str],
            data_root: str = r'd:\opt\pimes\data\raw',
            earthquake_fetch: bool = False) -> dict:
        """Replay one day. Returns full report."""
        from qc_orchestrator import QCOrchestrator
        import shutil

        BASE = r'd:\opt\pimes\pocc\collector'
        for dp in ['scientific_qg/__pycache__', 'scientific_qg/rules/__pycache__']:
            shutil.rmtree(os.path.join(BASE, dp), ignore_errors=True)

        orch = QCOrchestrator()
        date_str = f"{year}-{month:02d}-{day:02d}"
        predictions = []

        for stn in stations:
            try:
                data = read_604rcsv_new_python(year, month, day, stn, data_root)
            except Exception:
                continue

            H, D, Z = data['H'], data['D'], data['Z']

            class Ctx:
                pass
            ctx = Ctx()
            qc = orch.evaluate_and_decide(stn, H, D, Z)
            ctx.score = qc['qc_result'].score
            ctx.severity = qc['qc_result'].severity
            ctx.passed = qc['qc_result'].passed
            ctx.station = stn

            pred = self.predictor.predict(ctx)
            predictions.append(pred)

            self.audit.log(pred, qc_score=ctx.score, input_hash=pred.input_hash)
            self.metrics.record(pred, ground_truth=False, eq_matched=False)
            self.drift.record(pred)

        # Metrics report
        mfp = self.metrics.save_metrics(f"metrics_{date_str}.json")
        dftp = self.drift.save_report(f"drift_{date_str}.json")

        # Ground truth
        events = []
        if earthquake_fetch:
            events = self.gt.fetch_events(date_str, f"{year}-{month:02d}-{day+1:02d}")

        report = {
            "date": date_str,
            "stations_processed": len(predictions),
            "n_predictions": len(predictions),
            "metrics": json.load(open(mfp)),
            "drift": json.load(open(dftp)),
            "ground_truth": {
                "fetched": earthquake_fetch,
                "total_events": len(events),
            },
            "predictor": self.predictor.get_name(),
            "completed_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        }

        fp = os.path.join(self.output_dir, f"replay_report_{date_str}.json")
        with open(fp, "w") as f:
            json.dump(report, f, indent=2)
        return report


class ModelComparer:
    """Run multiple predictors side-by-side and compare outputs."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def compare(self, backends: list[tuple[str, PredictorInterface]],
                ctx, station: str) -> dict:
        """Run all backends on same context, return comparison."""
        results = []
        for name, predictor in backends:
            pred = predictor.predict(ctx)
            results.append({
                "backend": name,
                "model_name": pred.model_name,
                "model_version": pred.model_version,
                "probability": pred.probability,
                "confidence": pred.confidence,
                "uncertainty": pred.uncertainty,
                "latency_ms": pred.latency_ms,
                "explanation": pred.explanation,
                "prediction_hash": pred.prediction_hash,
            })
        return {
            "station": station,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            "results": results,
        }
