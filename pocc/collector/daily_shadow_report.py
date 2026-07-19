#!/usr/bin/env python3
"""P7B — Daily Shadow Report Generator."""
import os, sys, json, time
sys.path.insert(0, r'd:\opt\pimes\pocc\collector')
sys.path.insert(0, r'd:\opt\pimes\1dep_ready\laws\preprocessing_bundle\data_fetching')

from replay_engine import ReplayEngine, ModelComparer
from mock_predictor import MockPredictor


class DailyShadowReport:
    """Generate structured daily report from shadow mode execution."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate(self, year: int, month: int, day: int,
                 stations: list[str],
                 backends: list[tuple[str, object]] = None) -> str:
        date_str = f"{year}-{month:02d}-{day:02d}"
        backends = backends or [("Mock", MockPredictor(mode="deterministic"))]

        all_reports = {}
        for bname, backend in backends:
            engine = ReplayEngine(
                output_dir=os.path.join(self.output_dir, bname),
                predictor=backend
            )
            report = engine.run(year, month, day, stations,
                                earthquake_fetch=True)
            all_reports[bname] = report

        # Markdown summary
        lines = []
        lines.append(f"# Shadow Report — {date_str}")
        lines.append("")
        lines.append(f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime())}Z")
        lines.append("")

        for bname, report in all_reports.items():
            m = report.get("metrics", {})
            gt = report.get("ground_truth", {})
            drift = report.get("drift", {}).get("any_drift", False)
            lines.append(f"## Backend: {bname}")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Stations processed | {report.get('stations_processed', '?')} |")
            lines.append(f"| Precision | {m.get('precision', '?')} |")
            lines.append(f"| Recall | {m.get('recall', '?')} |")
            lines.append(f"| FAR | {m.get('far', '?')} |")
            lines.append(f"| Miss Rate | {m.get('miss_rate', '?')} |")
            lines.append(f"| Brier Score | {m.get('brier_score', '?')} |")
            lines.append(f"| Mean Probability | {m.get('mean_probability', '?')} |")
            lines.append(f"| Mean Uncertainty | {m.get('mean_uncertainty', '?')} |")
            lines.append(f"| Mean Latency | {m.get('mean_latency_ms', '?')} ms |")
            lines.append(f"| EQ Events (global) | {gt.get('total_events', '?')} |")
            lines.append(f"| Drift Alert | {'YES' if drift else 'NO'} |")
            lines.append("")

        # Health
        n_total = len(stations)
        lines.append("## System Health")
        lines.append("")
        for bname, report in all_reports.items():
            n_processed = report.get("stations_processed", 0)
            coverage = n_processed / n_total if n_total else 0
            lines.append(f"- **{bname}**: {n_processed}/{n_total} stations ({coverage:.0%})")
        lines.append("")

        fp = os.path.join(self.output_dir, f"shadow_report_{date_str}.md")
        with open(fp, "w") as f:
            f.write("\n".join(lines))
        print(f"Report: {fp}")
        return fp
