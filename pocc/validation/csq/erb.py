"""CSQ Living ERB — Phase 7: always-current evidence review board."""
import json
from .config import DATA_DIR, REPORTS_DIR, EVIDENCE_DIR
from .utils import sf, now_iso, sha256_str, new_uuid, log_entry

def update(qualification: dict, scores: dict):
    uid = new_uuid()
    now = now_iso()
    overall = qualification.get("overall", 0)

    # Read last drift
    drift_data = {}
    try: drift_data = json.loads((DATA_DIR / "drift_score.json").read_text())
    except: pass

    erb = {
        "erb_uuid": uid,
        "timestamp": now,
        "overall_score": sf(overall),
        "component_scores": scores,
        "drift_status": drift_data.get("status", "UNKNOWN"),
        "shadow_readiness": overall >= 75.0,
        "production_readiness": overall >= 85.0,
        "manifest_sha256": sha256_str(json.dumps(qualification)),
    }

    # Write ERB files
    (DATA_DIR / "erb_manifest.json").write_text(json.dumps(erb, indent=2))
    (EVIDENCE_DIR / "erb_manifest.json").write_text(json.dumps(erb, indent=2))

    # ERB summary
    shadow = "YES" if erb["shadow_readiness"] else "NO"
    prod = "YES" if erb["production_readiness"] else "NO"
    summary = f"""# Living ERB Summary

Last Updated: {now}
ERB UUID: {uid}

## Overall Score: {overall:.1f}%

## Component Scores
| Component | Score | Weight |
|-----------|-------|--------|
"""
    from .config import WEIGHTS
    for k, v in sorted(scores.items(), key=lambda x: -x[1]):
        w = WEIGHTS.get(k, 0)
        summary += f"| {k.title()} | {sf(v):.1f}% | {w*100:.0f}% |\n"

    summary += f"""
## Readiness
- Shadow Ready: **{shadow}**
- Production Ready: **{prod}**
- Drift Status: {erb['drift_status']}

## Manifest SHA256
{erb['manifest_sha256']}
"""
    (REPORTS_DIR / "ERB_SUMMARY.md").write_text(summary, encoding="utf-8")
    (EVIDENCE_DIR / "ERB_SUMMARY.md").write_text(summary, encoding="utf-8")
    log_entry(DATA_DIR / "audit_log.jsonl", "ERB_UPDATE", overall, {"uid": uid})
    print(f"  ERB: updated (uuid={uid[:12]}, overall={overall:.1f}%)")
    return erb
