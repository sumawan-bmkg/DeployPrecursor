#!/usr/bin/env python3

from common import *
import numpy as np

from read_mdata import read_604rcsv_new_python

header("READ RAW FILE")

raw = read_604rcsv_new_python(
    YEAR,
    MONTH,
    DAY,
    STATION,
    RAW_ROOT
)

print("Available keys")
print(raw.keys())

for key in raw.keys():

    value = raw[key]

    if isinstance(value, np.ndarray):

        print()
        print("=" * 60)
        print(key)
        print("=" * 60)

        print("shape :", value.shape)
        print("dtype :", value.dtype)

        print("mean :", np.nanmean(value))
        print("std  :", np.nanstd(value))
        print("min  :", np.nanmin(value))
        print("max  :", np.nanmax(value))

        print()

        print("First 10 values")

        print(value[:10])

        print()

        print("NaN :", np.isnan(value).sum())
