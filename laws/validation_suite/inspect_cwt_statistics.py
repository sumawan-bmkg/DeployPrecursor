import numpy as np

for name in ["H", "D", "Z"]:

    x = np.load(f"{name}_CWT.npy")

    print("="*60)
    print(name)
    print("="*60)

    print("shape :", x.shape)
    print("mean  :", x.mean())
    print("std   :", x.std())
    print("min   :", x.min())
    print("max   :", x.max())

    print()

    for p in [1,5,25,50,75,95,99]:
        print(f"P{p:02d} :", np.percentile(x,p))

    print()
