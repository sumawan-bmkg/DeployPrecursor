"""CSQ Scheduler — main orchestrator, runs all phases sequentially."""
import time, traceback
from . import config
from .utils import ensure_dirs
from .collector import audit as collector_audit
from .runtime import audit as runtime_audit
from .prediction import audit as prediction_audit
from .drift import audit as drift_audit
from .dashboard import audit as dashboard_audit
from .qualification import run as qualification_run
from .erb import update as erb_update
from .shadow import evaluate as shadow_evaluate
from .report import generate_daily
from .certificate import generate as cert_generate

def run_once():
    """Execute one full CSQ cycle. Graceful failure per phase."""
    ensure_dirs()
    print(f"\n{'='*50}")
    print(f"CSQ Audit Cycle — {__import__('datetime').datetime.utcnow().isoformat()}Z")
    print(f"{'='*50}")

    scores = {}

    for name, fn in [
        ("collector", collector_audit),
        ("runtime", runtime_audit),
        ("prediction", prediction_audit),
        ("drift", drift_audit),
        ("dashboard", dashboard_audit),
    ]:
        try:
            result = fn()
            scores[name] = result.get("score", 0)
        except Exception as e:
            print(f"  {name}: FAILED — {e}")
            scores[name] = 0
            # Log failure as evidence
            from .utils import log_entry
            log_entry(config.DATA_DIR / "audit_log.jsonl", f"{name.upper()}_FAIL", 0, {"error": str(e)})

    # Qualification
    try:
        qual = qualification_run(scores)
    except Exception as e:
        print(f"  qualification: FAILED — {e}")
        qual = {"overall": 0, "components": scores}

    # ERB
    try:
        erb_update(qual, scores)
    except Exception as e:
        print(f"  ERB: FAILED — {e}")

    # Shadow
    try:
        drift_data = {}
        try: drift_data = __import__("json").loads((config.DATA_DIR / "drift_score.json").read_text())
        except: pass
        shadow_result = shadow_evaluate(scores, drift_data)
    except Exception as e:
        print(f"  Shadow: FAILED — {e}")
        shadow_result = {"recommendation": "ERROR"}

    # Daily report
    try:
        generate_daily(scores, drift_data, shadow_result)
    except Exception as e:
        print(f"  Report: FAILED — {e}")

    # Certificate
    try:
        cert_generate(qual, shadow_result)
    except Exception as e:
        print(f"  Certificate: FAILED — {e}")

    print(f"\n{'='*50}")
    print(f"CSQ COMPLETE — Overall: {scores.get('overall', 0):.1f}%")
    print(f"{'='*50}\n")
    return scores
