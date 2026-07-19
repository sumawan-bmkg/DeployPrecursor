import numpy as np
from pathlib import Path

REF = Path("/opt/pimes/laws/reference_npy/raw_tensor_ALR_1735660800.npy")

ref = np.load(REF)

print("="*70)
print("REFERENCE TENSOR")
print("="*70)

print("Shape :", ref.shape)
print("Dtype :", ref.dtype)
print()

for i, name in enumerate(["H","D","Z"]):

    x = ref[i]

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
