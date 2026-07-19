#!/usr/bin/env python3

import sys
from pathlib import Path
import numpy as np

ROOT = Path("/opt/pimes")

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "intial"))
sys.path.insert(0, str(ROOT / "laws/preprocessing_bundle/data_fetching"))

from geomagnetic_fetcher import fetch_local_data
from read_mdata import read_604rcsv_new_python

reader = read_604rcsv_new_python(
    2025,
    1,
    1,
    "ALR",
    "/tmp/alr_check"
)

fetcher = fetch_local_data(
    "2025-01-01",
    "ALR"
)

pairs = [
    ("H", reader["H"], fetcher["Hcomp"]),
    ("D", reader["D"], fetcher["Dcomp"]),
    ("Z", reader["Z"], fetcher["Zcomp"]),
]

for name, a, b in pairs:

    print("=" * 60)
    print(name)
    print("=" * 60)

    mask = np.isfinite(a) & np.isfinite(b)

    a = a[mask]
    b = b[mask]

    print("Reader mean :", np.mean(a))
    print("Fetcher mean:", np.mean(b))

    print("Reader std :", np.std(a))
    print("Fetcher std:", np.std(b))

    print("MAE :", np.mean(np.abs(a-b)))
    print("RMSE:", np.sqrt(np.mean((a-b)**2)))

    print("Exact:", np.array_equal(a,b))
    print("Close:", np.allclose(a,b))
