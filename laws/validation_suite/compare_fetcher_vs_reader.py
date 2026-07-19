from datetime import datetime
import numpy as np
import sys

# supaya import intial.* berhasil

import sys

# Root project
sys.path.insert(0, "/opt/pimes")

# Folder intial agar import "read_mdata" berhasil
sys.path.insert(0, "/opt/pimes/intial")

from intial.geomagnetic_fetcher import GeomagneticDataFetcher
from intial.read_mdata import read_604rcsv_new_python

print("=" * 70)
print("LOADING DATA")
print("=" * 70)

reader = read_604rcsv_new_python(
    2025,
    1,
    1,
    "ALR",
    "/tmp/alr_check"
)

with GeomagneticDataFetcher(use_local=True) as fetcher:
    fetched = fetcher.fetch_data(
        datetime(2025, 1, 1),
        "ALR"
    )

print()

mapping = [
    ("H", "Hcomp"),
    ("D", "Dcomp"),
    ("Z", "Zcomp"),
]

for r_key, f_key in mapping:

    print("=" * 70)
    print(r_key)
    print("=" * 70)

    a = np.asarray(reader[r_key], dtype=np.float64)
    b = np.asarray(fetched[f_key], dtype=np.float64)

    print("Reader shape :", a.shape)
    print("Fetcher shape:", b.shape)

    mask = np.isfinite(a) & np.isfinite(b)

    a = a[mask]
    b = b[mask]

    print("Reader mean :", np.mean(a))
    print("Fetcher mean:", np.mean(b))

    print("Reader std :", np.std(a))
    print("Fetcher std:", np.std(b))

    print("MAE :", np.mean(np.abs(a - b)))
    print("RMSE:", np.sqrt(np.mean((a - b) ** 2)))

    print("CORR:", np.corrcoef(a, b)[0, 1])

    print("Exact:", np.array_equal(a, b))
    print("Close:", np.allclose(a, b))
