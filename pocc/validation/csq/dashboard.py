"""CSQ Dashboard Audit — Phase 9."""
import json
from .config import API_HOST, DASHBOARD_PAGES, DATA_DIR, EVIDENCE_DIR
from .utils import sf, now_iso, local_api, log_entry

def audit():
    results = {}
    up = 0
    for p in DASHBOARD_PAGES:
        code = local_api(p)
        ok = code.strip() in ("200", "201") if code else False
        results[p] = {"http": code.strip(), "ok": ok}
        if ok: up += 1

    score = sf(up / max(len(DASHBOARD_PAGES), 1) * 100)

    result = {
        "ts": now_iso(), "score": score,
        "pages_total": len(DASHBOARD_PAGES), "pages_up": up,
        "pages": results,
    }
    (DATA_DIR / "dashboard_score.json").write_text(json.dumps(result, indent=2))
    (EVIDENCE_DIR / "dashboard_score.json").write_text(json.dumps(result, indent=2))
    log_entry(DATA_DIR / "audit_log.jsonl", "DASHBOARD", score, {"up": up, "total": len(DASHBOARD_PAGES)})
    print(f"  Dashboard: {score:.1f}% ({up}/{len(DASHBOARD_PAGES)} pages)")
    return result
