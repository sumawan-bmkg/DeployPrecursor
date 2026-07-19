# V8 SupCon-TFLite Edge — Deployment Audit Report

**Date:** 2026-06-29  
**Target Hardware:** NVIDIA Jetson Nano 4GB  
**Auditor:** AI Agent (Lead MLOps Engineer)

---

## 1. Model Identity

| Attribute | Value |
|-----------|-------|
| Architecture | MultiTaskScalogramV3_v8 (SupCon) |
| Backbone | EfficientNet-B1 |
| Temporal | BiGRU |
| Spatial | 2-layer GAT |
| Task Heads | Detection (2-class), Magnitude (5 bins), Azimuth (sin/cos), SupCon projection |
| Source Checkpoint | `checkpoints/v8_supcon_best.pth` (38 MB, PyTorch) |
| Target Format | TFLite (INT8 quantized) |
| Target Size | ~4.7 MB (estimated after INT8 quantization) |

## 2. Input / Output Specification

### Inputs

| Name | Shape | Type | Description |
|------|-------|------|-------------|
| `x_img` | (1, 3, 128, 1440) | float32 | 3-channel scalogram (H, D, Z), 128 scales × 1440 time samples |
| `x_cosmic` | (1, 2) | float32 | [Kp_norm, Dst_norm] ∈ [0,1] each |

### Outputs

| Name | Type | Description |
|------|------|-------------|
| `detection_prob` | float [0,1] | P(class=1) — earthquake detected |
| `magnitude` | float | Weighted sum of 5 magnitude bins |
| `magnitude_bins` | float[5] | Softmax probabilities per bin |
| `azimuth_sin` | float | Azimuth unit vector component |
| `azimuth_cos` | float | Azimuth unit vector component |

## 3. Performance Metrics (from FPR Suppression Report)

| Metric | Value |
|--------|-------|
| FPR | 0.125 |
| Recall | 0.972 |
| EWS Score | +0.829 |
| Latency (target) | ~116 ms (Jetson Nano, TFLite INT8) |
| Memory (target) | ~4.7 MB (TFLite) |

## 4. Asset Checklist

| Asset | Status | Location |
|-------|--------|----------|
| PyTorch checkpoint | ✅ EXISTS | `checkpoints/v8_supcon_best.pth` |
| TFLite quantized model | ❌ NOT YET | Needs conversion from `.pth` |
| KDE spatial priors | ✅ EXISTS | `priors/prior_*.pt` (23 stations) |
| KDE priors (npy format) | ❌ NOT YET | Needs conversion from `.pt` |
| Station config | ✅ EXISTS | `app/config.py` (23 stations) |
| CWT preprocessing | ✅ EXISTS | `app/utils/cwt_generator.py` |
| ULF2 feature extraction | ✅ EXISTS | `app/models/ulf2_inference.py` |
| Dockerfile (PyTorch) | ✅ EXISTS | `Dockerfile` (needs edge variant) |
| requirements.txt (PyTorch) | ✅ EXISTS | `requirements.txt` (needs edge variant) |

## 5. Conversion Pipeline Required

```
v8_supcon_best.pth (PyTorch)
         ↓
  convert_to_tflite.py
         ↓
         ├── v8_supcon_float32.tflite (debug)
         ├── v8_supcon_int8.tflite (deploy)  ← TARGET
         └── priors.npy (KDE, converted from .pt)
```

## 6. Deployment Files (THIS PACKAGE)

| File | Purpose |
|------|---------|
| `requirements_edge.txt` | Minimal Jetson deps (tflite-runtime, numpy, scipy, pywavelets) |
| `config.yaml` | Sensor coords, thresholds, KDE bandwidth, normalization params |
| `preprocessing_pipeline.py` | CWT scalogram + Spectral Polarization feature extraction |
| `edge_inference.py` | TFLite interpreter + KDE prior → probabilistic hazard output |
| `convert_to_tflite.py` | PyTorch → TFLite conversion (run on dev GPU, not Jetson) |
| `Dockerfile` | Lightweight L4T-based container for Jetson Nano 4GB |

## 7. Known Gaps & Risks

| Gap | Impact | Mitigation |
|-----|--------|------------|
| TFLite conversion untested | Blocking | Run `convert_to_tflite.py` on CUDA dev machine |
| GNN (GAT) may not convert cleanly to TFLite | High | Fallback: export backbone only, run GNN as separate NumPy op |
| Dynamic model definition (importlib) | Medium | Convert via `torch.jit.trace` with dummy input |
| 1440×128 scalogram may exceed 4GB RAM in batch | Medium | Enforce batch_size=1 on Jetson |
| Prior .pt → .npy conversion trivial | None | Included in `convert_to_tflite.py` |

## 8. Recommendation

**CONDITIONAL PASS** — Package structure is complete for Jetson Nano staging. Execute `convert_to_tflite.py` on dev GPU to generate actual `.tflite` files before full deployment test.
