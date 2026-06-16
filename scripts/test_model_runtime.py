import sys
import yaml
import psycopg2
import torch
import numpy as np
from pathlib import Path

print("=" * 60)
print("PIMES MODEL RUNTIME TEST")
print("=" * 60)

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

DEPLOY_ROOT = Path("/opt/pimes/repository/staging/deploy")

MODEL_DIR = DEPLOY_ROOT / "models"
CKPT_PATH = DEPLOY_ROOT / "checkpoints" / "v3_v8_conv_fpr_best_weights.pth"

sys.path.insert(0, str(MODEL_DIR))

# --------------------------------------------------
# LOAD MODEL
# --------------------------------------------------

print("\n[1] Loading model...")

from V3_Model_v8 import (
    MultiTaskScalogramV3_v8,
    azimuth_from_sincos
)

model = MultiTaskScalogramV3_v8(pretrained=False)

state = torch.load(
    CKPT_PATH,
    map_location="cpu"
)

model.load_state_dict(state, strict=False)
model.eval()

print("OK - model loaded")

# --------------------------------------------------
# DUMMY INPUT
# --------------------------------------------------

print("\n[2] Generating dummy tensor...")

tensor = torch.randn(
    1,
    3,
    128,
    1440
)

cosmic = torch.tensor(
    [[2.0, -10.0]],
    dtype=torch.float32
)

print("OK - dummy tensor created")

# --------------------------------------------------
# INFERENCE
# --------------------------------------------------

print("\n[3] Running inference...")

with torch.no_grad():
    det, mag, azm, *_ = model(tensor, cosmic)

prob = torch.softmax(det, dim=1)[0,1].item()

azimuth = azimuth_from_sincos(azm)[0].item()

mag_bins = np.array([3.5,4.5,5.5,6.5,7.5])

mag_class = torch.argmax(mag, dim=1).item()

magnitude = float(mag_bins[mag_class])

print(f"Probability : {prob:.4f}")
print(f"Azimuth     : {azimuth:.2f}")
print(f"Magnitude   : {magnitude:.1f}")

# --------------------------------------------------
# DATABASE
# --------------------------------------------------

print("\n[4] Connecting database...")

with open("/opt/pimes/config/db.yaml") as f:
    db = yaml.safe_load(f)

conn = psycopg2.connect(
    host=db["host"],
    database=db["database"],
    user=db["user"],
    password=db["password"]
)

cur = conn.cursor()

print("OK - database connected")

# --------------------------------------------------
# INSERT TEST RECORD
# --------------------------------------------------

print("\n[5] Writing test prediction...")

cur.execute(
    """
    INSERT INTO predictions
    (
        station_code,
        prediction_time,
        detection_probability,
        magnitude_class,
        azimuth_class,
        kp,
        dst,
        model_version
    )
    VALUES
    (
        %s,
        NOW(),
        %s,
        %s,
        %s,
        %s,
        %s,
        %s
    )
    """,
    (
        "TEST",
        float(prob),
        int(mag_class),
        int(round(azimuth)),
        2.0,
        -10.0,
        "V8_SMOKE_TEST"
    )
)

conn.commit()

print("OK - prediction inserted")

cur.close()
conn.close()

print("\nSUCCESS")
print("MODEL -> DATABASE pipeline validated")
print("=" * 60)
