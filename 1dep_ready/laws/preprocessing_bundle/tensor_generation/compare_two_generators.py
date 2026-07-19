import inspect
from pathlib import Path
import sys

ROOT = Path("/opt/pimes")

sys.path.insert(0, str(ROOT / "laws/preprocessing_bundle/core"))
sys.path.insert(0, str(ROOT / "laws/preprocessing_bundle"))

from tensor_generator import V2TensorGenerator as NewGenerator

print("="*60)
print("NEW GENERATOR")
print("="*60)

print(inspect.getsource(NewGenerator.generate_tensor))
