import numpy as np
from pathlib import Path

GEN = Path("/opt/pimes/laws/preprocessing_bundle/validation_raw/generated_tensor.npy")

gen = np.load(GEN)

print("="*70)
print("GENERATED TENSOR")
print("="*70)

print("Shape :", gen.shape)
print("Dtype :", gen.dtype)
print()

for i, name in enumerate(["H","D","Z"]):

    x = gen[i]

    print("="*70)
    print(name)
    print("="*70)

    print("mean :", np.mean(x))
    print("std  :", np.std(x))
    print("min  :", np.min(x))
    print("max  :", np.max(x))

    print()

    for p in [1,5,25,50,75,95,99]:
        print(f"P{p:02d} :", np.percentile(x,p))

    print()

    print("zeros :", np.sum(x==0))
    print("<1    :", np.sum(x<1))
    print(">50   :", np.sum(x>50))

    print()

    energy = np.sum(x*x)

    print("sum      :", np.sum(x))
    print("energy   :", energy)
    print("mean(E)  :", np.mean(x*x))
    print()
