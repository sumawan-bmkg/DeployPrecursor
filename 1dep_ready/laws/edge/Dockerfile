# ═══════════════════════════════════════════════════════════════════
# V8 SupCon-TFLite Edge — Dockerfile for NVIDIA Jetson Nano 4GB
# Base: nvcr.io/nvidia/l4t-base:r35.4.1
#
# Why L4T base:
#   - Native JetPack 5.1.x compatibility
#   - Pre-installed CUDA 11.4 + cuDNN 8.6 for ARM64
#   - TensorRT for optional optimization
#
# Size target: <800 MB (slim variant)
# ═══════════════════════════════════════════════════════════════════

# Use L4T base (minimal, no PyTorch since we run TFLite)
FROM nvcr.io/nvidia/l4t-base:r35.4.1

LABEL maintainer="BMKG LAWS Team"
LABEL description="V8 SupCon-TFLite Edge Inference — NVIDIA Jetson Nano 4GB"
LABEL version="1.0.0"

# ── Environment ──────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# ── System Dependencies ──────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-dev \
    libopenblas-dev \
    liblapack-dev \
    libatlas-base-dev \
    libgomp1 \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

# ── Set working directory ────────────────────────────────────
WORKDIR /app

# ── Copy dependency manifest ─────────────────────────────────
COPY requirements_edge.txt .

# ── Install Python Dependencies ──────────────────────────────
RUN pip3 install --no-cache-dir \
    --extra-index-url https://google-coral.github.io/py-repo/ \
    -r requirements_edge.txt

# ── Copy application code ────────────────────────────────────
COPY preprocessing_pipeline.py .
COPY edge_inference.py .
COPY config.yaml .
COPY models/ models/

# ── Create output & log directories ──────────────────────────
RUN mkdir -p output logs

# ── Default command: daemon mode ─────────────────────────────
CMD ["python3", "edge_inference.py", "--daemon", "--interval", "60", "--log-file", "logs/edge.log"]
