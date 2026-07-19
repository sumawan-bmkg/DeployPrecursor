#!/usr/bin/env python3

import numpy as np

for name in ["h_pc3", "d_pc3", "z_pc3"]:

    x = np.load(name + ".npy")

    print("=" * 60)
    print(name)

    print("shape :", x.shape)
    print("dtype :", x.dtype)

    print("mean  :", np.mean(x))
    print("std   :", np.std(x))

    print("min   :", np.min(x))
    print("max   :", np.max(x))

    print("nan   :", np.isnan(x).sum())

    print("finite:", np.isfinite(x).sum())
