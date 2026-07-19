from pathlib import Path
import hashlib

reader = Path("/opt/pimes/intial/read_mdata.py")
fetcher = Path("/opt/pimes/intial/geomagnetic_fetcher.py")

print("="*60)
print("READ_MDATA")
print("="*60)

print(hashlib.sha256(reader.read_bytes()).hexdigest())

print()

print("="*60)
print("GEOMAGNETIC_FETCHER")
print("="*60)

print(hashlib.sha256(fetcher.read_bytes()).hexdigest())
