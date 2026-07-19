#!/usr/bin/env python3

import numpy as np

from common import *

from read_mdata import read_604rcsv_new_python
from signal_processing import GeomagneticSignalProcessor

processor = GeomagneticSignalProcessor()

raw = read_604rcsv_new_python(
    YEAR,
    MONTH,
    DAY,
    STATION,
    RAW_ROOT
)

processed = processor.process_components(
    raw["H"],
    raw["D"],
    raw["Z"],
    apply_pc3=True
)

mapping = [
    ("H", "h_pc3"),
    ("D", "d_pc3"),
    ("Z", "z_pc3"),
]

for raw_key, proc_key in mapping:

    direct, _ = processor.bandpass_filter(raw[raw_key])
    proc = processed[proc_key]

    print()
    print("=" * 70)
    print(raw_key)
    print("=" * 70)

    print("Direct std :", np.std(direct))
    print("Process std:", np.std(proc))

    print()

    print("MAE  :", np.mean(np.abs(direct - proc)))
    print("RMSE :", np.sqrt(np.mean((direct - proc)**2)))
    print("CORR :", np.corrcoef(direct, proc)[0,1])

    print()

    print("Exact equal :", np.array_equal(direct, proc))
    print("All close   :", np.allclose(direct, proc))
    print("Max diff    :", np.max(np.abs(direct - proc)))
