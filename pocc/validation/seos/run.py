"""SEOS Runner — Milestone 1: Provenance + Fingerprint + Ledger + Evidence + SAI.

Usage: python -m validation.seos
"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from validation.seos.utils import now_iso, ensure_dirs, local_curl, ssh_client, remote_cat
from validation.seos import ledger
from validation.seos.provenance import build_lineage, save_lineage
from validation.seos.fingerprint import build_from_stages
from validation.seos.evidence_db import record_evidence, build_from_csq, summary as ev_summary
from validation.seos.recommendation import generate_recommendations
from validation.seos.accreditation import compute as compute_sai
from validation.seos.config import SEOS_DIR, REPORTS_DIR

def run():
    ensure_dirs()
    print(f"\n{'='*55}")
    print(f"SEOS v1.0 — Scientific Evidence Operating System")
    print(f"Milestone 1: Provenance + Fingerprint + Ledger + Evidence + SAI")
    print(f"{'='*55}\n")

    # Init ledger
    print("Phase 1: Initializing append-only ledger...")
    ledger.init()
    stats = ledger.stats()
    print(f"  Ledger: {stats}")

    # Collect live data
    print("\nPhase 2: Collecting live system data...")
    try:
        pipeline_raw = local_curl("/api/pipeline/stages")
        pipeline = json.loads(pipeline_raw).get("stages", []) if pipeline_raw else []
        stage_data = {s["id"]: s for s in pipeline}
    except:
        stage_data = {}

    try:
        hm_raw = local_curl("/api/health-model")
        hm = json.loads(hm_raw) if hm_raw else {}
    except:
        hm = {}

    # Provenance
    print("\nPhase 3: Building provenance lineage...")
    try:
        collector_data = {"station": "all", "total_files": sum(s.get("score", 0) for s in pipeline)}
        prediction_data = {"station": "all", "magnitude": 0, "confidence": 0}
        artifacts = build_lineage(collector_data, stage_data, prediction_data)
        chain_id = save_lineage(artifacts)
        print(f"  Provenance: {len(artifacts)} artifacts, chain_id={chain_id}")
        record_evidence("PROVENANCE_BUILT", "provenance", 100, "SUCCESS",
                        details={"chain_id": chain_id, "artifacts": len(artifacts)})
    except Exception as e:
        print(f"  Provenance: FAILED — {e}")
        record_evidence("PROVENANCE_FAIL", "provenance", 0, "FAILED", severity="ERROR",
                        details={"error": str(e)})

    # Fingerprint chain
    print("\nPhase 4: Building fingerprint chain...")
    try:
        chain = build_from_stages(stage_data)
        chain_result = chain.verify()
        print(f"  Fingerprint: {chain_result['entries']} entries, valid={chain_result['valid']}")
        record_evidence("FINGERPRINT_BUILT", "fingerprint", 100 if chain_result["valid"] else 50,
                        "SUCCESS" if chain_result["valid"] else "CHAIN_BROKEN",
                        details=chain_result)
    except Exception as e:
        print(f"  Fingerprint: FAILED — {e}")
        record_evidence("FINGERPRINT_FAIL", "fingerprint", 0, "FAILED", severity="ERROR",
                        details={"error": str(e)})

    # Import CSQ evidence
    print("\nPhase 5: Importing CSQ evidence...")
    try:
        imported = build_from_csq()
        print(f"  CSQ import: {imported} evidence records")
    except Exception as e:
        print(f"  CSQ import: FAILED — {e}")

    # Compute SAI
    print("\nPhase 6: Computing Scientific Accreditation Index...")
    scores = {}
    comps = hm.get("components", {})
    for name, data in comps.items():
        scores[name] = data.get("score", 0)

    # Add non-model scores from CSQ
    from validation.seos.config import CSQ_DATA
    for fname, key in [("collector_score.json", "collector"), ("runtime_score.json", "runtime"),
                        ("dashboard_score.json", "dashboard"), ("drift_score.json", "drift_health")]:
        try:
            d = json.loads((CSQ_DATA / fname).read_text())
            scores[key] = d.get("score", 0)
        except: pass

    # Map to SAI domains
    sai_scores = {
        "scientific_integrity": scores.get("scientific", scores.get("runtime", 0)),
        "engineering_reliability": scores.get("engineering", scores.get("runtime", 0)),
        "infrastructure_stability": scores.get("infrastructure", 0),
        "evidence_completeness": 0,  # filled below
        "governance_compliance": scores.get("governance", 0),
        "operational_stability": scores.get("operational", 0),
        "drift_health": scores.get("drift_health", scores.get("drift", 0)),
        "release_readiness": scores.get("release", 0),
    }
    ev = ev_summary()
    sai_scores["evidence_completeness"] = min(100, ev["total"] * 10)

    sai = compute_sai(sai_scores)

    # Generate recommendations
    print("\nPhase 7: Generating recommendations...")
    try:
        drifts = []
        try:
            drift_data = json.loads((CSQ_DATA / "drift_score.json").read_text())
            drifts = drift_data.get("drifts", [])
        except: pass
        recs = generate_recommendations(scores, drifts)
        print(f"  Recommendations: {len(recs)} generated")
    except Exception as e:
        print(f"  Recommendations: FAILED — {e}")

    # Summary
    ev_sum = ev_summary()
    print(f"\n{'='*55}")
    print(f"SEOS COMPLETE")
    print(f"  SAI: {sai['overall']:.1f}% — {sai['recommendation']}")
    print(f"  Evidence: {ev_sum['json_files']} JSON, {ev_sum['ledger_entries']} ledger")
    print(f"  Ledger: {ledger.stats()}")
    print(f"{'='*55}\n")

if __name__ == "__main__":
    run()
