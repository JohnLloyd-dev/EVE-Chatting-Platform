#!/bin/bash

echo "🔧 EVE Chat Platform - Troubleshooting Script"
echo "============================================="

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

print_status "Starting troubleshooting for VPS: $VPS_IP"
echo ""

# Check Docker status
print_status "Checking Docker status..."
if docker info > /dev/null 2>&1; then
    print_success "Docker is running"
else
    print_error "Docker is not running"
    exit 1
fi

# Check if containers are running
print_status "Checking container status..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""

# Check service health
print_status "Testing service connectivity..."

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
    
    # Get AI model details
    AI_DETAILS=$(curl -s http://$VPS_IP:8001/ai/health 2>/dev/null)
    if [ -n "$AI_DETAILS" ]; then
        echo "   AI Model Details:"
        echo "$AI_DETAILS" | jq -r '.model_name, .device, .status' 2>/dev/null || \
        echo "$AI_DETAILS" | grep -E '"model_name"|"device"|"status"' 2>/dev/null || \
        echo "   (Raw response: $AI_DETAILS)"
    fi
else
    print_warning "AI Model Integration: FAILED (Status: $AI_STATUS)"
    print_status "Note: AI model is now integrated into backend, not a separate service"
fi

# Test frontend
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$VPS_IP:3000 2>/dev/null || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    print_success "Frontend: OK (http://$VPS_IP:3000)"
else
    print_warning "Frontend: FAILED (Status: $FRONTEND_STATUS)"
fi

echo ""

# Check environment variables
print_status "Checking frontend environment variables..."
if docker ps --format "{{.Names}}" | grep -q "frontend"; then
    FRONTEND_CONTAINER=$(docker ps --format "{{.Names}}" | grep "frontend" | head -1)
    print_status "Frontend container: $FRONTEND_CONTAINER"
    
    NEXT_PUBLIC_API_URL=$(docker exec "$FRONTEND_CONTAINER" env | grep NEXT_PUBLIC_API_URL | cut -d'=' -f2)
    if [ "$NEXT_PUBLIC_API_URL" = "http://$VPS_IP:8001" ]; then
        print_success "NEXT_PUBLIC_API_URL is correct: $NEXT_PUBLIC_API_URL"
    else
        print_error "NEXT_PUBLIC_API_URL is wrong: $NEXT_PUBLIC_API_URL (should be http://$VPS_IP:8001)"
    fi
else
    print_warning "Frontend container not found"
fi

echo ""

# Check logs
print_status "Recent logs from services..."
echo "Backend logs (last 5 lines):"
docker-compose logs backend --tail 5 2>/dev/null || echo "No backend logs found"

echo ""
echo "Frontend logs (last 5 lines):"
docker-compose logs frontend --tail 5 2>/dev/null || echo "No frontend logs found"

echo ""
print_status "Troubleshooting complete!"
print_status "Access URLs:"
echo "  Frontend: http://$VPS_IP:3000"
echo "  Backend API: http://$VPS_IP:8001"
echo "  AI Model Health: http://$VPS_IP:8001/ai/health"

echo ""
print_status "AI Integration Troubleshooting Tips:"
echo "  1. If AI model fails to load, check backend logs: docker-compose logs backend"
echo "  2. Verify GPU availability: nvidia-smi"
echo "  3. Check AI model cache: docker exec backend ls -la /app/.cache/huggingface"
echo "  4. Test AI endpoints: ./test_ai_integration.sh"
echo "  5. Restart backend if needed: docker-compose restart backend" 