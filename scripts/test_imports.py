import sys

sys.path.insert(
    0,
    "/opt/pimes/repository/staging/deploy/models"
)

sys.path.insert(
    0,
    "/opt/pimes/repository/staging/deploy/scripts/preprocessing"
)

sys.path.insert(
    0,
    "/opt/pimes/repository/staging/deploy/scripts/inference"
)

from signal_processing import GeomagneticSignalProcessor
from tensor_generator import V2TensorGenerator
from inference_service import load_model

print("OK signal_processing")
print("OK tensor_generator")
print("OK inference_service")
