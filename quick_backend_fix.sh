#!/bin/bash

echo "🔧 Quick Backend Fix"
echo "==================="

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

# Step 1: Check backend container status
print_status "Step 1: Checking backend container status..."
docker ps -a | grep backend

# Step 2: Check backend logs for errors
print_status "Step 2: Checking backend logs..."
docker logs eve-chatting-platform_backend_1 --tail 30

# Step 3: Check if backend is actually running
print_status "Step 3: Checking if backend process is running..."
docker exec eve-chatting-platform_backend_1 ps aux | grep uvicorn

# Step 4: Check if backend is listening on port 8000 inside container
print_status "Step 4: Checking if backend is listening inside container..."
docker exec eve-chatting-platform_backend_1 netstat -tlnp | grep 8000

# Step 5: Check port mapping
print_status "Step 5: Checking port mapping..."
docker port eve-chatting-platform_backend_1

# Step 6: Test internal backend access
print_status "Step 6: Testing internal backend access..."
docker exec eve-chatting-platform_backend_1 curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health
echo " - Internal health check"

# Step 7: Check environment variables
print_status "Step 7: Checking environment variables..."
docker exec eve-chatting-platform_backend_1 env | grep -E "(DATABASE_URL|REDIS_URL|SECRET_KEY)" | head -5

# Step 8: If backend is not running, restart it
print_status "Step 8: Restarting backend if needed..."
if ! docker exec eve-chatting-platform_backend_1 ps aux | grep -q uvicorn; then
    print_warning "Backend not running, restarting..."
    docker-compose restart backend
    sleep 10
else
    print_success "Backend is running"
fi

# Step 9: Test again after restart
print_status "Step 9: Testing after restart..."
sleep 5
curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health
echo " - Local health check"

# Step 10: Show final status
print_status "Step 10: Final status..."
echo ""
echo "📋 Container Status:"
docker ps | grep backend
echo ""
echo "🔗 Port Mapping:"
docker port eve-chatting-platform_backend_1
echo ""
echo "🌐 Access URLs:"
echo "   Local: http://localhost:8001"
echo "   External: http://204.12.223.76:8001"
echo ""

print_success "Quick backend fix completed!" 