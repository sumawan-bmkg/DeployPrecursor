import struct
import numpy as np
import os

FILE_PATH = "/opt/pimes/data/raw/SCN/S260611.SCN"

HEADER_SIZE = 32
RECORD_SIZE = 17
EXPECTED_RECORDS = 86400

with open(FILE_PATH, "rb") as f:
    data = f.read()

file_size = len(data)
expected_size = HEADER_SIZE + EXPECTED_RECORDS * RECORD_SIZE

print("FILE SIZE     :", file_size)
print("EXPECTED SIZE :", expected_size)
print("DIFF          :", file_size - expected_size)

payload = data[HEADER_SIZE:]

n_records = len(payload) // RECORD_SIZE
remainder = len(payload) % RECORD_SIZE

print("PARSED RECORDS:", n_records)
print("REMAINDER     :", remainder)

H = np.empty(n_records, dtype=np.float32)
D = np.empty(n_records, dtype=np.float32)
Z = np.empty(n_records, dtype=np.float32)

for i in range(n_records):
    off = i * RECORD_SIZE
    rec = payload[off:off+RECORD_SIZE]

    H[i] = struct.unpack("<h", rec[0:2])[0] * 0.1
    D[i] = struct.unpack("<h", rec[2:4])[0] * 0.1
    Z[i] = struct.unpack("<h", rec[4:6])[0] * 0.1

for name, arr in [("H", H), ("D", D), ("Z", Z)]:
    print()
    print(name)
    print("MIN :", arr.min())
    print("MAX :", arr.max())
    print("MEAN:", arr.mean())
    print("STD :", arr.std())

print("\nFIRST 10 SAMPLES")

for i in range(min(10, n_records)):
    print(
        i,
        H[i],
        D[i],
        Z[i]
    )
