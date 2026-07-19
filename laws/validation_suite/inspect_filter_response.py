import numpy as np

from common import *

from read_mdata import read_604rcsv_new_python
from signal_processing import GeomagneticSignalProcessor

processor = GeomagneticSignalProcessor()

raw = read_604rcsv_new_python(
    YEAR,
    MONTH,
    DAY,
    STATION,
    RAW_ROOT
)

print("=" * 70)
print("RAW DATA LOADED")
print("=" * 70)
print(raw.keys())
print(raw["H"].shape)
print(raw["D"].shape)
print(raw["Z"].shape)

def analyze(name, raw, filt):
    raw = np.asarray(raw)
    filt = np.asarray(filt)

    raw_rms = np.sqrt(np.nanmean(raw**2))
    filt_rms = np.sqrt(np.nanmean(filt**2))

    raw_energy = np.nansum(raw**2)
    filt_energy = np.nansum(filt**2)

    print()
    print("=" * 70)
    print(name)
    print("=" * 70)

    print("RAW")
    print(" mean      :", np.nanmean(raw))
    print(" std       :", np.nanstd(raw))
    print(" rms       :", raw_rms)
    print(" energy    :", raw_energy)
    print(" max(abs)  :", np.nanmax(np.abs(raw)))

    print()

    print("PC3")
    print(" mean      :", np.nanmean(filt))
    print(" std       :", np.nanstd(filt))
    print(" rms       :", filt_rms)
    print(" energy    :", filt_energy)
    print(" max(abs)  :", np.nanmax(np.abs(filt)))

    print()

    print("GAIN")
    print(" std ratio    :", np.nanstd(filt) / np.nanstd(raw))
    print(" rms ratio    :", filt_rms / raw_rms)
    print(" energy ratio :", filt_energy / raw_energy)

processed = processor.process_components(
    raw["H"],
    raw["D"],
    raw["Z"],
    apply_pc3=True
)

print()
print("=" * 70)
print("PROCESSED KEYS")
print("=" * 70)

print(processed.keys())

print(processed["h_pc3"].shape)
print(processed["d_pc3"].shape)
print(processed["z_pc3"].shape)

analyze(
    "H",
    raw["H"],
    processed["h_pc3"]
)

analyze(
    "D",
    raw["D"],
    processed["d_pc3"]
)

analyze(
    "Z",
    raw["Z"],
    processed["z_pc3"]
)
