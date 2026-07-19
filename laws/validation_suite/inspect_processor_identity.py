#!/usr/bin/env python3

from common import *

import signal_processing
from signal_processing import GeomagneticSignalProcessor

print("=" * 70)
print("MODULE")
print("=" * 70)

print(signal_processing.__file__)

print()

print("=" * 70)
print("CLASS")
print("=" * 70)

print(GeomagneticSignalProcessor)

print()

processor = GeomagneticSignalProcessor()

print("=" * 70)
print("INSTANCE")
print("=" * 70)

print(processor)

print()

print("=" * 70)
print("PARAMETERS")
print("=" * 70)

print("fs       :", processor.fs)
print("pc3_low  :", processor.pc3_low)
print("pc3_high :", processor.pc3_high)

print()

print("=" * 70)
print("METHOD")
print("=" * 70)

print(processor.bandpass_filter)
