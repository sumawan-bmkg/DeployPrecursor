import numpy as np

ref = np.load("/opt/pimes/laws/reference_npy/raw_tensor_ALR_1735660800.npy")
gen = np.load("/opt/pimes/laws/preprocessing_bundle/validation_raw/generated_tensor.npy")

print("Reference :", ref.shape)
print("Generated :", gen.shape)

for i, ch in enumerate(["H","D","Z"]):
    a = ref[i].ravel()
    b = gen[i].ravel()

    print("\n", ch)
    print("MAE :", np.mean(np.abs(a-b)))
    print("RMSE:", np.sqrt(np.mean((a-b)**2)))
    print("CORR:", np.corrcoef(a,b)[0,1])
