#!/usr/bin/env python3

from common import *

from read_mdata import read_604rcsv_new_python

header("STEP 1 : BMKG READER")

raw = read_604rcsv_new_python(
    YEAR,
    MONTH,
    DAY,
    STATION,
    str(RAW_DATA)
)

print("Available keys:")
print(raw.keys())

print()

stats("H", raw["H"])
stats("D", raw["D"])
stats("Z", raw["Z"])

assert raw["H"].shape == (86400,)
assert raw["D"].shape == (86400,)
assert raw["Z"].shape == (86400,)

print("✓ Reader validation PASSED")
