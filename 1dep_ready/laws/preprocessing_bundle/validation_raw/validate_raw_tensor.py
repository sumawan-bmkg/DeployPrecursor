#!/usr/bin/env python3

import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "preprocessing_bundle"))
sys.path.insert(0, str(ROOT / "preprocessing_bundle" / "core"))
sys.path.insert(0, str(ROOT / "preprocessing_bundle" / "data_fetching"))
sys.path.insert(0, str(ROOT / "preprocessing_bundle" / "tensor_generation"))

print("ROOT =", ROOT)

from core.signal_processing import GeomagneticSignalProcessor
from core.tensor_generator import V2TensorGenerator
from data_fetching.read_mdata import read_604rcsv_new_python

print("IMPORT OK")

processor = GeomagneticSignalProcessor()
generator = V2TensorGenerator()

print("Processor OK")
print("Generator OK")

print()
print("=" * 60)
print("STEP 1 : READ BMKG BINARY")
print("=" * 60)

raw = read_604rcsv_new_python(
    year=2026,
    month=6,
    day=11,
    stn="ALR",
    path="/opt/pimes/data/raw"
)

print("Keys :", raw.keys())

print("H :", raw["H"].shape, raw["H"].dtype)
print("D :", raw["D"].shape, raw["D"].dtype)
print("Z :", raw["Z"].shape, raw["Z"].dtype)

print()

print("H mean =", np.nanmean(raw["H"]))
print("D mean =", np.nanmean(raw["D"]))
print("Z mean =", np.nanmean(raw["Z"]))

print()

print("H std =", np.nanstd(raw["H"]))
print()
print("=" * 60)
print("STEP 2 : PC3 PROCESSING")
print()
print("=" * 60)
print("STEP 3 : GENERATE RAW TENSOR")
print("=" * 60)

tensor, pooled_mask = generator.generate_tensor(
    processed["h_pc3"],
    processed["d_pc3"],
    processed["z_pc3"]
)

print("Tensor shape :", tensor.shape)
print("Tensor dtype :", tensor.dtype)

print("Tensor mean :", tensor.mean())
print("Tensor std  :", tensor.std())
print("Tensor min  :", tensor.min())
print("Tensor max  :", tensor.max())

print("=" * 60)

processed = processor.process_components(
    raw["H"],
    raw["D"],
    raw["Z"],
    apply_pc3=True
)

print("Returned keys:")
print(processed.keys())

print()

print("h_pc3 :", processed["h_pc3"].shape)
print("d_pc3 :", processed["d_pc3"].shape)
print("z_pc3 :", processed["z_pc3"].shape)

print()

print("mask shape :", processed["mask"].shape)
print("valid ratio :", processed["mask"].mean())

print()

print("H PC3 mean :", np.mean(processed["h_pc3"]))
print("H PC3 std  :", np.std(processed["h_pc3"]))

print("D PC3 mean :", np.mean(processed["d_pc3"]))
print("D PC3 std  :", np.std(processed["d_pc3"]))

print("Z PC3 mean :", np.mean(processed["z_pc3"]))
print("Z PC3 std  :", np.std(processed["z_pc3"]))


print("D std =", np.nanstd(raw["D"]))
print("Z std =", np.nanstd(raw["Z"]))


