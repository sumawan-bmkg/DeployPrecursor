#!/usr/bin/env python3

import numpy as np

from common import *
from read_mdata import read_604rcsv_new_python


raw = read_604rcsv_new_python(
    YEAR,
    MONTH,
   DAY,
    STATION,
    RAW_ROOT
)

channels = [
    ("H", raw["H"]),
    ("D", raw["D"]),
    ("Z", raw["Z"])
]

for name, x in channels:

    print()
    print("="*70)
    print(name)
    print("="*70)

    x = np.asarray(x, dtype=float)

    x = np.nan_to_num(x, nan=np.nanmean(x))

    x = x - np.mean(x)

    fft = np.fft.rfft(x)

    freq = np.fft.rfftfreq(len(x), d=1.0)

    power = np.abs(fft)**2

    total = np.sum(power)

    pc3 = (freq >= 0.022) & (freq <= 0.10)

    pc3_energy = np.sum(power[pc3])

    print("Total FFT Energy :", total)
    print("PC3 FFT Energy   :", pc3_energy)
    print("Ratio            :", pc3_energy / total)
