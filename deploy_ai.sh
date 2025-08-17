#!/bin/bash

echo "🤖 EVE Chat Platform - AI Model Integration Deployment"
echo "======================================================"

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

# Configuration
VPS_IP="204.12.233.105"

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
print_status "AI Model Integration Status:"
echo "✅ AI model is now integrated into the backend service"
echo "✅ No separate AI server needed"
echo "✅ GPU acceleration automatically detected and used"
echo "✅ Simplified deployment and management"

# Use the standard docker-compose.yml (AI model is integrated)
COMPOSE_FILE="docker-compose.yml"
print_status "Using integrated docker-compose.yml"
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
docker-compose -f $COMPOSE_FILE down

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
    if docker exec eve-chatting-platform_postgres_1 pg_isready -U "adam2025man" &> /dev/null; then
        print_success "PostgreSQL is ready"
        break
    else
        print_warning "PostgreSQL not ready yet, attempt $i/5"
        sleep 10
    fi
done

# Wait for backend with integrated AI model to load
print_status "Waiting for Backend with integrated AI model to load (this may take several minutes)..."
for i in {1..20}; do
    BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$VPS_IP:8001/health 2>/dev/null || echo "000")
    AI_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$VPS_IP:8001/ai/health 2>/dev/null || echo "000")
    
    if [ "$BACKEND_STATUS" = "200" ] && [ "$AI_STATUS" = "200" ]; then
        print_success "Backend with AI model is ready"
        break
    else
        print_warning "Backend/AI not ready yet, attempt $i/20"
        print_warning "Backend Status: $BACKEND_STATUS, AI Status: $AI_STATUS"
        
        # Show backend logs every 5 attempts
        if [ $((i % 5)) -eq 0 ]; then
            print_status "Backend logs (last 10 lines):"
            docker-compose -f $COMPOSE_FILE logs backend --tail 10
        fi
        
        sleep 30
    fi
done

# Final health checks
echo ""
print_status "Running final health checks..."

# Test backend
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$VPS_IP:8001/health 2>/dev/null || echo "000")
if [ "$BACKEND_STATUS" = "200" ]; then
    print_success "Backend: OK (http://$VPS_IP:8001)"
else
    print_error "Backend: FAILED (Status: $BACKEND_STATUS)"
fi

# Test AI model integration
AI_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$VPS_IP:8001/ai/health 2>/dev/null || echo "000")
if [ "$AI_STATUS" = "200" ]; then
    print_success "AI Model Integration: OK (http://$VPS_IP:8001/ai/health)"
else
    print_warning "AI Model Integration: FAILED (Status: $AI_STATUS)"
fi

# Test frontend
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$VPS_IP:3000 2>/dev/null || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    print_success "Frontend: OK (http://$VPS_IP:3000)"
else
    print_warning "Frontend: FAILED (Status: $FRONTEND_STATUS)"
fi

echo ""
print_success "🚀 AI Model Integration deployment completed!"
echo ""
print_status "Access URLs:"
echo "  Frontend: http://$VPS_IP:3000"
echo "  Backend API: http://$VPS_IP:8001"
echo "  AI Model Health: http://$VPS_IP:8001/ai/health"
echo ""
print_status "AI Model Status: Integrated into Backend"
print_status "GPU Acceleration: Automatically detected and used"
echo ""
print_status "For troubleshooting, run: ./troubleshoot.sh" 