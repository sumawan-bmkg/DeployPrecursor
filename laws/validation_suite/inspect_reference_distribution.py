#!/usr/bin/env python3

import numpy as np
from pathlib import Path

REF = Path("/opt/pimes/laws/reference_npy/raw_tensor_ALR_1735660800.npy")

ref = np.load(REF)

channels = ["H", "D", "Z"]

for i, ch in enumerate(channels):

    x = ref[i]

    print()
    print("=" * 70)
    print(ch)
    print("=" * 70)

    print("Negative :", np.sum(x < 0))
    print("Positive :", np.sum(x > 0))
    print("Zero     :", np.sum(x == 0))

    print()

    print("Median :", np.median(x))
    print("Mean   :", x.mean())
    print("Std    :", x.std())

    print()

    print("Top 20 largest values")

    flat = np.sort(x.ravel())

    print(flat[-20:])

    print()

    print("Top 20 smallest values")

    print(flat[:20])
