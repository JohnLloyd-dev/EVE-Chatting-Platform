#!/bin/bash

echo "🚀 EVE Chat Platform - GPU Deployment"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if NVIDIA Docker runtime is available
print_status "Checking NVIDIA Docker runtime..."
if docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi >/dev/null 2>&1; then
    print_success "NVIDIA Docker runtime is working"
    USE_GPU=true
else
    print_error "NVIDIA Docker runtime not available, falling back to CPU"
    USE_GPU=false
fi

if [ "$USE_GPU" = true ]; then
    print_status "Using GPU-enabled Docker Compose configuration..."
    
    # Stop existing containers
    print_status "Stopping existing containers..."
    docker-compose down
    
    # Build GPU version
    print_status "Building GPU version of AI server..."
    docker-compose -f docker-compose.gpu.yml build --no-cache ai-server
    
    if [ $? -ne 0 ]; then
        print_error "GPU build failed, falling back to CPU version"
        ./deploy.sh
        exit 1
    fi
    
    # Run with GPU support
    print_status "Starting services with GPU support..."
    docker-compose -f docker-compose.gpu.yml up -d
    
    print_success "GPU deployment completed!"
    print_status "Monitor AI server logs: docker-compose -f docker-compose.gpu.yml logs ai-server"
    
else
    print_status "Running standard CPU deployment..."
    ./deploy.sh
fi

print_status "Access URLs:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8001"
echo "  AI Server: http://localhost:8000"