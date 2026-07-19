#!/usr/bin/env python3

import os

ROOT = "/opt/pimes"

keywords = [
    "raw_tensor_ALR_1735660800",
    "reference_npy",
    "1735660800",
    "raw_tensor_",
    "generate_tensor",
]

print("=" * 70)
print("SEARCHING REFERENCE ORIGIN")
print("=" * 70)

for root, dirs, files in os.walk(ROOT):
    for f in files:
        if not (f.endswith(".py") or f.endswith(".sh") or f.endswith(".md") or f.endswith(".ipynb")):
            continue

        path = os.path.join(root, f)

        try:
            with open(path, "r", errors="ignore") as fp:
                text = fp.read()

            for key in keywords:
                if key in text:
                    print()
                    print(path)
                    print("contains:", key)
                    break

        except Exception:
            pass
