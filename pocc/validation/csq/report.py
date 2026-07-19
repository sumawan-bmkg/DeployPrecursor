"""CSQ Report Generator — Phase 11: daily scientific report."""
import json
from .config import DATA_DIR, REPORTS_DIR, HISTORY_CSV
from .utils import sf, now_iso

def generate_daily(scores: dict, drift: dict, shadow: dict):
    now = now_iso()
    today = now[:10]

    # Read history
    history_points = 0
    if HISTORY_CSV.exists():
        history_points = len(HISTORY_CSV.read_text(encoding="utf-8").strip().split("\n")) - 1

    report = f"""# Daily Scientific Report

**Date:** {today}
**Generated:** {now}
**Framework:** CSQ v1.0

---

## Executive Summary

Overall Qualification Score: **{sf(scores.get('overall', 0)):.1f}%**
Recommendation: **{shadow.get('recommendation', 'PENDING')}**
Drift Status: {drift.get('status', 'UNKNOWN')}
History Points: {history_points}

---

## Component Scores

| Component | Score | Status |
|-----------|-------|--------|
"""
    for k, v in sorted(scores.items(), key=lambda x: -x[1]):
        s = sf(v)
        status = "PASS" if s >= 80 else "MONITOR" if s >= 50 else "BLOCKED"
        report += f"| {k.title()} | {s:.1f}% | {status} |\n"

    report += f"""
---

## Drift Analysis

| Metric | Status | Trend |
|--------|--------|-------|
"""
    for d in drift.get("drifts", []):
        report += f"| {d.get('name','?')} | {d.get('status','?')} | {d.get('trend',0):+.2f} |\n"

    report += f"""
---

## Readiness Gates

| Gate | Threshold | Status |
|------|-----------|--------|
| Shadow | 75% | {'PASS' if shadow.get('shadow_ready') else 'BLOCKED'} |
| Production | 85% | {'PASS' if shadow.get('production_ready') else 'BLOCKED'} |

---

## Recommendations

"""
    recs = []
    for k, v in scores.items():
        s = sf(v)
        if s < 50:
            recs.append(f"- **CRITICAL:** {k.title()} score {s:.1f}% — investigate immediately")
        elif s < 70:
            recs.append(f"- **WARNING:** {k.title()} score {s:.1f}% — monitor closely")
        elif s < 80:
            recs.append(f"- **INFO:** {k.title()} score {s:.1f}% — room for improvement")

    if not recs:
        recs.append("- All components within acceptable range. Continue monitoring.")

    report += "\n".join(recs)
    report += f"""

---

*This report is generated automatically by CSQ Engine v1.0*
*Next audit scheduled: hourly via cron*
"""

    path = REPORTS_DIR / f"DAILY_SCIENTIFIC_REPORT_{today}.md"
    path.write_text(report, encoding="utf-8")
    print(f"  Daily report: {path.name}")
    return report
