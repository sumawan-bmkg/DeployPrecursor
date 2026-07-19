#!/usr/bin/env python3
"""
convert_to_tflite.py — Convert V8 SupCon PyTorch checkpoint → TFLite quantized model.

**Run on CUDA dev machine, NOT on Jetson Nano.**

Pipeline:
  1. Load PyTorch model from checkpoint
  2. Export to ONNX (via torch.onnx.export)
  3. Convert ONNX → TFLite (via tf.lite.TFLiteConverter.from_onnx)
  4. INT8 quantization with representative dataset
  5. Save to edge/models/

Also converts KDE priors from .pt → .npy for numpy-on-edge.

Usage:
    python convert_to_tflite.py --checkpoint ../checkpoints/v8_supcon_best.pth
    python convert_to_tflite.py --checkpoint ../checkpoints/v8_supcon_best.pth --quantize int8

Requires:
    torch, onnx, tensorflow (>=2.14), onnx-tf
"""

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("convert")

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
LAWS_DIR = SCRIPT_DIR.parent
CHECKPOINTS_DIR = LAWS_DIR / "checkpoints"
PRIORS_DIR = LAWS_DIR / "priors"
EDGE_MODELS_DIR = SCRIPT_DIR / "models"
EDGE_MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Model source
V8_MODEL_SRC = LAWS_DIR.parent / "ScalogramV3_V8_Repository" / "model" / "V3_Model_v8.py"


def load_pytorch_model(checkpoint_path: str, device: str = "cpu"):
    """Load V8 SupCon model from PyTorch checkpoint."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("V3_Model_v8", str(V8_MODEL_SRC))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ModelClass = mod.MultiTaskScalogramV3_v8

    model = ModelClass(pretrained=False)
    model = model.to(device)
    model.eval()

    state = torch.load(str(checkpoint_path), map_location=device)
    if isinstance(state, dict):
        sd = state.get("model_state_dict") or state.get("state_dict") or state
    else:
        sd = state

    sd_clean = {}
    for k, v in sd.items():
        k_clean = k.replace("module.", "").replace("_v8.", "")
        sd_clean[k_clean] = v

    missing, unexpected = model.load_state_dict(sd_clean, strict=False)
    if missing:
        logger.warning("Missing keys: %s", missing)
    if unexpected:
        logger.warning("Unexpected keys: %s", unexpected)
    logger.info("Model loaded from %s", checkpoint_path)
    return model


def export_to_onnx(model, onnx_path: str, device: str = "cpu"):
    """Export PyTorch model to ONNX format."""
    import torch

    # Dummy inputs matching training shape
    dummy_img = torch.randn(1, 3, 128, 1440, device=device)
    dummy_cosmic = torch.randn(1, 2, device=device)

    torch.onnx.export(
        model,
        (dummy_img, dummy_cosmic),
        onnx_path,
        input_names=["x_img", "x_cosmic"],
        output_names=["detection", "magnitude", "azimuth", "reg_score"],
        dynamic_axes={
            "x_img": {0: "batch"},
            "x_cosmic": {0: "batch"},
            "detection": {0: "batch"},
            "magnitude": {0: "batch"},
            "azimuth": {0: "batch"},
            "reg_score": {0: "batch"},
        },
        opset_version=17,
    )
    logger.info("ONNX exported to %s", onnx_path)


def convert_onnx_to_tflite(onnx_path: str, tflite_path: str,
                           quantize: str = "int8",
                           representative_path: str = None):
    """Convert ONNX model to TFLite with optional quantization."""
    import onnx
    from onnx_tf.backend import prepare
    import tensorflow as tf

    # ONNX → TF
    onnx_model = onnx.load(str(onnx_path))
    tf_rep = prepare(onnx_model)
    tf_model_path = str(onnx_path).replace(".onnx", "_tf")
    tf_rep.export_graph(tf_model_path)
    logger.info("TF model exported to %s", tf_model_path)

    # TF → TFLite
    converter = tf.lite.TFLiteConverter.from_saved_model(tf_model_path)
    converter.target_spec.supported_ops = [
        tf.lite.OpsSet.TFLITE_BUILTINS,
        tf.lite.OpsSet.SELECT_TF_OPS,  # GNN may need this
    ]

    if quantize == "int8":
        converter.optimizations = [tf.lite.Optimize.DEFAULT]

        # Representative dataset for INT8 calibration
        def representative_dataset():
            for _ in range(100):
                yield [
                    np.random.randn(1, 3, 128, 1440).astype(np.float32),
                    np.random.randn(1, 2).astype(np.float32),
                ]

        converter.representative_dataset = representative_dataset
        converter.target_spec.supported_types = [tf.float16]
        converter.inference_input_type = tf.float32  # Keep float32 input
        converter.inference_output_type = tf.float32
    elif quantize == "float16":
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.target_spec.supported_types = [tf.float16]
    else:
        # Float32 (no quantization)
        pass

    tflite_model = converter.convert()
    Path(tflite_path).write_bytes(tflite_model)
    size_mb = len(tflite_model) / (1024 * 1024)
    logger.info("TFLite saved to %s (%.2f MB, %s)", tflite_path, size_mb, quantize)
    return tflite_model


def convert_priors(priors_dir: str, output_path: str):
    """Convert KDE spatial priors from .pt → .npy."""
    import torch

    priors_dir = Path(priors_dir)
    station_order = [
        "ALR", "AMB", "CLP", "GTO", "KPY", "LPS", "LUT", "LWA", "LWK",
        "MLB", "PLU", "ROT", "SBG", "SCN", "SKB", "SMI", "SRG", "SRO",
        "TNT", "TRD", "TRT", "YOG", "UNK",
    ]
    n_bins = 360
    n_stations = len(station_order)
    priors = np.ones((n_stations, n_bins), dtype=np.float32) / n_bins

    for i, stn in enumerate(station_order):
        if stn == "UNK":
            continue
        pt_path = priors_dir / f"prior_{stn}.pt"
        if pt_path.exists():
            tensor = torch.load(str(pt_path), map_location="cpu")
            if tensor.shape == (n_bins,):
                priors[i] = tensor.numpy().astype(np.float32)
                # Normalize
                priors[i] /= priors[i].sum() + 1e-12

    np.save(str(output_path), priors)
    logger.info("Priors saved to %s — shape %s", output_path, priors.shape)
    return priors


def validate_tflite(tflite_path: str, priors_path: str = None):
    """Run a sanity check on the converted TFLite model."""
    import numpy as np

    try:
        from tflite_runtime.interpreter import Interpreter
    except ImportError:
        try:
            import tensorflow as tf
            interpreter = tf.lite.Interpreter(model_path=tflite_path)
        except ImportError:
            logger.warning("tflite-runtime not installed, skipping validation")
            return
    else:
        interpreter = Interpreter(model_path=tflite_path)

    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    # Run dummy inference
    dummy_img = np.random.randn(1, 3, 128, 1440).astype(np.float32)
    dummy_cosmic = np.random.randn(1, 2).astype(np.float32)

    interpreter.set_tensor(input_details[0]["index"], dummy_img)
    if len(input_details) > 1:
        interpreter.set_tensor(input_details[1]["index"], dummy_cosmic)
    interpreter.invoke()

    # Read outputs
    for det in output_details:
        tensor = interpreter.get_tensor(det["index"])
        logger.info("  Output '%s': shape=%s, min=%.4f, max=%.4f",
                    det["name"], tensor.shape, tensor.min(), tensor.max())

    logger.info("TFLite validation PASSED — %s", tflite_path)


def main():
    parser = argparse.ArgumentParser(
        description="Convert V8 SupCon PyTorch → TFLite for Jetson Nano"
    )
    parser.add_argument("--checkpoint", type=str,
                        default=str(LAWS_DIR / "checkpoints" / "v8_supcon_best.pth"),
                        help="PyTorch checkpoint path")
    parser.add_argument("--quantize", choices=["float32", "float16", "int8"],
                        default="int8",
                        help="Quantization mode (default: int8)")
    parser.add_argument("--output-dir", type=str, default=str(EDGE_MODELS_DIR),
                        help="Output directory for TFLite + priors")
    parser.add_argument("--validate", action="store_true", default=True,
                        help="Run validation after conversion")
    parser.add_argument("--skip-onnx", action="store_true",
                        help="Skip ONNX export if .onnx already exists")
    args = parser.parse_args()

    import numpy as np
    import torch

    # Resolve checkpoint path
    ckpt = Path(args.checkpoint)
    if not ckpt.is_absolute():
        ckpt = CHECKPOINTS_DIR / ckpt.name
    if not ckpt.exists():
        logger.error("Checkpoint not found: %s", ckpt)
        sys.exit(1)

    # Paths
    onnx_path = Path(args.output_dir) / "v8_supcon.onnx"
    tflite_path = Path(args.output_dir) / "v8_supcon_int8.tflite"
    priors_out = Path(args.output_dir) / "priors.npy"

    # Step 1: Convert priors .pt → .npy
    logger.info("=" * 60)
    logger.info("STEP 1/4: Converting KDE priors .pt → .npy")
    convert_priors(str(PRIORS_DIR), str(priors_out))

    # Step 2: Export PyTorch → ONNX
    logger.info("=" * 60)
    logger.info("STEP 2/4: Exporting PyTorch → ONNX")
    if args.skip_onnx and onnx_path.exists():
        logger.info("Skipping ONNX export (already exists: %s)", onnx_path)
    else:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = load_pytorch_model(str(ckpt), device=device)
        export_to_onnx(model, str(onnx_path), device=device)

    # Step 3: ONNX → TFLite
    logger.info("=" * 60)
    logger.info("STEP 3/4: Converting ONNX → TFLite (%s)", args.quantize)
    if args.skip_onnx and tflite_path.exists():
        logger.info("Skipping TFLite conversion (already exists: %s)", tflite_path)
    else:
        convert_onnx_to_tflite(str(onnx_path), str(tflite_path), quantize=args.quantize)

    # Step 4: Validate
    if args.validate:
        logger.info("=" * 60)
        logger.info("STEP 4/4: Validating TFLite model")
        validate_tflite(str(tflite_path), str(priors_out))

    # Summary
    logger.info("=" * 60)
    logger.info("CONVERSION COMPLETE")
    logger.info("  TFLite:  %s", tflite_path)
    logger.info("  Priors:  %s", priors_out)
    logger.info("  Size:    %.1f MB", tflite_path.stat().st_size / (1024 * 1024))
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
