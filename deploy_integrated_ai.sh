#!/bin/bash

echo "🚀 EVE Chat Platform - Integrated AI Backend Deployment"
echo "======================================================="

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
COMPOSE_FILE="docker-compose.yml"

echo ""
print_status "🚀 Starting Integrated AI Backend Deployment"
print_status "AI model is now integrated into the backend service"
print_status "No separate AI server needed"
echo ""

# Step 1: Stop existing services
print_status "Step 1: Stopping existing services..."
docker-compose -f $COMPOSE_FILE down

# Step 2: Build backend with AI dependencies
print_status "Step 2: Building backend with integrated AI model..."
docker-compose -f $COMPOSE_FILE build --no-cache backend

if [ $? -ne 0 ]; then
    print_error "Backend build failed"
    exit 1
fi

# Step 3: Start services
print_status "Step 3: Starting services with integrated AI..."
docker-compose -f $COMPOSE_FILE up -d

# Step 4: Wait for services to be ready
print_status "Step 4: Waiting for services to be ready..."
sleep 30

# Step 5: Check service health
print_status "Step 5: Checking service health..."

# Check backend health
for i in {1..10}; do
    BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$VPS_IP:8001/health 2>/dev/null || echo "000")
    if [ "$BACKEND_STATUS" = "200" ]; then
        print_success "Backend is healthy"
        break
    else
        print_warning "Backend not ready yet, attempt $i/10 (Status: $BACKEND_STATUS)"
        if [ $i -eq 5 ]; then
            print_status "Showing backend logs..."
            docker-compose -f $COMPOSE_FILE logs backend --tail 10
        fi
        sleep 15
    fi
done

# Check AI model integration
print_status "Step 6: Checking AI model integration..."
for i in {1..15}; do
    AI_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$VPS_IP:8001/ai/health 2>/dev/null || echo "000")
    if [ "$AI_STATUS" = "200" ]; then
        print_success "AI model is loaded and ready"
        
        # Show AI model details
        AI_DETAILS=$(curl -s http://$VPS_IP:8001/ai/health 2>/dev/null)
        if [ -n "$AI_DETAILS" ]; then
            echo "   AI Model Details:"
            echo "$AI_DETAILS" | jq -r '.model_name, .device, .status' 2>/dev/null || \
            echo "$AI_DETAILS" | grep -E '"model_name"|"device"|"status"' 2>/dev/null || \
            echo "   (Raw response: $AI_DETAILS)"
        fi
        break
    else
        print_warning "AI model not ready yet, attempt $i/15 (Status: $AI_STATUS)"
        if [ $i -eq 8 ]; then
            print_status "Showing backend logs for AI model loading..."
            docker-compose -f $COMPOSE_FILE logs backend --tail 15 | grep -E "(AI|Model|GPU|Loading)" || \
            docker-compose -f $COMPOSE_FILE logs backend --tail 15
        fi
        sleep 20
    fi
done

# Step 7: Final health check
echo ""
print_status "Step 7: Final health check..."

# Test all services
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$VPS_IP:8001/health 2>/dev/null || echo "000")
AI_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$VPS_IP:8001/ai/health 2>/dev/null || echo "000")
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$VPS_IP:3000 2>/dev/null || echo "000")

echo ""
print_status "Service Status Summary:"
echo "  Backend: $([ "$BACKEND_STATUS" = "200" ] && echo "✅ OK" || echo "❌ FAILED")"
echo "  AI Model: $([ "$AI_STATUS" = "200" ] && echo "✅ OK" || echo "❌ FAILED")"
echo "  Frontend: $([ "$FRONTEND_STATUS" = "200" ] && echo "✅ OK" || echo "❌ FAILED")"

# Step 8: Run integration test
echo ""
print_status "Step 8: Running AI integration test..."
if [ -f "./test_ai_integration.sh" ]; then
    ./test_ai_integration.sh
else
    print_warning "AI integration test script not found, skipping..."
fi

# Final summary
echo ""
if [ "$BACKEND_STATUS" = "200" ] && [ "$AI_STATUS" = "200" ] && [ "$FRONTEND_STATUS" = "200" ]; then
    print_success "🎉 Integrated AI Backend deployment completed successfully!"
    echo ""
    print_status "Access URLs:"
    echo "  Frontend: http://$VPS_IP:3000"
    echo "  Backend API: http://$VPS_IP:8001"
    echo "  AI Model Health: http://$VPS_IP:8001/ai/health"
    echo ""
    print_status "Next steps:"
    echo "  1. Test the chat interface in the frontend"
    echo "  2. Check the admin dashboard for AI status"
    echo "  3. Monitor backend logs for AI model performance"
    echo ""
    print_status "For troubleshooting, run: ./troubleshoot.sh"
else
    print_warning "⚠️ Some services are not healthy"
    print_status "Check the logs above and run: ./troubleshoot.sh"
    exit 1
fi 