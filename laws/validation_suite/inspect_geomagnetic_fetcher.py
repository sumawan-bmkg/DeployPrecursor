import inspect
import sys

sys.path.insert(0, "/opt/pimes/laws/preprocessing_bundle")
sys.path.insert(0, "/opt/pimes/laws/preprocessing_bundle/intial")

from geomagnetic_fetcher import GeomagneticDataFetcher

print("=" * 70)
print("GeomagneticDataFetcher")
print("=" * 70)

print(inspect.getsource(GeomagneticDataFetcher))
