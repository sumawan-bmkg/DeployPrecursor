"""SOAP Config."""
from pathlib import Path
BASE = Path(__file__).parent.parent.parent
SOAP_DIR = BASE / "validation" / "soap"
REGISTRY_DIR = SOAP_DIR / "registry"
REPORTS_DIR = SOAP_DIR / "reports"
ACCREDITATION_DIR = REPORTS_DIR / "accreditation_package"

# Paths to other modules (read-only)
CSQ_DATA = BASE / "validation" / "csq" / "data"
SEOS_DATA = BASE / "validation" / "seos" / "evidence_db"
SEOS_LEDGER = BASE / "validation" / "seos" / "ledger"
SOQ_REPORTS = BASE / "validation" / "soq" / "reports"
OSRV_REPORTS = BASE / "validation" / "osrv" / "reports"

SSH_HOST = "10.20.229.43"
SSH_USER = "bmkg"
SSH_PASS = "precursor@admin2026!"
API_HOST = "10.20.229.43:8500"
