#!/usr/bin/env python3

import numpy as np

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "preprocessing_bundle"))
sys.path.insert(0, str(ROOT / "preprocessing_bundle" / "core"))
sys.path.insert(0, str(ROOT / "preprocessing_bundle" / "data_fetching"))
#sys.path.insert(0, str(ROOT / "preprocessing_bundle" / "tensor_generation"))

from signal_processing import GeomagneticSignalProcessor
from tensor_generator import V2TensorGenerator
from read_mdata import read_604rcsv_new_python

processor = GeomagneticSignalProcessor()
generator = V2TensorGenerator()

raw = read_604rcsv_new_python(
    2025,
    1,
    1,
    "ALR",
    "/tmp/alr_check"
)

processed = processor.process_components(
    raw["H"],
    raw["D"],
    raw["Z"],
    apply_pc3=True
)

tensor, _ = generator.generate_tensor(
    processed["h_pc3"],
    processed["d_pc3"],
    processed["z_pc3"]
)

print("Generated tensor")
print("----------------")
print("shape :", tensor.shape)
print("dtype :", tensor.dtype)
print("mean  :", tensor.mean())
print("std   :", tensor.std())
print("min   :", tensor.min())
print("max   :", tensor.max())

np.save(
    "/opt/pimes/laws/preprocessing_bundle/validation_raw/generated_tensor.npy",
    tensor.astype(np.float32)
)

print("Tensor saved.")
