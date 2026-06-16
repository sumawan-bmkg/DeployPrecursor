#!/bin/bash
# ScalogramV3 V8 Inference Execution Script
# Target: Ubuntu 24.04 LTS
# Purpose: Run inference for 25 BMKG stations hourly
# Author: Deployment Team
# Date: 2026-06-10

set -e

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

print_info() {
    echo -e "${NC}ℹ️  $1${NC}"
}

# Configuration
DEPLOY_DIR="/opt/scalogramv3"
VENV_PATH="$DEPLOY_DIR/venv"
INFERENCE_SCRIPT="$DEPLOY_DIR/inference/inference.py"
CONFIG_FILE="$DEPLOY_DIR/config/config.yaml"
LOG_DIR="$DEPLOY_DIR/logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/inference_$TIMESTAMP.log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
error_handler() {
    print_error "Inference failed at line $1"
    log "ERROR: Inference failed at line $1"
    exit 1
}

trap 'error_handler $LINENO' ERR

# Main execution
main() {
    echo "=========================================="
    echo "ScalogramV3 V8 Inference Execution"
    echo "=========================================="
    log "Starting inference execution"
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_PATH" ]; then
        print_error "Virtual environment not found at $VENV_PATH"
        log "ERROR: Virtual environment not found"
        exit 1
    fi
    
    # Activate virtual environment
    print_info "Activating virtual environment..."
    source "$VENV_PATH/bin/activate"
    log "Virtual environment activated"
    
    # Check if inference script exists
    if [ ! -f "$INFERENCE_SCRIPT" ]; then
        print_error "Inference script not found at $INFERENCE_SCRIPT"
        log "ERROR: Inference script not found"
        exit 1
    fi
    
    # Check if checkpoint exists
    if [ ! -f "$DEPLOY_DIR/checkpoints/v3_v8_conv_fpr_best_weights.pth" ]; then
        print_error "Checkpoint not found"
        log "ERROR: Checkpoint not found"
        exit 1
    fi
    
    print_success "All prerequisites verified"
    
    # Load configuration if exists
    if [ -f "$CONFIG_FILE" ]; then
        print_info "Loading configuration from $CONFIG_FILE"
        # Parse config and set environment variables if needed
        export SCALOGRAM_CONFIG="$CONFIG_FILE"
        log "Configuration loaded"
    fi
    
    # Run inference based on mode
    print_info "Starting inference..."
    log "Starting inference process"
    
    # Check if HDF5 dataset is available
    if [ -f "$DEPLOY_DIR/runtime_assets/scalogram_v8_true_negatives.h5" ]; then
        print_info "Running HDF5 batch inference..."
        log "Mode: HDF5 batch inference"
        
        python "$INFERENCE_SCRIPT" \
            --h5_path "$DEPLOY_DIR/runtime_assets/scalogram_v8_true_negatives.h5" \
            --split val \
            --max_samples 200 \
            --ckpt "$DEPLOY_DIR/checkpoints/v3_v8_conv_fpr_best_weights.pth" \
            --device cpu \
            2>&1 | tee -a "$LOG_FILE"
        
        print_success "HDF5 batch inference completed"
        log "HDF5 batch inference completed"
        
    # Check if single tensor is available
    elif [ -f "$DEPLOY_DIR/runtime_assets/sample_tensor.npy" ]; then
        print_info "Running single tensor inference..."
        log "Mode: Single tensor inference"
        
        python "$INFERENCE_SCRIPT" \
            --tensor_npy "$DEPLOY_DIR/runtime_assets/sample_tensor.npy" \
            --kp 2.5 \
            --dst -10 \
            --threshold 0.30 \
            --ckpt "$DEPLOY_DIR/checkpoints/v3_v8_conv_fpr_best_weights.pth" \
            --device cpu \
            2>&1 | tee -a "$LOG_FILE"
        
        print_success "Single tensor inference completed"
        log "Single tensor inference completed"
        
    else
        print_warning "No dataset found. Running help command..."
        log "WARNING: No dataset found"
        
        python "$INFERENCE_SCRIPT" --help 2>&1 | tee -a "$LOG_FILE"
        
        print_info "Please provide dataset via --h5_path or --tensor_npy"
        log "INFO: No dataset provided"
    fi
    
    # Cleanup old logs (keep last 30 days)
    print_info "Cleaning up old logs..."
    find "$LOG_DIR" -name "inference_*.log" -mtime +30 -delete
    log "Old logs cleaned up"
    
    print_success "Inference execution completed successfully"
    log "Inference execution completed successfully"
    
    echo ""
    echo "=========================================="
    echo "Summary"
    echo "=========================================="
    echo "Log file: $LOG_FILE"
    echo "Deployment directory: $DEPLOY_DIR"
    echo ""
    echo "To view logs:"
    echo "  tail -f $LOG_FILE"
    echo ""
    echo "=========================================="
}

# Run main function
main

exit 0
