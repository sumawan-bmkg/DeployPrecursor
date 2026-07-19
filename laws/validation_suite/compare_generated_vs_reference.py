#!/usr/bin/env python3

import numpy as np

REF = "/opt/pimes/laws/reference_npy/raw_tensor_ALR_1735660800.npy"
GEN = "/opt/pimes/laws/preprocessing_bundle/validation_raw/generated_tensor.npy"

ref = np.load(REF)
gen = np.load(GEN)

print("=" * 70)
print("REFERENCE")
print("=" * 70)
print(ref.shape)
print(ref.dtype)

print()

print("=" * 70)
print("GENERATED")
print("=" * 70)
print(gen.shape)
print(gen.dtype)

channel_names = ["H", "D", "Z"]

for i, name in enumerate(channel_names):

    print()
    print("=" * 70)
    print(name)
    print("=" * 70)

    r = ref[i]
    g = gen[i]

    diff = r - g

    mae = np.mean(np.abs(diff))
    rmse = np.sqrt(np.mean(diff ** 2))

    corr = np.corrcoef(
        r.ravel(),
        g.ravel()
    )[0, 1]

    print("MAE :", mae)
    print("RMSE:", rmse)
    print("CORR:", corr)

    print()

    print("Reference mean :", np.mean(r))
    print("Generated mean :", np.mean(g))

    print("Reference std  :", np.std(r))
    print("Generated std  :", np.std(g))

    print()

    print("Mean diff :", np.mean(diff))
    print("Std diff  :", np.std(diff))

    print()

    print("Max abs diff :", np.max(np.abs(diff)))

    print()

    print("Exact equal :", np.array_equal(r, g))
    print("All close   :", np.allclose(r, g, rtol=1e-6, atol=1e-6))

print()
print("=" * 70)
print("WHOLE TENSOR")
print("=" * 70)

whole = ref - gen

print("L2 norm :", np.linalg.norm(whole))
print("Max abs :", np.max(np.abs(whole)))
print("Mean abs:", np.mean(np.abs(whole)))
