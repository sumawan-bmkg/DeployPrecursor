"""SEOS Recommendation Engine — evidence-based, never hardcoded."""
import json
from .config import PROVENANCE_DIR
from .utils import now_iso, sf
from . import ledger

RECOMMENDATION_RULES = {
    ("collector", "CRITICAL"): {
        "cause": "Collector failure rate exceeded threshold",
        "action": "Check SSH connectivity, verify remote data availability, restart collector",
    },
    ("collector", "WARNING"): {
        "cause": "Collector performance degraded",
        "action": "Monitor queue depth, check for network latency",
    },
    ("prediction", "CRITICAL"): {
        "cause": "Prediction score below minimum threshold",
        "action": "Verify checkpoint integrity, check tensor pipeline, review inference logs",
    },
    ("prediction", "WARNING"): {
        "cause": "Prediction confidence trending down",
        "action": "Review recent drift analysis, check feature extraction pipeline",
    },
    ("runtime", "CRITICAL"): {
        "cause": "Multiple pipeline stages unhealthy",
        "action": "Check server resources (CPU/RAM/Disk), review process logs",
    },
    ("drift", "WARNING"): {
        "cause": "Statistical drift detected in pipeline metrics",
        "action": "Review rolling statistics, compare with baseline, check data distribution",
    },
    ("infrastructure", "CRITICAL"): {
        "cause": "Infrastructure resource exhaustion",
        "action": "Check disk space, RAM usage, CPU load. Scale if needed.",
    },
    ("dashboard", "WARNING"): {
        "cause": "Dashboard pages not responding",
        "action": "Check FastAPI process, verify template rendering, check API endpoints",
    },
}

def generate_recommendations(scores: dict, drifts: list) -> list:
    """Generate recommendations based on evidence."""
    recs = []
    for component, score in scores.items():
        s = sf(score)
        if s < 30:
            severity = "CRITICAL"
        elif s < 60:
            severity = "WARNING"
        elif s < 80:
            severity = "INFO"
        else:
            continue

        key = (component, severity)
        rule = RECOMMENDATION_RULES.get(key, {
            "cause": f"{component} score below optimal ({s:.1f}%)",
            "action": f"Investigate {component} component and review recent changes",
        })

        rec_id = ledger.insert("recommendations", {
            "component": component, "severity": severity,
            "cause": rule["cause"], "confidence": max(0.5, 1.0 - s / 200),
            "action": rule["action"],
            "evidence_ref": f"score={s:.1f}%",
        })
        recs.append({"id": rec_id, "component": component, "severity": severity, **rule})

    # Drift-based recommendations
    for d in (drifts if isinstance(drifts, list) else []):
        if d.get("status") in ("WARNING", "CRITICAL"):
            rec_id = ledger.insert("recommendations", {
                "component": d.get("name", "unknown"), "severity": d.get("status"),
                "cause": f"Drift detected: trend={d.get('trend', 0):+.2f}",
                "confidence": 0.7, "action": "Review time-series data and check for data distribution shift",
                "evidence_ref": f"drift={d.get('drift', 0):.2f}",
            })
            recs.append({"id": rec_id, **d})

    return recs
