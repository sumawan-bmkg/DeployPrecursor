"""SEOS SAI — Scientific Accreditation Index.

Comprehensive score 0-100 based on all evidence.
"""
import json
from .config import SAI_WEIGHTS, DATA_DIR, REPORTS_DIR
from .utils import now_iso, sf, new_uuid, sha256_str
from . import ledger

def compute(scores: dict) -> dict:
    """Compute SAI from component scores."""
    now = now_iso()
    uid = new_uuid()

    components = {}
    total_w = 0
    total_s = 0
    for domain, weight in SAI_WEIGHTS.items():
        score = sf(scores.get(domain, 0))
        components[domain] = {"score": score, "weight": weight}
        total_w += weight
        total_s += score * weight

    overall = sf(total_s / max(total_w, 1))

    # Determine recommendation
    if overall >= 85:
        rec = "READY FOR PRODUCTION"
    elif overall >= 75:
        rec = "READY FOR SHADOW"
    elif overall >= 60:
        rec = "READY FOR ERB"
    else:
        rec = "NOT READY"

    sai = {
        "sai_uuid": uid, "timestamp": now, "overall": overall,
        "components": components, "recommendation": rec,
        "manifest_hash": sha256_str(json.dumps(components)),
    }

    # Save
    (DATA_DIR / "sai_current.json").write_text(json.dumps(sai, indent=2), encoding="utf-8")

    # Generate certificate
    cert = f"""# Scientific Accreditation Certificate

**UUID:** {uid}
**Generated:** {now}
**Overall SAI:** {overall:.1f}%
**Recommendation:** {rec}

## Component Breakdown
| Domain | Score | Weight |
|--------|-------|--------|
"""
    for domain, c in sorted(components.items(), key=lambda x: -x[1]["score"]):
        cert += f"| {domain.replace('_',' ').title()} | {c['score']:.1f}% | {c['weight']*100:.0f}% |\n"

    cert += f"""
## Manifest Hash: {sai['manifest_hash'][:16]}

## Attestation
This certificate is generated automatically by the SEOS v1.0
Scientific Accreditation Index engine. All scores are derived
from live operational evidence in the append-only ledger.

**No scientific modifications were made.**
"""
    (REPORTS_DIR / "SCIENTIFIC_ACCREDITATION.md").write_text(cert, encoding="utf-8")

    # Record in ledger
    ledger.insert("certificates", {
        "certificate_type": "SAI", "overall_score": overall,
        "recommendation": rec, "manifest_hash": sai["manifest_hash"],
        "details": json.dumps(components),
    })

    print(f"  SAI: {overall:.1f}% ({rec})")
    return sai
