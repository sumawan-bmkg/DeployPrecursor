"""CSQ Configuration — all paths, hosts, weights."""
from pathlib import Path

# Remote
SSH_HOST = "10.20.229.43"
SSH_USER = "bmkg"
SSH_PASS = "precursor@admin2026!"
API_HOST = "10.20.229.43:8500"

# Paths (remote, used via SSH)
PDAC = Path("/opt/pimes/laws/runtime/validation/pdac")
RDMC = Path("/opt/pimes/laws/runtime/validation/rdmc")
BURNIN = Path("/opt/pimes/laws/runtime/validation/burnin")
PSEP = Path("/opt/pimes/laws/runtime/validation/psep")
SHADOW = Path("/opt/pimes/laws/runtime/validation/shadow")

# Paths (local)
BASE = Path(__file__).parent.parent.parent  # pocc/
CSQ_DIR = BASE / "validation" / "csq"
DATA_DIR = CSQ_DIR / "data"
REPORTS_DIR = CSQ_DIR / "reports"
EVIDENCE_DIR = CSQ_DIR / "evidence"
HISTORY_CSV = DATA_DIR / "qualification_history.csv"
AUDIT_LOG = DATA_DIR / "audit_log.jsonl"

# Weights
WEIGHTS = {
    "collector": 0.15,
    "runtime": 0.10,
    "prediction": 0.15,
    "infrastructure": 0.10,
    "dashboard": 0.10,
    "engineering": 0.10,
    "release": 0.05,
    "governance": 0.05,
    "burnin": 0.10,
    "drift": 0.10,
}

# Thresholds
THRESHOLDS = {
    "shadow_ready": 75.0,
    "production_ready": 85.0,
    "min_component": 50.0,
    "drift_warning": 5.0,
    "drift_critical": 10.0,
    "stability_min": 20,
}

# Pages
DASHBOARD_PAGES = [
    "/", "/engineering", "/scientific-ops", "/pipeline-runtime",
    "/mission-timeline", "/alert-center", "/evidence-center",
    "/release-center", "/executive-center", "/digitaltwin", "/governance",
]
