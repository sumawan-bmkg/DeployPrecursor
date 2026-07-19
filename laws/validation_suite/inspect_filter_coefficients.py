#!/usr/bin/env python3

import numpy as np
from scipy import signal

from common import *
from signal_processing import GeomagneticSignalProcessor

processor = GeomagneticSignalProcessor()

nyquist = processor.fs / 2.0

low = processor.pc3_low / nyquist
high = processor.pc3_high / nyquist

b, a = signal.butter(
    4,
    [low, high],
    btype="band"
)

header("FILTER PARAMETERS")

print("fs      :", processor.fs)
print("nyquist :", nyquist)
print("low     :", low)
print("high    :", high)

header("b")

print(b)

header("a")

print(a)

w, h = signal.freqz(b, a, worN=4096)

freq = w * processor.fs / (2*np.pi)

header("GAIN")

for f in [0.005,0.01,0.022,0.03,0.05,0.08,0.10,0.15]:

    idx = np.argmin(np.abs(freq-f))

    gain = np.abs(h[idx])

    print(f"{f:7.3f} Hz : {gain:.6f}")
