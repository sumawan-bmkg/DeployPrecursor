import numpy as np

ref = np.load("/opt/pimes/laws/reference_npy/raw_tensor_ALR_1735660800.npy")
gen = np.load(
    "/opt/pimes/laws/preprocessing_bundle/validation_raw/generated_tensor.npy"
)

names = ["H", "D", "Z"]

for i, name in enumerate(names):

    r = ref[i].astype(np.float64).ravel()
    g = gen[i].astype(np.float64).ravel()

    mae = np.mean(np.abs(r - g))
    rmse = np.sqrt(np.mean((r - g) ** 2))

    corr = np.corrcoef(r, g)[0, 1]

    cos = np.dot(r, g) / (
        np.linalg.norm(r) * np.linalg.norm(g)
    )

    print("=" * 60)
    print(name)
    print("=" * 60)

    print("Reference")
    print(" mean :", r.mean())
    print(" std  :", r.std())

    print()

    print("Generated")
    print(" mean :", g.mean())
    print(" std  :", g.std())

    print()

    print("MAE  :", mae)
    print("RMSE :", rmse)
    print("CORR :", corr)
    print("COS  :", cos)
    print()
