#!/usr/bin/env python3

import numpy as np

from common import *

from read_mdata import read_604rcsv_new_python
from signal_processing import GeomagneticSignalProcessor

raw = read_604rcsv_new_python(
    YEAR,
    MONTH,
    DAY,
    STATION,
    RAW_ROOT
)

processor = GeomagneticSignalProcessor()

mapping = {
    "H": raw["H"],
    "D": raw["D"],
    "Z": raw["Z"],
}

for name, arr in mapping.items():

    clean, mask = processor.handle_gaps(arr)

    print()
    print("=" * 70)
    print(name)
    print("=" * 70)

    print("RAW")
    print("std :", np.nanstd(arr))
    print("mean:", np.nanmean(arr))

    print()

    print("CLEAN")
    print("std :", np.std(clean))
    print("mean:", np.mean(clean))

    print()

    print("Difference")
    print("max :", np.max(np.abs(clean - np.nan_to_num(arr))))
    print("mean:", np.mean(np.abs(clean - np.nan_to_num(arr))))

    print()

    print("Mask valid :", mask.sum())
