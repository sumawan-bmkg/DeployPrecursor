#!/usr/bin/env python3

import numpy as np
from scipy import signal

from common import *
from read_mdata import read_604rcsv_new_python

raw = read_604rcsv_new_python(
    YEAR,
    MONTH,
    DAY,
    STATION,
    RAW_ROOT
)

fs = 1.0

low = 0.022 / (fs / 2.0)
high = 0.10 / (fs / 2.0)

b, a = signal.butter(4, [low, high], btype="band")

channels = [
    ("H", raw["H"]),
    ("D", raw["D"]),
    ("Z", raw["Z"]),
]

for name, x in channels:

    print()
    print("=" * 70)
    print(name)
    print("=" * 70)

    x = np.asarray(x, dtype=float)
    x = np.nan_to_num(x, nan=np.nanmean(x))

    y = signal.filtfilt(b, a, x)

    print("Input std  :", np.std(x))
    print("Output std :", np.std(y))
    print("Gain       :", np.std(y) / np.std(x))
