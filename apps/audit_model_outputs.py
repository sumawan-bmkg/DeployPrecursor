#!/usr/bin/env python3

import sys
import torch

sys.path.insert(0, "/opt/pimes/apps")

from run_station import (
    load_model,
    build_tensor_from_scn
)

FILES = [
    ("/opt/pimes/data/raw/ALR/S260611.ALR", "ALR"),
    ("/opt/pimes/data/raw/YOG/S260611.YOG", "YOG"),
    ("/opt/pimes/data/raw/TRT/S260611.TRT", "TRT"),
]

model = load_model()

for filepath, station in FILES:

    print("\n" + "="*60)
    print(station)
    print("="*60)

    tensor = build_tensor_from_scn(
        filepath,
        station
    )

    x_img = torch.tensor(
        tensor,
        dtype=torch.float32
    ).unsqueeze(0)

    x_cos = torch.tensor(
        [[2.0, 4.0]],
        dtype=torch.float32
    )

    with torch.no_grad():

        det, mag, azm, *_ = model(
            x_img,
            x_cos
        )

    print("DET:")
    print(det)

    print("\nMAG:")
    print(mag)

    print("\nAZM:")
    print(azm)
