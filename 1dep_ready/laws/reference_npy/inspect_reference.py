import numpy as np

ref = np.load("raw_tensor_ALR_1735660800.npy")

print("=" * 60)
print("REFERENCE TENSOR")
print("=" * 60)

print("Shape :", ref.shape)
print("Dtype :", ref.dtype)
print("Mean  :", ref.mean())
print("Std   :", ref.std())
print("Min   :", ref.min())
print("Max   :", ref.max())

for i, name in enumerate(["H", "D", "Z"]):

    x = ref[i]

    print()
    print("=" * 60)
    print(name)
    print("=" * 60)

    print("Mean :", x.mean())
    print("Std  :", x.std())
    print("Min  :", x.min())
    print("Max  :", x.max())

    print()

    for p in [1, 5, 25, 50, 75, 95, 99]:
        print(f"P{p:02d} :", np.percentile(x, p))
