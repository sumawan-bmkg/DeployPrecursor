import numpy as np

A = np.load("generated_tensor.npy")

B = np.load(
    "/opt/pimes/laws/reference_npy/raw_tensor_ALR_1735660800.npy"
)

print(A.shape)
print(B.shape)

mae = np.mean(np.abs(A-B))

rmse = np.sqrt(np.mean((A-B)**2))

corr = np.corrcoef(
    A.flatten(),
    B.flatten()
)[0,1]

cos = np.dot(
    A.flatten(),
    B.flatten()
)

cos /= np.linalg.norm(A.flatten())

cos /= np.linalg.norm(B.flatten())

print()

print("MAE :",mae)

print("RMSE:",rmse)

print("CORR:",corr)

print("COS :",cos)
