#!/usr/bin/env python3

import sys
import numpy as np

sys.path.insert(
    0,
    "/opt/pimes/repository/staging/deploy/scripts/preprocessing"
)

from signal_processing import GeomagneticSignalProcessor
from tensor_generator import V2TensorGenerator

# import parser Anda
from parse_mdata_audit import read_mdata_file

FILE_PATH = "/opt/pimes/data/raw/SCN/S260611.SCN"


def main():

    print("=" * 60)
    print("STEP 1 : PARSE RAW FILE")
    print("=" * 60)

    result = read_mdata_file(FILE_PATH)

    h = result["H"]
    d = result["D"]
    z = result["Z"]

    print("H shape:", h.shape)
    print("D shape:", d.shape)
    print("Z shape:", z.shape)

    print()
    print("=" * 60)
    print("STEP 2 : PC3 FILTER")
    print("=" * 60)

    processor = GeomagneticSignalProcessor()

    processed = processor.process_components(
        h,
        d,
        z,
        apply_pc3=True
    )

    h_pc3 = processed["h_pc3"]
    d_pc3 = processed["d_pc3"]
    z_pc3 = processed["z_pc3"]

    print("PC3 shape:", h_pc3.shape)

    print()
    print("=" * 60)
    print("STEP 3 : TENSOR")
    print("=" * 60)

    generator = V2TensorGenerator()

    tensor, _ = generator.generate_tensor(
        h_pc3,
        d_pc3,
        z_pc3,
        apply_pooling=True
    )

    tensor = generator.zscore_normalize(
        tensor,
        per_channel=True
    )

    tensor = tensor.astype(np.float32)

    print("Tensor shape:", tensor.shape)
    print("Tensor dtype:", tensor.dtype)

    print("Min :", tensor.min())
    print("Max :", tensor.max())
    print("Mean:", tensor.mean())
    print("Std :", tensor.std())

    out_file = "/tmp/test_tensor.npy"

    np.save(out_file, tensor)

    print()
    print("Saved:", out_file)


if __name__ == "__main__":
    main()
