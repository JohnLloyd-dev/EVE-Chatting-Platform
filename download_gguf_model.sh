#!/bin/bash

# 🚀 Download GGUF Model for EVE Chat Platform
# =============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Model configuration
MODEL_NAME="openhermes-2.5-mistral-7b.Q5_K_M.gguf"
MODEL_URL="https://huggingface.co/TheBloke/OpenHermes-2.5-Mistral-7B-GGUF/resolve/main/${MODEL_NAME}"
CACHE_DIR="./backend/.cache/huggingface"
MODEL_PATH="${CACHE_DIR}/${MODEL_NAME}"

log "🚀 Downloading GGUF Model for EVE Chat Platform"
log "Model: ${MODEL_NAME}"
log "URL: ${MODEL_URL}"
log "Target: ${MODEL_PATH}"

# Check if model already exists
if [[ -f "${MODEL_PATH}" ]]; then
    success "✅ Model already exists: ${MODEL_PATH}"
    log "File size: $(du -h "${MODEL_PATH}" | cut -f1)"
    exit 0
fi

# Create cache directory
log "📁 Creating cache directory..."
mkdir -p "${CACHE_DIR}"
success "✅ Cache directory created: ${CACHE_DIR}"

# Check available disk space
AVAILABLE_SPACE=$(df . | awk 'NR==2 {print $4}')
REQUIRED_SPACE=6000000  # 6GB in KB
log "📊 Available disk space: $((${AVAILABLE_SPACE} / 1024 / 1024))GB"
log "📊 Required space: ~6GB"

if [[ ${AVAILABLE_SPACE} -lt ${REQUIRED_SPACE} ]]; then
    warning "⚠️ Low disk space. Available: $((${AVAILABLE_SPACE} / 1024 / 1024))GB, Required: ~6GB"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        error "❌ Download cancelled due to low disk space"
        exit 1
    fi
fi

# Download model
log "📥 Downloading model (this may take 10-30 minutes depending on your connection)..."
log "💡 Model size: ~6GB"

# Use wget with progress bar and resume capability
if command -v wget &> /dev/null; then
    wget --continue --progress=bar:force:noscroll "${MODEL_URL}" -O "${MODEL_PATH}"
elif command -v curl &> /dev/null; then
    curl -L --continue-at - "${MODEL_URL}" -o "${MODEL_PATH}"
else
    error "❌ Neither wget nor curl found. Please install one of them."
    exit 1
fi

# Verify download
if [[ -f "${MODEL_PATH}" ]]; then
    FILE_SIZE=$(du -h "${MODEL_PATH}" | cut -f1)
    success "✅ Model downloaded successfully!"
    log "📁 Location: ${MODEL_PATH}"
    log "📊 Size: ${FILE_SIZE}"
    
    # Verify file integrity (basic check)
    if [[ ${FILE_SIZE} == *"G"* ]] || [[ ${FILE_SIZE} == *"M"* ]]; then
        success "✅ File size looks correct"
    else
        warning "⚠️ File size seems small. Download may be incomplete."
    fi
    
    log ""
    log "🎉 Next steps:"
    log "1. Run: docker-compose -f docker-compose.gpu.yml up -d --build"
    log "2. Check logs: docker-compose -f docker-compose.gpu.yml logs -f backend"
    log "3. Test AI: curl http://localhost:8001/ai/health"
    
else
    error "❌ Download failed. Model file not found."
    exit 1
fi 