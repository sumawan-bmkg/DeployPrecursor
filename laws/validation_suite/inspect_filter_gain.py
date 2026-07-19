from common import *
import numpy as np
from signal_processing import GeomagneticSignalProcessor
from read_mdata import read_604rcsv_new_python

raw = read_604rcsv_new_python(
    2026,
    6,
    11,
    "ALR",
    "/opt/pimes/data/raw"
)

proc = GeomagneticSignalProcessor()

out = proc.process_components(
    raw["H"],
    raw["D"],
    raw["Z"],
    apply_pc3=True
)

for name in ["H", "D", "Z"]:

    raw_std = np.nanstd(raw[name])

    pc3_std = np.std(out[f"{name.lower()}_pc3"])

    print(name)
    print("Raw std :", raw_std)
    print("PC3 std :", pc3_std)
    print("Gain    :", pc3_std / raw_std)
    print()
