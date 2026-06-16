import sys
import numpy as np

sys.path.insert(
    0,
    "/opt/pimes/repository/staging/deploy/scripts/inference"
)

from inference_service import predict_single

tensor = np.random.randn(
    3,
    128,
    1440
).astype(np.float32)

predict_single(
    tensor,
    kp=2.0,
    dst=-10.0
)
