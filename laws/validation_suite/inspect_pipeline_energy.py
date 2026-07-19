#!/usr/bin/env python3

import numpy as np

from common import *

from read_mdata import read_604rcsv_new_python
from signal_processing import GeomagneticSignalProcessor
from tensor_generator import V2TensorGenerator


def energy(x):
    x = np.asarray(x)
    return np.sum(x.astype(np.float64)**2)


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

generator = V2TensorGenerator()

channels = [
    ("H", processed["h_pc3"]),
    ("D", processed["d_pc3"]),
    ("Z", processed["z_pc3"])
]

for name, signal in channels:

    print()
    print("="*70)
    print(name)
    print("="*70)

    pooled = generator.pool_signal(signal)

    cwt = generator.extract_cwt_tensor(pooled)

    print("PC3 Energy     :", energy(signal))
    print("Pool Energy    :", energy(pooled))
    print("CWT Energy     :", energy(cwt))

    print()

    print("PC3 std        :", np.std(signal))
    print("Pool std       :", np.std(pooled))
    print("CWT mean       :", np.mean(cwt))
    print("CWT std        :", np.std(cwt))
