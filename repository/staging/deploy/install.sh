#!/bin/bash
# ScalogramV3 V8 Production Installation Script
# Target: Ubuntu 24.04 LTS
# Author: Deployment Team
# Date: 2026-06-10

set -e

echo "=========================================="
echo "ScalogramV3 V8 Production Installation"
echo "=========================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root. Creating dedicated user..."
    useradd -r -s /bin/bash scalogramv3 2>/dev/null || true
    print_success "User scalogramv3 created (or already exists)"
fi

# Step 1: System Update
echo ""
echo "Step 1: Updating system packages..."
sudo apt update
sudo apt upgrade -y
print_success "System updated"

# Step 2: Install system dependencies
echo ""
echo "Step 2: Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    build-essential \
    htop \
    tmux
print_success "System dependencies installed"

# Step 3: Verify Python version
echo ""
echo "Step 3: Verifying Python version..."
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
print_success "Python version: $PYTHON_VERSION"

# Check if Python version is >= 3.8
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    print_error "Python version must be >= 3.8. Current: $PYTHON_VERSION"
    exit 1
fi

print_success "Python version compatible (>= 3.8)"

# Step 4: Create deployment directory
echo ""
echo "Step 4: Creating deployment directory..."
DEPLOY_DIR="/opt/scalogramv3"
sudo mkdir -p $DEPLOY_DIR
sudo chown $USER:$USER $DEPLOY_DIR
cd $DEPLOY_DIR
print_success "Deployment directory created: $DEPLOY_DIR"

# Step 5: Create virtual environment
echo ""
echo "Step 5: Creating Python virtual environment..."
python3 -m venv venv
print_success "Virtual environment created"

# Step 6: Activate virtual environment
echo ""
echo "Step 6: Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Step 7: Upgrade pip
echo ""
echo "Step 7: Upgrading pip..."
pip install --upgrade pip
print_success "pip upgraded"

# Step 8: Install Python dependencies
echo ""
echo "Step 8: Installing Python dependencies..."
if [ -f "requirements_exact.txt" ]; then
    pip install torch==2.0.1 torchvision==0.15.2 --index-url https://download.pytorch.org/whl/cpu
    pip install numpy==1.24.3 pandas==2.0.3 h5py==3.9.0
    print_success "Python dependencies installed"
else
    print_error "requirements_exact.txt not found"
    exit 1
fi

# Step 9: Verify installation
echo ""
echo "Step 9: Verifying installation..."
python -c "import torch; print('PyTorch:', torch.__version__)"
python -c "import torchvision; print('TorchVision:', torchvision.__version__)"
python -c "import numpy; print('NumPy:', numpy.__version__)"
python -c "import pandas; print('Pandas:', pandas.__version__)"
python -c "import h5py; print('h5py:', h5py.__version__)"
print_success "All dependencies verified"

# Step 10: Create directory structure
echo ""
echo "Step 10: Creating directory structure..."
mkdir -p checkpoints
mkdir -p models
mkdir -p preprocessing
mkdir -p inference
mkdir -p runtime_assets
mkdir -p config
mkdir -p logs
mkdir -p scripts
print_success "Directory structure created"

# Step 11: Set permissions
echo ""
echo "Step 11: Setting permissions..."
chmod 755 scripts/*.sh 2>/dev/null || true
chmod 644 config/*.yaml 2>/dev/null || true
chmod 644 models/*.py 2>/dev/null || true
chmod 644 inference/*.py 2>/dev/null || true
chmod 600 checkpoints/*.pth 2>/dev/null || true
print_success "Permissions set"

# Step 12: Test model loading (if checkpoint exists)
echo ""
echo "Step 12: Testing model loading..."
if [ -f "checkpoints/v3_v8_conv_fpr_best_weights.pth" ]; then
    python -c "
import sys
sys.path.insert(0, 'models')
from V3_Model_v8 import MultiTaskScalogramV3_v8
from SpatialGNNModule import SpatialGNNModule
import torch

model = MultiTaskScalogramV3_v8(pretrained=False)
ckpt = torch.load('checkpoints/v3_v8_conv_fpr_best_weights.pth', map_location='cpu')
model.load_state_dict(ckpt, strict=False)
model.eval()
print('Model loaded successfully')
"
    print_success "Model loading test passed"
else
    print_warning "Checkpoint not found. Skipping model loading test."
fi

# Step 13: Test inference script (if exists)
echo ""
echo "Step 13: Testing inference script..."
if [ -f "inference/inference.py" ]; then
    python inference/inference.py --help > /dev/null 2>&1
    print_success "Inference script test passed"
else
    print_warning "inference.py not found. Skipping inference test."
fi

# Step 14: Create log directory
echo ""
echo "Step 14: Creating log directory..."
mkdir -p logs
print_success "Log directory created"

# Step 15: Generate installation summary
echo ""
echo "Step 15: Generating installation summary..."
cat > logs/installation_summary.txt << EOF
ScalogramV3 V8 Installation Summary
====================================
Date: $(date)
Python Version: $PYTHON_VERSION
Deployment Directory: $DEPLOY_DIR
Virtual Environment: venv
Dependencies: torch, torchvision, numpy, pandas, h5py
Status: SUCCESS
EOF
print_success "Installation summary generated"

# Final message
echo ""
echo "=========================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "=========================================="
echo ""
echo "Deployment Directory: $DEPLOY_DIR"
echo "Virtual Environment: $DEPLOY_DIR/venv"
echo "Log Directory: $DEPLOY_DIR/logs"
echo ""
echo "To activate the environment:"
echo "  source $DEPLOY_DIR/venv/bin/activate"
echo ""
echo "To run inference:"
echo "  python inference/inference.py --help"
echo ""
echo "To verify installation:"
echo "  bash scripts/verify_installation.sh"
echo ""
echo "=========================================="

# Exit successfully
exit 0
