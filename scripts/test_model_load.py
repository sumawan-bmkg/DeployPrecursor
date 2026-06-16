import sys

sys.path.insert(
    0,
    "/opt/pimes/repository/staging/deploy/scripts/inference"
)

from inference_service import load_model

model = load_model()

print(type(model))
print("MODEL LOAD SUCCESS")
