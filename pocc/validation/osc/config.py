"""OSC Config — paths and constants."""
from pathlib import Path

# Remote paths (runs on Ubuntu server)
POCC = Path("/opt/pimes/pocc")
PDAC = Path("/opt/pimes/laws/runtime/validation/pdac")
RDMC = Path("/opt/pimes/laws/runtime/validation/rdmc")
BURNIN = Path("/opt/pimes/laws/runtime/validation/burnin")
PSEP = Path("/opt/pimes/laws/runtime/validation/psep")

OSC_DIR = Path("/opt/pimes/posc/osc")  # where data lives on server
API = "http://127.0.0.1:8500"
OBSERVATION_PERIOD_DAYS = 14
REPORTS = OSC_DIR / "reports"
DATA = OSC_DIR / "data"
BASELINE = OSC_DIR / "baseline"
FINAL_PACKAGE = OSC_DIR / "FINAL_OPERATIONAL_CAMPAIGN"
