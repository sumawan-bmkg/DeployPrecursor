#!/usr/bin/env python3

from common import *

from read_mdata import read_604rcsv_new_python
from signal_processing import GeomagneticSignalProcessor
from tensor_generator import V2TensorGenerator

header("CWT FORENSICS")

processor = GeomagneticSignalProcessor()
generator = V2TensorGenerator()

raw = read_604rcsv_new_python(
    YEAR,
    MONTH,
    DAY,
    STATION,
    str(RAW_DATA)
)

processed = processor.process_components(
    raw["H"],
    raw["D"],
    raw["Z"],
    apply_pc3=True
)

h_pool = generator.pool_signal(processed["h_pc3"])
d_pool = generator.pool_signal(processed["d_pc3"])
z_pool = generator.pool_signal(processed["z_pc3"])

print("Pool OK")
print(h_pool.shape)
print(d_pool.shape)
print(z_pool.shape)

h_cwt = generator.extract_cwt_tensor(h_pool)
d_cwt = generator.extract_cwt_tensor(d_pool)
z_cwt = generator.extract_cwt_tensor(z_pool)

print()
print("CWT Shapes")

print(h_cwt.shape)
print(d_cwt.shape)
print(z_cwt.shape)

np.save("H_CWT.npy", h_cwt)
np.save("D_CWT.npy", d_cwt)
np.save("Z_CWT.npy", z_cwt)

print()
print("Saved CWT matrices.")
