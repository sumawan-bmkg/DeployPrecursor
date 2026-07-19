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

for key in ["H", "D", "Z"]:

    arr = raw[key]

    clean, mask = processor.handle_gaps(arr)

    print()
    print("="*70)
    print(key)
    print("="*70)

    print("NaN raw   :", np.isnan(arr).sum())
    print("NaN clean :", np.isnan(clean).sum())

    idx = np.where(np.isnan(arr))[0]

    print("Gap count :", len(idx))

    if len(idx):

        print()

        print("First 20 gap indices")

        print(idx[:20])

        print()

        for i in idx[:20]:

            print(
                i,
                arr[i],
                clean[i],
                mask[i]
            )

    print()

    print("Largest value raw  :", np.nanmax(np.abs(arr)))
    print("Largest value clean:", np.max(np.abs(clean)))
