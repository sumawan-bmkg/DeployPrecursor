#!/usr/bin/env python3

import inspect
import sys
from pathlib import Path

ROOT = Path("/opt/pimes/laws")

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "preprocessing_bundle"))
sys.path.insert(0, str(ROOT / "preprocessing_bundle" / "tensor_generation"))

import V2_Generate_Raw_Tensors as gen

print("=" * 70)
print("MODULE")
print("=" * 70)
print(gen.__file__)

print()

print("=" * 70)
print("AVAILABLE FUNCTIONS")
print("=" * 70)

for name in dir(gen):
    if not name.startswith("_"):
        obj = getattr(gen, name)
        if callable(obj):
            print(name)

print()

print("=" * 70)
print("generate_daily_tensor SOURCE")
print("=" * 70)

for name in dir(gen):
    if "generate" in name.lower():
        obj = getattr(gen, name)
        if callable(obj):
            print()
            print("FUNCTION :", name)
            print("-" * 50)
            print(inspect.getsource(obj))
