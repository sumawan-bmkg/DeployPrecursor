import sys
import numpy as np

sys.path.insert(
    0,
    "/opt/pimes/scripts"
)

sys.path.insert(
    0,
    "/opt/pimes/repository/staging/deploy/scripts/preprocessing"
)

from parse_mdata_audit import read_mdata_file
from signal_processing import GeomagneticSignalProcessor
from tensor_generator import V2TensorGenerator

FILE_PATH = "/opt/pimes/data/raw/SCN/S260611.SCN"

print("=" * 60)
print("STEP 1 PARSER")
print("=" * 60)

d = read_mdata_file(FILE_PATH)

H = d["H"]
D = d["D"]
Z = d["Z"]

print("H", H.shape)
print("D", D.shape)
print("Z", Z.shape)

print()
print("=" * 60)
print("STEP 2 SIGNAL PROCESSING")
print("=" * 60)

proc = GeomagneticSignalProcessor()

result = proc.process_components(
    H,
    D,
    Z,
    apply_pc3=True
)

print("h_pc3", result["h_pc3"].shape)
print("d_pc3", result["d_pc3"].shape)
print("z_pc3", result["z_pc3"].shape)

print()
print("=" * 60)
print("STEP 3 TENSOR")
print("=" * 60)

gen = V2TensorGenerator()

tensor, _ = gen.generate_tensor(
    result["h_pc3"],
    result["d_pc3"],
    result["z_pc3"]
)

print("tensor shape =", tensor.shape)
print("tensor dtype =", tensor.dtype)

print("min =", tensor.min())
print("max =", tensor.max())
print("mean =", tensor.mean())
print("std =", tensor.std())
