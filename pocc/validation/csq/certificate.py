"""CSQ Certificate Generator — Phase 10."""
import json
from .config import DATA_DIR, REPORTS_DIR, EVIDENCE_DIR
from .utils import sf, now_iso, new_uuid, sha256_str, log_entry

def generate(qualification: dict, shadow: dict):
    uid = new_uuid()
    now = now_iso()
    overall = qualification.get("overall", 0)

    cert = f"""# Scientific Operational Certificate

**Certificate UUID:** {uid}
**Generated:** {now}
**Framework:** CSQ Engine v1.0

---

## Release Identity

| Field | Value |
|-------|-------|
| Certificate UUID | {uid} |
| Timestamp (UTC) | {now} |
| Overall Score | {overall:.1f}% |
| Manifest SHA256 | {sha256_str(json.dumps(qualification))[:16]} |

---

## Qualification Scores

| Domain | Score |
|--------|-------|
"""
    for k, v in sorted(qualification.get("components", {}).items(), key=lambda x: -x[1]):
        cert += f"| {k.title()} | {sf(v):.1f}% |\n"

    cert += f"""
---

## Scientific Verdict

| Gate | Result |
|------|--------|
| Shadow Ready | {shadow.get('shadow_ready', False)} |
| Production Ready | {shadow.get('production_ready', False)} |
| Recommendation | {shadow.get('recommendation', 'PENDING')} |

---

## Attestation

I certify that this Scientific Operational Certificate is based on
evidence collected by the CSQ Engine v1.0. No scientific modifications
were made. All scores are derived from live operational data.

**Operator:** CSQ Engine (automated)
**Generated:** {now}
"""
    (REPORTS_DIR / "SCIENTIFIC_OPERATIONAL_CERTIFICATE.md").write_text(cert, encoding="utf-8")
    (EVIDENCE_DIR / "certificate.json").write_text(json.dumps({
        "uuid": uid, "ts": now, "overall": sf(overall),
        "shadow_ready": shadow.get("shadow_ready"),
        "prod_ready": shadow.get("production_ready"),
    }, indent=2))
    log_entry(DATA_DIR / "audit_log.jsonl", "CERTIFICATE", overall, {"uuid": uid})
    print(f"  Certificate: {uid[:12]}")
    return uid
