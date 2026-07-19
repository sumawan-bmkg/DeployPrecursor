#!/usr/bin/env python3

from common import *

import numpy as np

from scipy import signal

from signal_processing import GeomagneticSignalProcessor

from read_mdata import read_604rcsv_new_python

processor = GeomagneticSignalProcessor()

raw = read_604rcsv_new_python(
    YEAR,
    MONTH,
    DAY,
    STATION,
    RAW_ROOT
)

def manual_filter(x):

    clean, _ = processor.handle_gaps(x)

    nyquist = processor.fs / 2.0

    low = processor.pc3_low / nyquist

    high = processor.pc3_high / nyquist

    b, a = signal.butter(
        4,
        [low, high],
        btype="band"
    )

    return signal.filtfilt(b, a, clean)

def compare(name, raw_signal):

    print()
    print("=" * 70)
    print(name)
    print("=" * 70)

    manual = manual_filter(raw_signal)

    proc, _ = processor.bandpass_filter(raw_signal)

    print("manual std :", manual.std())
    print("proc   std :", proc.std())

    diff = proc - manual

    print()
    print("Difference")

    print("mean :", diff.mean())
    print("std  :", diff.std())
    print("max  :", np.max(np.abs(diff)))

    print()

    print("Correlation")

    print(np.corrcoef(proc, manual)[0,1])

    print()

    print("Exact equal")

    print(np.array_equal(proc, manual))

    print()

    print("All close")

    print(np.allclose(proc, manual))

compare("H", raw["H"])

compare("D", raw["D"])

compare("Z", raw["Z"])


