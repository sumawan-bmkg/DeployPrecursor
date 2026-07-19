"""SEOS Configuration."""
from pathlib import Path

SSH_HOST = "10.20.229.43"
SSH_USER = "bmkg"
SSH_PASS = "precursor@admin2026!"
API_HOST = "10.20.229.43:8500"

BASE = Path(__file__).parent.parent.parent
SEOS_DIR = BASE / "validation" / "seos"
DATA_DIR = SEOS_DIR / "evidence_db"
LEDGER_DIR = SEOS_DIR / "ledger"
PROVENANCE_DIR = SEOS_DIR / "provenance"
REPORTS_DIR = SEOS_DIR / "reports"

# CSQ scores feed into SEOS
CSQ_DATA = BASE / "validation" / "csq" / "data"

# Fingerprint stages
PIPELINE_STAGES = [
    "raw", "qc", "pc3", "cwt", "scalogram",
    "tensor", "feature", "embedding", "inference", "prediction",
]

# Weights for SAI
SAI_WEIGHTS = {
    "scientific_integrity": 0.20,
    "engineering_reliability": 0.15,
    "infrastructure_stability": 0.10,
    "evidence_completeness": 0.15,
    "governance_compliance": 0.10,
    "operational_stability": 0.15,
    "drift_health": 0.10,
    "release_readiness": 0.05,
}
