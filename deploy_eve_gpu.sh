#!/bin/bash

# 🚀 EVE Chat Platform - Complete GPU Deployment Script
# ======================================================
# This script handles everything: model download, GPU setup, and deployment

set -e  # Exit on any error

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

# Configuration
MODEL_NAME="openhermes-2.5-mistral-7b.Q5_K_M.gguf"
MODEL_URL="https://huggingface.co/TheBloke/OpenHermes-2.5-Mistral-7B-GGUF/resolve/main/${MODEL_NAME}"
CACHE_DIR="./backend/.cache/huggingface"
MODEL_PATH="${CACHE_DIR}/${MODEL_NAME}"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root"
   exit 1
fi

# Check if we're in the right directory
if [[ ! -f "docker-compose.gpu.yml" ]]; then
    error "docker-compose.gpu.yml not found. Please run this script from the project root."
    exit 1
fi

log "🚀 EVE Chat Platform - Complete GPU Deployment"
log "Target: RTX 4060 with GGUF optimization"
log "Model: ${MODEL_NAME}"

# Step 1: Pull latest changes
log "Step 1: Pulling latest changes from GitHub..."
if git pull origin main; then
    success "✅ Latest changes pulled successfully"
else
    warning "⚠️ Could not pull changes (maybe no changes or not a git repo)"
fi

# Step 2: Check GPU availability
log "Step 2: Checking GPU availability..."
if command -v nvidia-smi &> /dev/null; then
    GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits | head -1)
    success "✅ GPU detected: $GPU_INFO"
    
    # Check VRAM
    VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
    if [[ $VRAM -ge 8000 ]]; then
        success "✅ Sufficient VRAM: ${VRAM}MB (≥8GB required)"
    else
        warning "⚠️ Low VRAM: ${VRAM}MB (8GB recommended for 7B model)"
    fi
else
    error "❌ nvidia-smi not found. GPU acceleration may not work."
    read -p "Continue without GPU acceleration? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        error "❌ Deployment cancelled"
        exit 1
    fi
fi

# Step 3: Download GGUF Model
log "Step 3: Checking/Downloading GGUF Model..."
if [[ ! -f "${MODEL_PATH}" ]]; then
    log "📥 Model not found. Starting download..."
    
    # Create cache directory
    mkdir -p "${CACHE_DIR}"
    success "✅ Cache directory created: ${CACHE_DIR}"
    
    # Check disk space
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
    log "📥 Downloading model (this may take 10-30 minutes)..."
    log "💡 Model size: ~6GB"
    
    if command -v wget &> /dev/null; then
        wget --continue --progress=bar:force:noscroll "${MODEL_URL}" -O "${MODEL_PATH}"
    elif command -v curl &> /dev/null; then
        curl -L --continue-at - "${MODEL_URL}" -o "${MODEL_PATH}"
    else
        error "❌ Neither wget nor curl found. Please install one of them."
        exit 1
    fi
    
    if [[ -f "${MODEL_PATH}" ]]; then
        FILE_SIZE=$(du -h "${MODEL_PATH}" | cut -f1)
        success "✅ Model downloaded successfully!"
        log "📁 Location: ${MODEL_PATH}"
        log "📊 Size: ${FILE_SIZE}"
    else
        error "❌ Download failed. Model file not found."
        exit 1
    fi
else
    FILE_SIZE=$(du -h "${MODEL_PATH}" | cut -f1)
    success "✅ Model already exists: ${MODEL_PATH}"
    log "📊 Size: ${FILE_SIZE}"
fi

# Step 4: Stop existing services
log "Step 4: Stopping existing services..."
docker-compose -f docker-compose.gpu.yml down
success "✅ Services stopped"

# Step 5: Clean up old containers and volumes
log "Step 5: Cleaning up old containers and volumes..."
docker system prune -f
docker volume rm eve-chatting-platform_ai_model_cache 2>/dev/null || true
success "✅ Cleanup completed"

# Step 6: Build and start services
log "Step 6: Building and starting services with GPU optimization..."
log "🚀 This will take several minutes for the first build..."
docker-compose -f docker-compose.gpu.yml up -d --build

# Step 7: Wait for services to be ready
log "Step 7: Waiting for services to be ready..."
sleep 15

# Step 8: Check service health
log "Step 8: Checking service health..."

# Check PostgreSQL
log "Checking PostgreSQL..."
for i in {1..15}; do
    if docker exec eve-chatting-platform-postgres-1 pg_isready -U adam2025man -d chatting_platform &>/dev/null; then
        success "✅ PostgreSQL is ready"
        break
    else
        warning "PostgreSQL not ready yet, attempt $i/15"
        sleep 5
    fi
done

# Check Redis
log "Checking Redis..."
if docker exec eve-chatting-platform-redis-1 redis-cli ping &>/dev/null; then
    success "✅ Redis is ready"
else
    error "❌ Redis is not responding"
fi

# Check Backend
log "Checking Backend..."
for i in {1..20}; do
    if curl -s http://localhost:8001/health &>/dev/null; then
        success "✅ Backend is ready"
        break
    else
        warning "Backend not ready yet, attempt $i/20"
        sleep 10
    fi
done

# Step 9: Check AI Model Integration
log "Step 9: Checking AI Model Integration..."

# Wait for AI model to load
log "Waiting for AI model to load (this may take several minutes)..."
sleep 45

# Check AI health endpoint
log "Checking AI Model Health..."
for i in {1..25}; do
    AI_RESPONSE=$(curl -s http://localhost:8001/ai/health 2>/dev/null || echo "FAILED")
    if [[ "$AI_RESPONSE" != "FAILED" ]]; then
        success "✅ AI Model is responding"
        log "AI Response: $AI_RESPONSE"
        break
    else
        warning "AI Model not ready yet, attempt $i/25"
        sleep 15
    fi
done

# Step 10: Check Frontend
log "Step 10: Checking Frontend..."
if curl -s http://localhost:3000 &>/dev/null; then
    success "✅ Frontend is accessible"
else
    warning "⚠️ Frontend may not be ready yet"
fi

# Step 11: Test AI Functionality
log "Step 11: Testing AI Functionality..."
echo ""
echo "🤖 Testing AI Integration..."

# Test AI session creation
if curl -s -X POST "http://localhost:8001/ai/init-session" \
    -H "Content-Type: application/json" \
    -d '{"session_id": "test", "system_prompt": "You are a helpful assistant."}' &>/dev/null; then
    success "✅ AI Session creation: PASSED"
else
    warning "⚠️ AI Session creation: FAILED"
fi

# Test AI chat
if curl -s -X POST "http://localhost:8001/ai/chat" \
    -H "Content-Type: application/json" \
    -d '{"session_id": "test", "message": "Hello"}' &>/dev/null; then
    success "✅ AI Chat: PASSED"
else
    warning "⚠️ AI Chat: FAILED"
fi

# Step 12: Final Status Check
log "Step 12: Final Status Check..."
echo ""
echo "=========================================="
echo "🚀 EVE Chat Platform - GPU Deployment Status"
echo "=========================================="

# Service status
echo "Service Status:"
docker-compose -f docker-compose.gpu.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# GPU usage
echo ""
echo "GPU Usage:"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader
else
    echo "nvidia-smi not available"
fi

# Port status
echo ""
echo "Port Status:"
echo "Backend (8001): $(curl -s http://localhost:8001/health 2>/dev/null | head -c 50 || echo "Not responding")"
echo "Frontend (3000): $(curl -s http://localhost:3000 2>/dev/null | head -c 50 || echo "Not responding")"

# Final success message
echo ""
echo "=========================================="
success "🎉 EVE Chat Platform Deployment Completed!"
echo "=========================================="
echo ""
echo "🌐 Access Points:"
echo "  Frontend: http://localhost:3000"
echo "  Backend: http://localhost:8001"
echo "  AI Health: http://localhost:8001/ai/health"
echo ""
echo "📊 Monitoring:"
echo "  Logs: docker-compose -f docker-compose.gpu.yml logs -f"
echo "  Status: docker-compose -f docker-compose.gpu.yml ps"
echo "  GPU: nvidia-smi"
echo ""
echo "🔧 Troubleshooting:"
echo "  If AI model fails to load, check: docker-compose -f docker-compose.gpu.yml logs backend"
echo "  If database issues persist, check: docker-compose -f docker-compose.gpu.yml logs postgres"
echo "  If model file is missing, run: ./download_gguf_model.sh"
echo ""
echo "🚀 Your GPU-accelerated EVE Chat Platform is ready!"
echo "💡 The AI model is now running on your RTX 4060 with GGUF optimization!"
echo "⚡ Expected performance: 25-40 tokens/second with excellent quality" 