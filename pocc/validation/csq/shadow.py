"""CSQ Shadow Qualification — Phase 8."""
import json
from .config import DATA_DIR, REPORTS_DIR, EVIDENCE_DIR, THRESHOLDS
from .utils import sf, now_iso, log_entry

def evaluate(scores: dict, drift: dict):
    overall = scores.get("overall", 0)
    shadow_ready = overall >= THRESHOLDS["shadow_ready"]
    prod_ready = overall >= THRESHOLDS["production_ready"]

    result = {
        "ts": now_iso(),
        "overall": sf(overall),
        "shadow_ready": shadow_ready,
        "production_ready": prod_ready,
        "components": scores,
        "drift_status": drift.get("status", "UNKNOWN"),
    }

    rec = "READY FOR PRODUCTION" if prod_ready else \
          "READY FOR SHADOW" if shadow_ready else "NOT READY"
    result["recommendation"] = rec

    # Write shadow readiness
    shadow_md = f"""# Shadow Qualification Report

Generated: {now_iso()}

## Overall Score: {overall:.1f}%

## Recommendation: **{rec}**

## Readiness
| Gate | Status |
|------|--------|
| Shadow Ready | {'PASS' if shadow_ready else 'FAIL'} (threshold: {THRESHOLDS['shadow_ready']}%) |
| Production Ready | {'PASS' if prod_ready else 'FAIL'} (threshold: {THRESHOLDS['production_ready']}%) |
| Drift Status | {result['drift_status']} |

## Component Scores
| Component | Score | Status |
|-----------|-------|--------|
"""
    for k, v in sorted(scores.items(), key=lambda x: -x[1]):
        s = sf(v)
        status = "PASS" if s >= 80 else "MONITOR" if s >= 50 else "BLOCKED"
        shadow_md += f"| {k.title()} | {s:.1f}% | {status} |\n"

    shadow_md += f"""
## Shadow Mode Instructions
If READY FOR SHADOW:
1. Deploy to shadow environment
2. Run 7-14 days with live BMKG data
3. CSQ will auto-track prediction vs actual events
4. When all gates pass → Production

If NOT READY:
1. Investigate blocked components
2. Fix underlying issues
3. Re-run CSQ audit
"""
    (REPORTS_DIR / "SHADOW_QUALIFICATION.md").write_text(shadow_md, encoding="utf-8")
    (EVIDENCE_DIR / "shadow_readiness.json").write_text(json.dumps(result, indent=2))
    log_entry(DATA_DIR / "audit_log.jsonl", "SHADOW", overall, {"rec": rec})
    print(f"  Shadow: {rec}")
    return result
