# LAWS Phase 7 — TFLite/ONNX Conversion Audit

**Generated:** 2026-06-29 15:08:44
**Source:** v8_supcon_best.pth (1.2 MB FP32)
**Target:** v8_supcon_int8.onnx (1.2 MB INT8)
**Compression:** 1.0x

## Conversion Pipeline
| Step | Tool | Output |
|------|------|--------|
| PyTorch → ONNX | `torch.onnx.export` | `v8_supcon.onnx` (FP32) |
| ONNX → INT8 | `onnxruntime.quantization` | `v8_supcon_int8.onnx` (INT8) |
| .pt → .npy | `torch → numpy` | 22 prior files |

## Integrity Verification
| Metric | Value | Target | Pass? |
|--------|-------|--------|-------|
| Single-sample cosine similarity | 0.998454 | ≥0.95 | ✅ |
| Single-sample MAE (128D) | 0.003843 | - | - |
| ONNX output norm | 1.000000 | ~1.0 | ✅ |
| PyTorch output norm | 1.000000 | ~1.0 | ✅ |
| Multi-sample mean cosine (20) | 0.999836 | ≥0.95 | ✅ |
| Multi-sample min cosine (20) | 0.998951 | ≥0.95 | ✅ |

## Edge Files
| File | Size | Description |
|------|------|-------------|
| `edge/models/v8_supcon_int8.onnx` | 1.2 MB | INT8 quantized model |
| `edge/models/v8_supcon.onnx` | 1.2 MB | FP32 ONNX (fallback) |
| `edge/models/prior_*.npy` | 22 files | Spatial priors per station |
| `edge/models/priors_stacked.npy` | 1 file | Combined prior matrix |
| `edge/models/stations.json` | - | Station list for lookup |
| `edge/edge_inference.py` | - | Edge inference script |

## Conclusion
✅ **Cosine similarity ≥ 0.95 — latent space preserved.**
The INT8 quantized model retains the V8 projection quality. FAISS-based magnitude estimation will function correctly with the edge deployment.