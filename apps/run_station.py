#!/usr/bin/env python3

import sys
import yaml
import torch
import psycopg2
import numpy as np

from pathlib import Path

# ============================================================
# PATHS
# ============================================================

ROOT = Path("/opt/pimes")

sys.path.append("/opt/pimes/scripts")

sys.path.append(
    "/opt/pimes/repository/staging/deploy/scripts/preprocessing"
)

sys.path.append(
    "/opt/pimes/repository/staging/deploy/models"
)

# ============================================================
# IMPORTS
# ============================================================

from scn_parser import SCNParser

from signal_processing import (
    GeomagneticSignalProcessor
)

from tensor_generator import (
    V2TensorGenerator
)

from V3_Model_v8 import (
    MultiTaskScalogramV3_v8,
    azimuth_from_sincos
)

# ============================================================
# CONFIG
# ============================================================

CKPT = (
    "/opt/pimes/repository/staging/deploy/checkpoints/"
    "v3_v8_conv_fpr_best_weights.pth"
)

DBCFG = "/opt/pimes/config/db.yaml"

# ============================================================
# MODEL LOADER
# ============================================================

def load_model():

    print("[MODEL] Loading checkpoint...")

    state = torch.load(
        CKPT,
        map_location="cpu"
    )

    remapped = {}

    for k, v in state.items():

        nk = k

        nk = nk.replace(
            "gnn.gat1.a",
            "gnn.gat1_a"
        )

        nk = nk.replace(
            "gnn.gat2.a",
            "gnn.gat2_a"
        )

        nk = nk.replace(
            "gnn.gat1.W",
            "gnn.gat1_W"
        )

        nk = nk.replace(
            "gnn.gat2.W",
            "gnn.gat2_W"
        )

        nk = nk.replace(
            "gnn.gat1.norm",
            "gnn.gat1_norm"
        )

        nk = nk.replace(
            "gnn.gat2.norm",
            "gnn.gat2_norm"
        )

        nk = nk.replace(
            "gnn.consensus.k_sensitivity",
            "gnn.k_sensitivity"
        )

        remapped[nk] = v

    model = MultiTaskScalogramV3_v8(
        pretrained=False
    )

    model.load_state_dict(remapped)

    model.eval()

    print("[MODEL] Ready")

    return model

# ============================================================
# DATABASE
# ============================================================

def get_db():

    with open(DBCFG) as f:

        db = yaml.safe_load(f)

    conn = psycopg2.connect(
        host=db["host"],
        database=db["database"],
        user=db["user"],
        password=db["password"]
    )

    return conn

# ============================================================
# SAVE PREDICTION
# ============================================================

def save_prediction(
    station_code,
    probability,
    magnitude_class,
    azimuth,
    kp,
    dst
):

    conn = get_db()

    try:

        cur = conn.cursor()

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
                station_code,
                float(probability),
                int(magnitude_class),
                int(round(azimuth)),
                float(kp),
                float(dst),
                "V8_UBUNTU_PROD"
            )
        )

        conn.commit()

        print(
            "[DB] Prediction inserted"
        )

    finally:

        conn.close()

# ============================================================
# SCN -> TENSOR
# ============================================================

def build_tensor_from_scn(
    scn_file,
    station_code
):

    parser = SCNParser()

    data = parser.parse_scn_file(
        scn_file,
        station_code
    )

    proc = GeomagneticSignalProcessor()

    result = proc.process_components(
        data["H"],
        data["D"],
        data["Z"],
        apply_pc3=True
    )

    gen = V2TensorGenerator()

    tensor, _ = gen.generate_tensor(
        result["h_pc3"],
        result["d_pc3"],
        result["z_pc3"]
    )

    tensor = gen.zscore_normalize(
        tensor
    )

    return tensor.astype(
        np.float32
    )

# ============================================================
# INFERENCE
# ============================================================

def run_inference(
    model,
    tensor,
    kp=2.0,
    dst=-10.0
):

    x_img = torch.tensor(
        tensor,
        dtype=torch.float32
    ).unsqueeze(0)

    x_cos = torch.tensor(
        [[kp, dst]],
        dtype=torch.float32
    )

    with torch.no_grad():

        det, mag, azm, *_ = model(
            x_img,
            x_cos
        )

    probability = float(
        torch.softmax(
            det,
            dim=1
        )[0, 1]
    )

    magnitude_class = int(
        torch.argmax(
            mag,
            dim=1
        )
    )

    azimuth = float(
        azimuth_from_sincos(
            azm
        )[0]
    )

    return {
        "probability": probability,
        "magnitude_class": magnitude_class,
        "azimuth": azimuth
    }

# ============================================================
# MAIN
# ============================================================

def main():

    station_code = "SCN"

    scn_file = (
        "/opt/pimes/data/raw/SCN/"
        "S230101.SCN.gz"
    )

    kp = 2.0
    dst = -10.0

    model = load_model()

    print(
        "[SCN] Loading:",
        scn_file
    )

    tensor = build_tensor_from_scn(
        scn_file,
        station_code
    )

    print(
        "[TENSOR]",
        tensor.shape
    )

    result = run_inference(
        model,
        tensor,
        kp,
        dst
    )

    print(
        "\n[RESULT]"
    )

    print(result)

    save_prediction(
        station_code=station_code,
        probability=result["probability"],
        magnitude_class=result["magnitude_class"],
        azimuth=result["azimuth"],
        kp=kp,
        dst=dst
    )

    print(
        "\nDONE"
    )

# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    main()
