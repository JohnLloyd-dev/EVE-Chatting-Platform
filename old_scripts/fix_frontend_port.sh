#!/bin/bash

echo "🔧 Fixing Frontend Port Mapping"
echo "================================"

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

# Step 1: Stop frontend container
print_status "Step 1: Stopping frontend container..."
docker-compose stop frontend

# Step 2: Remove frontend container
print_status "Step 2: Removing frontend container..."
docker rm -f eve-chatting-platform_frontend_1

# Step 3: Start frontend with correct configuration
print_status "Step 3: Starting frontend with correct port mapping..."
docker-compose up -d frontend

# Step 4: Wait for container to start
print_status "Step 4: Waiting for container to start..."
sleep 15

# Step 5: Check container status
print_status "Step 5: Checking container status..."
docker ps | grep frontend

# Step 6: Check port mapping
print_status "Step 6: Checking port mapping..."
docker port eve-chatting-platform_frontend_1

# Step 7: Test connectivity
print_status "Step 7: Testing connectivity..."
sleep 10
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000

# Step 8: Show final status
print_status "Step 8: Final status..."
echo ""
echo "🌐 Frontend Access URLs:"
echo "   Local: http://localhost:3000"
echo "   External: http://204.12.223.76:3000"
echo ""
echo "📋 Container Status:"
docker ps | grep frontend
echo ""
echo "🔗 Port Mapping:"
docker port eve-chatting-platform_frontend_1
echo ""

print_success "Frontend port mapping fix completed!" 