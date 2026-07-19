#!/usr/bin/env python3

from pathlib import Path
import sys
import numpy as np

# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = Path("/opt/pimes/laws")

PREPROCESSING = ROOT / "preprocessing_bundle"

CORE = PREPROCESSING / "core"
DATA_FETCHING = PREPROCESSING / "data_fetching"
TENSOR_GENERATION = PREPROCESSING / "tensor_generation"

REFERENCE_NPY = ROOT / "reference_npy"

RAW_DATA = Path("/tmp/alr_check")

RAW_ROOT = "/tmp/alr_check"

# ============================================================
# PYTHON PATH
# ============================================================

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PREPROCESSING))
sys.path.insert(0, str(CORE))
sys.path.insert(0, str(DATA_FETCHING))
sys.path.insert(0, str(TENSOR_GENERATION))

# ============================================================
# CONSTANTS
# ============================================================

YEAR = 2025
MONTH = 1
DAY = 1
STATION = "ALR"

REFERENCE_TENSOR = (
    REFERENCE_NPY /
    "raw_tensor_ALR_1735660800.npy"
)

# ============================================================
# HELPERS
# ============================================================

def header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def stats(name, arr):
    arr = np.asarray(arr)

    print(name)
    print(" shape :", arr.shape)
    print(" dtype :", arr.dtype)
    print(" mean  :", np.nanmean(arr))
    print(" std   :", np.nanstd(arr))
    print(" min   :", np.nanmin(arr))
    print(" max   :", np.nanmax(arr))
    print(" nan   :", np.isnan(arr).sum())
    print(" finite:", np.isfinite(arr).sum())
    print()


print("ROOT =", ROOT)
print("PREPROCESSING =", PREPROCESSING)
