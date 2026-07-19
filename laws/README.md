# BMKG LAWS — Geomagnetic Lithosphere Activity Warning System

**Version:** 1.0 (Production Frozen)  
**Status:** Ready for BMKG VM Deployment  
**Architecture:** Hybrid V9.5 PIMES (CNN+GNN) + LightGBM V2 Magnitude Regressor

---

## 🎯 System Overview

This system provides real-time lithosphere activity warning by analyzing Ultra-Low Frequency (ULF) geomagnetic precursor signals from multiple ground stations. The hybrid pipeline:

1. **Storm Gatekeeper** — Filters geomagnetic storm interference (Kp/Dst indices)
2. **V9.5 PIMES (Deep Learning)** — Detects earthquake probability and azimuth from CWT scalogram imagery
3. **LightGBM V2 Regressor** — Estimates magnitude from 53 spatio-temporal ULF2 features

**Key Features:**
- ⚡ Sub-second inference (CPU: ~730ms, GPU: <100ms estimated)
- 🔒 Magnitude guardrails (clipped to 3.0–6.5 Mw, confidence-based alert status)
- 🐳 Docker-ready production deployment
- 📊 Real-time feature extraction from raw magnetometer signals (H, D, Z components)

---

## 📋 Prerequisites

### Hardware Requirements
- **CPU:** 4+ cores recommended
- **RAM:** 8 GB minimum, 16 GB recommended
- **GPU (Optional):** NVIDIA GPU with CUDA 11.8+ for accelerated inference

### Software Requirements
- **OS:** Ubuntu 20.04+ or compatible Linux distribution
- **Docker:** Version 20.10+
- **Docker Compose:** Version 1.29+
- **NVIDIA Container Toolkit** (if using GPU): [Installation Guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

---

## 🚀 Installation & Deployment

### Step 1: Extract Deployment Package

```bash
tar -xzf BMKG_LAWS_Production_v1.0.tar.gz
cd laws
```

### Step 2: Configure Environment

Create a `.env` file from the template:

```bash
cp .env.example .env
nano .env
```

**Required `.env` variables:**

```bash
# Device selection
LAWS_DEVICE=cuda          # Use 'cuda' for GPU, 'cpu' for CPU-only

# API server configuration
LAWS_HOST=0.0.0.0
LAWS_PORT=8000
LAWS_LOG_LEVEL=info       # Options: debug, info, warning, error

# Data paths (optional overrides)
LAWS_H5_DIR=/path/to/h5/data  # Override default HDF5 data location
```

### Step 3: Place Model Checkpoints

Ensure the following files exist in `checkpoints/`:

- `v95_pimes_champion.pth` — V9.5 deep learning model (~48 MB)
- `lgbm_mag_regression_v2_stable.pkl` — LightGBM magnitude model (~500 KB)

**Note:** If checkpoints are missing, the API will fail to start. Contact the research team for checkpoint files.

### Step 4: Build and Start Docker Container

```bash
docker-compose up --build -d
```

**Expected output:**
```
Creating network "laws_default" ...
Building LAWS_api...
Successfully built [image_id]
Creating LAWS_api_1 ... done
```

### Step 5: Verify Deployment

Check API health:

```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "ok",
  "models_loaded": true,
  "device": "cuda",
  "lgbm_checkpoint": "checkpoints/lgbm_mag_regression_v2_stable.pkl",
  "v95_checkpoint": "checkpoints/v95_pimes_champion.pth",
  ...
}
```

View logs:

```bash
docker logs -f LAWS_api_1
```

---

## 📡 API Usage

### Endpoint: `POST /predict`

**Full hybrid pipeline** — Storm gate → V9.5 detection → LightGBM magnitude

**Request body:**

```json
{
  "date": "20260616",
  "kp_index": 2.5,
  "dst_index": -15.0,
  "raw_signals": [
    {
      "station_id": "YOG",
      "raw_h": [/* 1440 float values */],
      "raw_d": [/* 1440 float values */],
      "raw_z": [/* 1440 float values */]
    },
    {
      "station_id": "SCN",
      "raw_h": [/* 1440 float values */],
      "raw_d": [/* 1440 float values */],
      "raw_z": [/* 1440 float values */]
    }
  ]
}
```

**Response:**

```json
{
  "timestamp": "2026-06-16T10:30:00Z",
  "earthquake_detected": true,
  "detection_prob": 0.87,
  "azimuth_deg": 135.2,
  "magnitude": 4.8,
  "magnitude_source": "lgbm_v2_stable_guarded",
  "alert_status": "DANGER",
  "per_station_magnitudes": {
    "YOG": 4.7,
    "SCN": 4.9
  },
  "storm_mode": false,
  "inference_time_ms": 732.5,
  "server_metrics": {
    "cwt_generation_ms": 26.3,
    "v95_inference_ms": 435.1,
    "ulf2_extraction_ms": 45.6,
    "lgbm_inference_ms": 0.98
  }
}
```

**Alert Status Values:**
- `NORMAL` — No earthquake detected
- `WARNING_LOW_MAGNITUDE` — Detection with Mw < 4.5 (low confidence)
- `DANGER` — Detection with Mw ≥ 4.5

---

## 📊 Monitoring & Maintenance

### Viewing Prediction Logs

Operational predictions are logged to:

```
logs/operational_predictions.csv
```

**Log rotation:** Logs are timestamped daily. Archive old logs periodically to prevent disk bloat.

### Updating Model Checkpoints

To deploy updated models without downtime:

1. **Stop the container:**
   ```bash
   docker-compose down
   ```

2. **Replace checkpoint files** in `checkpoints/`:
   ```bash
   cp /path/to/new_model.pkl checkpoints/lgbm_mag_regression_v2_stable.pkl
   ```

3. **Restart the container:**
   ```bash
   docker-compose up -d
   ```

### Performance Tuning

**GPU Acceleration:**
- Ensure `LAWS_DEVICE=cuda` in `.env`
- Verify GPU is accessible: `nvidia-smi`

**CPU-Only Mode:**
- Set `LAWS_DEVICE=cpu` in `.env`
- Expected RTT: ~730 ms per prediction

---

## 🔧 Troubleshooting

### Container fails to start

**Symptom:** `docker-compose up` exits with error

**Solutions:**
- Check logs: `docker logs LAWS_api_1`
- Verify checkpoint files exist in `checkpoints/`
- Ensure `.env` has correct `LAWS_DEVICE` (use `cpu` if no GPU)

### High latency (>2 seconds per prediction)

**Possible causes:**
- Running on CPU without GPU acceleration
- Large batch size (>5 stations per request)
- Network I/O bottleneck

**Solutions:**
- Enable GPU with `LAWS_DEVICE=cuda`
- Limit to 3-4 stations per request
- Check system CPU/RAM usage

### "Models not loaded" error

**Cause:** API started before models finished loading

**Solution:** Wait 5-10 seconds after container starts, then retry request

---

## 📞 Support & Contact

For technical issues or model updates, contact:

- **Research Team:** [Your contact info]
- **BMKG IT Support:** [BMKG contact info]

---

## 📄 License & Attribution

**Developed by:** [Your team/institution]  
**For:** BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)  
**License:** [Specify license, e.g., proprietary, GPL, MIT]

---

**Status:** Production Frozen (Phase 11) — Ready for operational deployment.
