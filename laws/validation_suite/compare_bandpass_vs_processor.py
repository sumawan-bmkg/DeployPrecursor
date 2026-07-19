#!/usr/bin/env python3

import numpy as np
from scipy import signal

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

processed = processor.process_components(
    raw["H"],
    raw["D"],
    raw["Z"],
    apply_pc3=True
)

fs = 1.0

low = 0.022/(fs/2)
high = 0.10/(fs/2)

b,a = signal.butter(4,[low,high],btype="band")

mapping = {
    "H": "h_pc3",
    "D": "d_pc3",
    "Z": "z_pc3",
}

for ch in ["H","D","Z"]:

    x = raw[ch]
    x = np.nan_to_num(x, nan=np.nanmean(x))

    y_manual = signal.filtfilt(b,a,x)

    y_proc = processed[mapping[ch]]

    print()
    print("="*70)
    print(ch)
    print("="*70)

    print("manual std :", np.std(y_manual))
    print("proc   std :", np.std(y_proc))

    print("MAE  :", np.mean(np.abs(y_manual-y_proc)))
    print("RMSE :", np.sqrt(np.mean((y_manual-y_proc)**2)))
    print("CORR :", np.corrcoef(y_manual,y_proc)[0,1])
