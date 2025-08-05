#!/bin/bash

echo "🤖 EVE Chat Platform - AI Server Deployment"
echo "==========================================="

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

# Check if NVIDIA GPU is available
check_gpu() {
    if command -v nvidia-smi &> /dev/null; then
        nvidia-smi &> /dev/null
        if [ $? -eq 0 ]; then
            return 0
        fi
    fi
    return 1
}

# Check if NVIDIA Docker runtime is available
check_nvidia_docker() {
    if docker info 2>/dev/null | grep -q "nvidia"; then
        return 0
    fi
    return 1
}

print_status "Checking system capabilities..."

# Check GPU availability
if check_gpu; then
    print_success "NVIDIA GPU detected"
    GPU_AVAILABLE=true
else
    print_warning "No NVIDIA GPU detected"
    GPU_AVAILABLE=false
fi

# Check NVIDIA Docker runtime
if check_nvidia_docker; then
    print_success "NVIDIA Docker runtime available"
    NVIDIA_DOCKER_AVAILABLE=true
else
    print_warning "NVIDIA Docker runtime not available"
    NVIDIA_DOCKER_AVAILABLE=false
fi

echo ""
print_status "Deployment Options:"
echo "1. CPU-only deployment (slower but works everywhere)"
echo "2. GPU deployment (faster, requires NVIDIA GPU + Docker runtime)"

if [ "$GPU_AVAILABLE" = true ] && [ "$NVIDIA_DOCKER_AVAILABLE" = true ]; then
    echo ""
    print_status "Your system supports GPU acceleration!"
    echo "Recommended: Option 2 (GPU deployment)"
    echo ""
    read -p "Choose deployment type (1=CPU, 2=GPU): " choice
else
    print_warning "GPU acceleration not available, using CPU-only deployment"
    choice=1
fi

case $choice in
    1)
        print_status "Deploying with CPU-only AI server..."
        COMPOSE_FILE="docker-compose.yml"
        ;;
    2)
        if [ "$GPU_AVAILABLE" = true ] && [ "$NVIDIA_DOCKER_AVAILABLE" = true ]; then
            print_status "Deploying with GPU-accelerated AI server..."
            COMPOSE_FILE="docker-compose.gpu.yml"
        else
            print_error "GPU deployment requested but not available"
            print_status "Falling back to CPU-only deployment..."
            COMPOSE_FILE="docker-compose.yml"
        fi
        ;;
    *)
        print_error "Invalid choice, using CPU-only deployment"
        COMPOSE_FILE="docker-compose.yml"
        ;;
esac

echo ""
print_status "Using compose file: $COMPOSE_FILE"

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose down

# Build and start services
print_status "Building and starting services..."
docker-compose -f $COMPOSE_FILE build --no-cache

if [ $? -ne 0 ]; then
    print_error "Build failed"
    exit 1
fi

# Start services
print_status "Starting services..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."

# Wait for PostgreSQL
sleep 20
for i in {1..5}; do
    if docker exec eve-chatting-platform_postgres_1 pg_isready -U "adam@2025@man" &> /dev/null; then
        print_success "PostgreSQL is ready"
        break
    else
        print_warning "PostgreSQL not ready yet, attempt $i/5"
        sleep 10
    fi
done

# Wait for AI server (takes longer to load model)
print_status "Waiting for AI Server to load model (this may take several minutes)..."
for i in {1..30}; do
    AI_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
    if [ "$AI_STATUS" = "200" ]; then
        print_success "AI Server is ready"
        break
    else
        print_warning "AI Server not ready yet, attempt $i/30 (Status: $AI_STATUS)"
        sleep 30
    fi
done

# Final health checks
echo ""
print_status "Running final health checks..."

# Test backend
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health 2>/dev/null || echo "000")
if [ "$BACKEND_STATUS" = "200" ]; then
    print_success "Backend: OK (http://localhost:8001)"
else
    print_error "Backend: FAILED (Status: $BACKEND_STATUS)"
fi

# Test AI server
AI_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
if [ "$AI_STATUS" = "200" ]; then
    print_success "AI Server: OK (http://localhost:8000)"
else
    print_warning "AI Server: FAILED (Status: $AI_STATUS)"
fi

# Test frontend
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    print_success "Frontend: OK (http://localhost:3000)"
else
    print_warning "Frontend: FAILED (Status: $FRONTEND_STATUS)"
fi

echo ""
print_success "🚀 AI Server deployment completed!"
echo ""
print_status "Access URLs:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8001"
echo "  AI Server: http://localhost:8000"
echo ""
print_status "AI Server Type: $([ "$choice" = "2" ] && echo "GPU-accelerated" || echo "CPU-only")"
echo ""
print_status "For troubleshooting, run: ./troubleshoot.sh" 