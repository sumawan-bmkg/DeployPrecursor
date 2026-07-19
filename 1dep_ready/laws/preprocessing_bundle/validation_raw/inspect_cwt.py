#!/usr/bin/env python3

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "preprocessing_bundle"))
sys.path.insert(0, str(ROOT / "preprocessing_bundle" / "core"))

from tensor_generator import V2TensorGenerator

g = V2TensorGenerator()

print("Wavelet :", g.wavelet)
print("fs      :", g.fs)
print("pool    :", g.pool_size)

print()

print("Scale count :", len(g.scales))

print("First scale :", g.scales[0])
print("Last scale  :", g.scales[-1])

print()

print("Min scale :", g.scales.min())
print("Max scale :", g.scales.max())
