#!/usr/bin/env python3

import inspect

from common import *

from signal_processing import GeomagneticSignalProcessor

processor = GeomagneticSignalProcessor()

print("=" * 70)
print("bandpass_filter SOURCE")
print("=" * 70)

print(inspect.getsource(processor.bandpass_filter))

print()

print("=" * 70)
print("process_components SOURCE")
print("=" * 70)

print(inspect.getsource(processor.process_components))
