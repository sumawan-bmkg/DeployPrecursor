# LAWS Production Deployment Guide

**Version:** 1.2.0 (Final Release)  
**Target:** BMKG Central Server (API) + NVIDIA Jetson Nano (Edge)  
**Last Updated:** 2026-06-29

---

## 1. Server Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8 cores |
| RAM | 2 GB | 4 GB |
| Storage | 10 GB SSD | 50 GB SSD |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| Python | 3.10+ | 3.12+ |

## 2. Installation

```bash
# Clone & enter
git clone <repo> laws
cd laws

# Create venv
python -m venv .venv
source .venv/bin/activate

# Install production deps
pip install -r requirements.txt
pip install onnxruntime fastapi uvicorn
```

## 3. Model Weights

Place model files in `laws/core/weights/`:

| File | Source | Size |
|------|--------|------|
| `v8_supcon_merged.onnx` | From Phase 7 export | 37.8 MB |

> The server auto-detects ONNX first, falls back to PyTorch.

## 4. Starting the Server

```bash
# Mandatory: single worker (singleton core)
uvicorn laws.shared_api.app:app --host 0.0.0.0 --port 8000 --workers 1
```

Flags:
- `--workers 1` — **Mandatory.** Singleton encoder requires single process.
- `--host 0.0.0.0` — Listen on all interfaces.
- `--port 8000` — Default LAWS API port.

### Expected startup log

```
[SharedEncoder] ONNX loaded in 320ms
[MagnitudePredictor] Quantile models loaded from .../checkpoints
[StationActivityIndex] 22 stations
[WARMUP] Pre-warming all model components...
[WARMUP] Complete in 1.2s — all components ready
```

> Warmup prevents 1.4 GB memory spike when first station connects.

## 5. Docker Deployment

```dockerfile
FROM nvcr.io/nvidia/l4t-pytorch:r35.1.0-pth1.13-py3

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt && pip install onnxruntime fastapi uvicorn

EXPOSE 8000
CMD ["uvicorn", "laws.shared_api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

**Memory limit:** 2.5 GB (based on Phase 9 stress test: peak = 1.45 GB)

```bash
docker run --memory="2.5g" --cpus="4" -p 8000:8000 laws-server
```

## 6. Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Response:
```json
{
  "status": "operational",
  "version": "1.2.0",
  "backend": "onnx",
  "storm_gate": {"kp_threshold": 5.0, "dst_threshold": -50},
  "downstreams": ["magnitude", "activity"],
  "singleton": true
}
```

## 7. Client Request Example

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "station_code": "ALR",
    "timestamp_unix": 1782710400,
    "scalogram": [[[ ... 3×128×1440 float array ... ]]],
    "cosmic_kp": 2.3,
    "cosmic_dst": -15.0,
    "downstreams": ["magnitude", "activity"]
  }'
```

## 8. Storm Gate Behavior

| Condition | System Status | Magnitude Output |
|-----------|---------------|------------------|
| Kp < 5.0 AND Dst > -50 | `ACTIVE_NOMINAL` | Normal bounds (p10-p90) |
| Kp >= 5.0 OR Dst <= -50 | `QUIET_SPACE_WEATHER_DISTURBANCE` | `null` (suppressed) |

## 9. Performance Benchmarks (Phase 9)

| Metric | Value |
|--------|-------|
| p95 latency | <200 ms |
| Throughput | 220 req/s |
| Peak RAM | 1.45 GB |
| Docker limit | 2.5 GB |

## 10. Edge Deployment

See `laws/edge/edge_inference.py` for Jetson Nano inference script.
Requires: `onnxruntime`, `requests`. Zero PyTorch dependencies.
