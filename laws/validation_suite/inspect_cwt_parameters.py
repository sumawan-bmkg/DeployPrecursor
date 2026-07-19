from common import *

from tensor_generator import V2TensorGenerator

g = V2TensorGenerator()

print("=" * 60)
print("CWT PARAMETERS")
print("=" * 60)

print("Wavelet :", g.wavelet)
print("Sampling frequency :", g.fs)
print("Pool size :", g.pool_size)

print()
print("Scale count :", len(g.scales))
print("First scale :", g.scales[0])
print("Last scale  :", g.scales[-1])

print()
print("First 10 scales:")
print(g.scales[:10])

print()
print("Last 10 scales:")
print(g.scales[-10:])
