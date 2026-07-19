"""
LAWS Edge Inference — v1.0.0 (Jetson Nano)
============================================
ZERO PyTorch dependencies. Uses ONNX Runtime + requests.

Pipeline:
  1. Load scalogram (numpy) from sensor
  2. Run ONNX model → 128D projection vector
  3. POST to LAWS API → get magnitude bounds + analogues
  4. Display result

Usage:
  python edge_inference.py --img sample.npy [--cosmic 2.3,-15] [--server http://10.0.0.1:8000]
  python edge_inference.py --img sample.npy --dry-run  (no API call)
"""
import os, sys, json, time, argparse, struct
import numpy as np
from pathlib import Path
from datetime import datetime

try:
    import onnxruntime
except ImportError:
    print("[FAIL] onnxruntime required: pip install onnxruntime")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("[FAIL] requests required: pip install requests")
    sys.exit(1)

LAWS_EDGE = Path(__file__).resolve().parent
MODEL_DIR = LAWS_EDGE / "models"


def load_model(model_path=None):
    """Load ONNX Runtime session. Falls back to INT8 then FP32."""
    if model_path is None:
        candidates = [
            MODEL_DIR / "v8_supcon_int8.onnx",
            MODEL_DIR / "v8_supcon.onnx",
        ]
        for p in candidates:
            if p.exists():
                model_path = str(p)
                break
        if model_path is None:
            raise FileNotFoundError("No model found in " + str(MODEL_DIR))

    providers = ['CPUExecutionProvider']
    # Use TensorRT if available (Jetson Nano)
    if 'TensorrtExecutionProvider' in onnxruntime.get_available_providers():
        providers = ['TensorrtExecutionProvider', 'CUDAExecutionProvider', 'CPUExecutionProvider']
    elif 'CUDAExecutionProvider' in onnxruntime.get_available_providers():
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']

    session = onnxruntime.InferenceSession(model_path, providers=providers)
    print(f"  Model: {model_path}")
    print(f"  Providers: {session.get_providers()}")
    print(f"  Inputs: {[(i.name, i.shape) for i in session.get_inputs()]}")
    print(f"  Outputs: {[(o.name, o.shape) for o in session.get_outputs()]}")
    return session


def preprocess(scalogram_path, cosmic=None):
    """Load and prepare scalogram for inference.

    Args:
        scalogram_path: path to .npy file with shape (3, 128, 1440) or (1, 3, 128, 1440)
        cosmic: optional (2,) array [kp, dst] or comma-separated string "kp,dst"

    Returns:
        input_img: (1, 3, 128, 1440) float32
        input_cosmic: (1, 2) float32
    """
    img = np.load(str(scalogram_path)).astype(np.float32)
    if img.ndim == 3:
        img = img[np.newaxis, ...]  # (1, 3, 128, 1440)
    elif img.ndim == 4 and img.shape[0] != 1:
        img = img[:1]  # take first batch

    # Handle cosmic features
    if cosmic is None:
        cosmic_arr = np.array([[2.0, -15.0]], dtype=np.float32)  # default
    elif isinstance(cosmic, str):
        parts = cosmic.split(',')
        cosmic_arr = np.array([[float(parts[0]), float(parts[1])]], dtype=np.float32)
    else:
        cosmic_arr = np.asarray(cosmic, dtype=np.float32).reshape(1, -1)

    return img, cosmic_arr


def extract_proj_vec(session, img, cosmic):
    """Run ONNX inference, return 128D L2-normalized projection vector."""
    ort_inputs = {
        session.get_inputs()[0].name: img,
        session.get_inputs()[1].name: cosmic,
    }
    t0 = time.time()
    proj_vec = session.run(None, ort_inputs)[0]  # (1, 128)
    latency_ms = (time.time() - t0) * 1000
    return proj_vec[0], latency_ms


def query_api(proj_vec, kp, dst, station, api_url, timeout=5):
    """POST to LAWS API, return parsed response."""
    payload = {
        "station_code": station,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "environmental_factors": {"kp_index": kp, "dst_index": dst},
        "latent_vector": proj_vec.tolist(),
        "local_inference_status": "REVIEW",
    }
    t0 = time.time()
    resp = requests.post(
        api_url + "/api/v1/magnitude-assistance",
        json=payload,
        timeout=timeout,
    )
    api_latency = (time.time() - t0) * 1000
    resp.raise_for_status()
    return resp.json(), api_latency


def main():
    parser = argparse.ArgumentParser(description="LAWS Edge Inference")
    parser.add_argument("--img", required=True, help="Path to .npy scalogram")
    parser.add_argument("--cosmic", default="2.0,-15.0", help="Kp,Dst values")
    parser.add_argument("--station", default="LAWS", help="Station code")
    parser.add_argument("--server", default="http://localhost:8000",
                        help="LAWS API server URL")
    parser.add_argument("--model", default=None, help="Override model path")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run inference only, skip API call")
    args = parser.parse_args()

    print(f"\n{'=' * 50}")
    print(f"LAWS Edge Inference v1.0.0")
    print(f"{'=' * 50}")
    print(f"  Image:     {args.img}")
    print(f"  Cosmic:    {args.cosmic}")
    print(f"  Station:   {args.station}")
    print(f"  Server:    {args.server}")
    print(f"  Dry-run:   {args.dry_run}")

    # Load
    session = load_model(args.model)
    img, cosmic = preprocess(args.img, args.cosmic)
    print(f"  Input shape: {img.shape}, cosmic: {cosmic.shape}")

    # Infer
    proj_vec, infer_ms = extract_proj_vec(session, img, cosmic)
    print(f"\n  Inference: {infer_ms:.2f} ms")
    print(f"  proj_vec[:5]:  {proj_vec[:5]}")
    print(f"  proj_vec norm: {np.linalg.norm(proj_vec):.6f} (should be ~1.0)")

    # API
    if args.dry_run:
        print("\n[DRY-RUN] API call skipped.")
        print(f"  Payload latent_vector (128 floats)")
        return

    try:
        kp, dst = [float(x) for x in args.cosmic.split(',')]
        result, api_ms = query_api(
            proj_vec, kp, dst, args.station, args.server)

        print(f"\n{'=' * 50}")
        print(f"LAWS API RESPONSE")
        print(f"{'=' * 50}")
        print(f"  API Latency: {api_ms:.1f} ms")

        lai = result.get('lithosphere_activity_index', {})
        print(f"\n  ├─ LAI Score:      {lai.get('mahalanobis_distance', '?'):.4f}")
        print(f"  ├─ Threshold p95:  {lai.get('threshold_p95', '?')}")
        print(f"  ├─ System Status:  {lai.get('system_status', '?')}")

        mag = result.get('magnitude_assistance', {})
        est = mag.get('estimated_magnitude')
        if est:
            print(f"  └─ Magnitude:")
            print(f"       ├─ Value:     {est.get('value')}")
            print(f"       ├─ Lower p10: {est.get('lower_bound_p10')}")
            print(f"       └─ Upper p90: {est.get('upper_bound_p90')}")

        analogues = mag.get('historical_analogues', [])
        if analogues:
            print(f"\n  Historical Analogues:")
            for a in analogues[:3]:
                print(f"    └─ {a.get('event_name')}: M{a.get('magnitude')} "
                      f"(sim: {a.get('similarity_score'):.3f})")

    except Exception as e:
        print(f"\n[FAIL] API call failed: {e}")


if __name__ == "__main__":
    main()
