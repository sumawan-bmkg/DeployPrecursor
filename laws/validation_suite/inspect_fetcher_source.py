import inspect
import sys

sys.path.insert(0, "/opt/pimes/laws/preprocessing_bundle")
sys.path.insert(0, "/opt/pimes/laws/preprocessing_bundle/data_fetching")

from read_mdata import read_604rcsv_new_python

print("="*70)
print("read_604rcsv_new_python")
print("="*70)

print(inspect.getsource(read_604rcsv_new_python))
