# V8 SupCon-TFLite Edge — BMKG LAWS Deployment Package

**Target Hardware:** NVIDIA Jetson Nano 4GB  
**Model:** MultiTaskScalogramV3_v8 (Supervised Contrastive Learning)  
**Inference Format:** TFLite INT8 Quantized

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Raw Magnetometer (H, D, Z) — 1440 samples/min              │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Preprocessing Pipeline                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐ │
│  │  CWT (cmor)  │  │ Z-score norm │  │  Polarization      │ │
│  │  128 scales  │  │ per channel  │  │  Ratio (H/D)       │ │
│  └─────────────┘  └──────────────┘  └────────────────────┘ │
│  Output: (3, 128, 1440) float32 scalogram                  │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  V8 SupCon TFLite (INT8) — ~4.7 MB                         │
│  ┌──────────────────────┐  ┌──────────────────────┐         │
│  │  EfficientNet-B1     │  │  BiGRU Temporal      │         │
│  │  Backbone            │  │  Feature Processing  │         │
│  └──────────┬───────────┘  └──────────┬───────────┘         │
│             └──────────┬──────────────┘                      │
│                        ↓                                     │
│  ┌──────────────────────────────────────────────┐            │
│  │  Task Heads                                  │            │
│  │  Detection(2) | Mag(5 bins) | Azimuth(sin/cos)│           │
│  └──────────────────────────────────────────────┘            │
│  Latency: ~116 ms (Nano)                                    │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Bayesian KDE Spatial Prior (23 stations × 360 bins)        │
│  → Station-aware azimuth calibration                        │
│  → Bayesian posterior: P(event | data, station)             │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Decision Engine                                            │
│  4-STATE: SAFE | MONITOR | REVIEW | ALERT                   │
│  + Hysteresis (60-min cooldown)                             │
│  + Storm Gate (Kp>4.0 or Dst<-30 → suppression)            │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
                     JSON Output
```

## File Structure

```
edge/
├── DEPLOYMENT_AUDIT.md         # Formal audit report
├── README.md                   # This file
├── requirements_edge.txt       # Jetson Nano deps
├── config.yaml                 # All parameters
├── preprocessing_pipeline.py   # CWT + spectral polarization
├── edge_inference.py           # Full inference pipeline
├── convert_to_tflite.py        # PyTorch→TFLite converter
├── Dockerfile                  # L4T-based container
├── models/                     # (created by convert_to_tflite.py)
│   ├── v8_supcon_int8.tflite   # Quantized model
│   └── priors.npy              # KDE spatial priors (23×360)
└── output/                     # Inference results (JSON)
```

## Quick Start

### 1. Convert Model (on dev machine with GPU)

```bash
cd laws/edge
pip install torch onnx tensorflow onnx-tf
python convert_to_tflite.py --checkpoint ../checkpoints/v8_supcon_best.pth --quantize int8
```

### 2. Build Docker (on Jetson)

```bash
docker build -t LAWS-v8-edge:latest .
docker run --runtime nvidia -v ./output:/app/output LAWS-v8-edge:latest
```

### 3. Standalone Run (on Jetson)

```bash
pip install -r requirements_edge.txt
python edge_inference.py --station ALR --kp 2.0 --dst -10.0
```

## Key Metrics

| Metric | Value |
|--------|-------|
| FPR | 0.125 |
| Recall | 0.972 |
| EWS Score | +0.829 |
| TFLite Size | ~4.7 MB (INT8) |
| Inference Latency | ~116 ms |
| Memory Usage | <500 MB |
| Input Shape | (3, 128, 1440) |
| Output Format | JSON |

## Decision States

| State | Probability Range | Action |
|-------|-------------------|--------|
| SAFE | [0.00, 0.30] | No action |
| MONITOR | [0.30, 0.50] | Log only |
| REVIEW | [0.50, 0.70] | Alert operator |
| ALERT | [0.70, 1.00] | Full alarm |

**Hysteresis:** 60-minute cooldown between state transitions to prevent alarm fatigue.
**Storm Gate:** Kp>4.0 or Dst<-30 → suppress to SAFE (geomagnetic storms cause false positives).
