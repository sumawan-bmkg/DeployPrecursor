"""
LAWS Shared Core — V8 SupCon Projection Encoder
=================================================
Singleton encoder: "Single Inference, Multiple Downstreams".

Loads frozen V8 backbone **once**, produces 128D latent
embedding per station per window. Embedding is distributed
to ALL downstream modules without reloading the backbone.

Architecture:
  ┌─────────────────────────────────────────────┐
  │          SHARED CORE (frozen)                │
  │  EfficientNet-B1 → GRU → GNN → Cosmic Gate  │
  │              → projection_head → 128D        │
  └─────────────┬───────────────────────────────┘
                │ 128D (L2-normalized)
        ┌───────┼───────────┐
        ▼       ▼           ▼
   ┌────────┐ ┌──────┐ ┌──────────┐
   │FAISS   │ │LAI   │ │ LT-LAF   │
   │k-NN    │ │Maha  │ │SpTemp    │
   │mag     │ │dist  │ │State Est │
   └────────┘ └──────┘ └──────────┘

Usage:
  from laws.core.v8_supcon_encoder import SharedEncoder
  encoder = SharedEncoder()         # loads model once
  proj_128d = encoder.encode(scalogram, cosmic)  # (1, 128)
"""
import os, sys, json, copy, time
import numpy as np
from pathlib import Path
from functools import lru_cache

LAWS = Path(__file__).resolve().parents[1]
CKPT = LAWS / "core" / "weights"
DEVICE = "cpu"

# ── Backend detection: PyTorch (server) vs ONNX (edge) ──────────
_BACKEND = None

def _detect_backend():
    global _BACKEND
    if _BACKEND is not None:
        return _BACKEND
    # Prefer ONNX for edge deployment
    onnx_path = CKPT / "v8_supcon_merged.onnx"
    pytorch_path = LAWS / "checkpoints" / "v8_supcon_best.pth"
    if onnx_path.exists():
        _BACKEND = "onnx"
    elif pytorch_path.exists():
        _BACKEND = "torch"
    else:
        _BACKEND = None
    return _BACKEND


class SharedEncoder:
    """
    Singleton shared encoder. Only ONE instance ever created.
    Loads frozen V8 backbone at first call.
    """

    _instance = None
    _model = None
    _backend = None
    _metadata = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._model is None:
            self._load_model()

    def _load_model(self):
        """Load model once. Frozen. Eval mode."""
        t0 = time.time()
        backend = _detect_backend()

        if backend == "onnx":
            import onnxruntime
            model_path = str(CKPT / "v8_supcon_merged.onnx")
            sess = onnxruntime.InferenceSession(
                model_path, providers=['CPUExecutionProvider'])
            self._model = sess
            self._backend = "onnx"
            self._metadata = {
                "backend": "onnx",
                "path": model_path,
                "providers": sess.get_providers(),
                "input_names": [i.name for i in sess.get_inputs()],
                "input_shapes": [i.shape for i in sess.get_inputs()],
            }
            load_ms = (time.time() - t0) * 1000
            print(f"[SharedEncoder] ONNX loaded in {load_ms:.0f}ms")

        elif backend == "torch":
            import torch
            sys.path.insert(0, str(LAWS.parent))
            from ScalogramV3_V8_Repository.model.V3_Model_v8 import MultiTaskScalogramV3_v8 as V8Model

            model = V8Model(pretrained=False)
            model = model.to(DEVICE)
            state = torch.load(
                str(CKPT / "v8_supcon_best.pth"),
                map_location=DEVICE, weights_only=True)
            model.load_state_dict(state, strict=False)

            # FREEZE: no gradients, eval mode
            for p in model.parameters():
                p.requires_grad = False
            model.eval()

            self._model = model
            self._backend = "torch"
            self._metadata = {
                "backend": "torch",
                "path": str(CKPT / "v8_supcon_best.pth"),
                "frozen": True,
                "device": DEVICE,
            }
            load_ms = (time.time() - t0) * 1000
            print(f"[SharedEncoder] PyTorch loaded in {load_ms:.0f}ms")

        else:
            raise FileNotFoundError(
                "No model found. Place v8_supcon_merged.onnx in "
                f"{CKPT} or v8_supcon_best.pth in {LAWS / 'checkpoints'}")

    @property
    def metadata(self):
        """Return copy of encoder metadata (thread-safe)."""
        return dict(self._metadata)

    def encode(self, scalogram: np.ndarray, cosmic: np.ndarray) -> np.ndarray:
        """
        Produce 128D L2-normalized projection vector.

        Args:
            scalogram: (1, 3, 128, 1440) float32 — scalogram image
            cosmic:    (1, 2) float32 — [Kp_norm, Dst_norm]

        Returns:
            proj_vec:  (1, 128) float32, L2-normalized to unit sphere
        """
        # ── Shape verification ─────────────────────────────────
        assert scalogram.ndim == 4, f"scalogram: expected 4D, got {scalogram.ndim}D"
        assert scalogram.shape == (1, 3, 128, 1440), \
            f"scalogram: expected (1,3,128,1440), got {scalogram.shape}"
        assert cosmic.ndim == 2, f"cosmic: expected 2D, got {cosmic.ndim}D"
        assert cosmic.shape == (1, 2), \
            f"cosmic: expected (1,2), got {cosmic.shape}"

        if self._backend == "onnx":
            inp_name = self._model.get_inputs()[0].name
            cosm_name = self._model.get_inputs()[1].name
            out = self._model.run(
                None, {inp_name: scalogram, cosm_name: cosmic})[0]
            return out.astype(np.float32)

        else:
            import torch
            with torch.no_grad():
                img_t = torch.from_numpy(scalogram).to(DEVICE)
                cosm_t = torch.from_numpy(cosmic).to(DEVICE)
                proj = self._model(img_t, cosm_t)[5]  # index 5 = proj_vec
            return proj.cpu().numpy().astype(np.float32)

    def __call__(self, scalogram, cosmic):
        return self.encode(scalogram, cosmic)


# ── Convenience ────────────────────────────────────────────────
def get_encoder() -> SharedEncoder:
    """Get or create shared encoder singleton."""
    return SharedEncoder()


# ── Self-test ──────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("SHARED ENCODER — Isolation Test")
    print("=" * 60)

    # Test singleton
    e1 = SharedEncoder()
    e2 = SharedEncoder()
    assert e1 is e2, "Singleton broken!"
    print("✅ Singleton: e1 is e2")

    # Test metadata
    meta = e1.metadata
    print(f"✅ Backend: {meta['backend']}")

    # Test inference with dummy data
    dummy_img = np.random.randn(1, 3, 128, 1440).astype(np.float32)
    dummy_cosmic = np.random.randn(1, 2).astype(np.float32)

    t0 = time.time()
    proj = e1.encode(dummy_img, dummy_cosmic)
    infer_ms = (time.time() - t0) * 1000
    norm = np.linalg.norm(proj)

    assert proj.shape == (1, 128), f"Expected (1,128), got {proj.shape}"
    assert abs(norm - 1.0) < 0.01, f"L2 norm {norm} != 1.0"

    print(f"✅ Shape: {proj.shape}")
    print(f"✅ L2 norm: {norm:.6f} (unit sphere)")
    print(f"✅ Inference: {infer_ms:.2f}ms")
    print(f"✅ proj[:5]: {proj[0][:5]}")

    # Bigger test: 50 runs, measure stability
    latencies = []
    norms = []
    for i in range(50):
        img = np.random.randn(1, 3, 128, 1440).astype(np.float32)
        cosm = np.random.randn(1, 2).astype(np.float32)
        t0 = time.time()
        p = e1.encode(img, cosm)
        latencies.append((time.time() - t0) * 1000)
        norms.append(np.linalg.norm(p))

    print(f"\n✅ Stability (50 runs):")
    print(f"   Mean latency: {np.mean(latencies):.2f}ms")
    print(f"   Std latency:  {np.std(latencies):.2f}ms")
    print(f"   Mean norm:    {np.mean(norms):.6f}")
    print(f"   Std norm:     {np.std(norms):.6f}")
    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
