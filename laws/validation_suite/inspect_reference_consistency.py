#!/usr/bin/env python3

import numpy as np
from pathlib import Path

REF = Path("/opt/pimes/laws/reference_npy/raw_tensor_ALR_1735660800.npy")
GEN = Path("/opt/pimes/laws/preprocessing_bundle/validation_raw/generated_tensor.npy")

ref = np.load(REF)
gen = np.load(GEN)

channels = ["H", "D", "Z"]

print("="*70)
print("REFERENCE vs GENERATED")
print("="*70)

for i, name in enumerate(channels):

    print()
    print("="*70)
    print(name)
    print("="*70)

    r = ref[i]
    g = gen[i]

    print("Reference")
    print("shape :", r.shape)
    print("dtype :", r.dtype)

    print()

    print("Generated")
    print("shape :", g.shape)
    print("dtype :", g.dtype)

    print()

    print("Reference Energy :", np.sum(r**2))
    print("Generated Energy :", np.sum(g**2))

    print()

    print("Reference Sum :", np.sum(r))
    print("Generated Sum :", np.sum(g))
