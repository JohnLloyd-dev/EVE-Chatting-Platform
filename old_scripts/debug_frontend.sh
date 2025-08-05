#!/bin/bash

# Debug Frontend Access Script
echo "🔍 Debugging Frontend Access Issues"
echo "==================================="

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

# Step 1: Check container status
print_status "Step 1: Checking container status..."
docker ps | grep frontend

# Step 2: Check container logs
print_status "Step 2: Checking container logs..."
docker logs eve-chatting-platform_frontend_1 --tail 20

# Step 3: Check container network
print_status "Step 3: Checking container network..."
docker inspect eve-chatting-platform_frontend_1 | grep -A 10 "NetworkSettings"

# Step 4: Check port mapping
print_status "Step 4: Checking port mapping..."
docker port eve-chatting-platform_frontend_1

# Step 5: Check if Next.js is listening inside container
print_status "Step 5: Checking if Next.js is listening inside container..."
docker exec eve-chatting-platform_frontend_1 netstat -tlnp | grep 3000

# Step 6: Check if port is accessible from host
print_status "Step 6: Checking if port is accessible from host..."
netstat -tlnp | grep 3000

# Step 7: Test connection from inside container
print_status "Step 7: Testing connection from inside container..."
docker exec eve-chatting-platform_frontend_1 curl -s -o /dev/null -w "%{http_code}" http://localhost:3000

# Step 8: Test connection from host to container
print_status "Step 8: Testing connection from host to container..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000

# Step 9: Check Docker network
print_status "Step 9: Checking Docker network..."
docker network ls
docker network inspect eve-chatting-platform_internal_network

# Step 10: Check firewall status
print_status "Step 10: Checking firewall status..."
sudo ufw status

# Step 11: Test with different methods
print_status "Step 11: Testing with different methods..."

echo "Testing with curl (verbose):"
curl -v http://localhost:3000 2>&1 | head -20

echo "Testing with wget:"
wget -qO- http://localhost:3000 2>&1 | head -10

echo "Testing with telnet:"
timeout 5 telnet localhost 3000 2>&1 | head -5

# Step 12: Check if it's a timing issue
print_status "Step 12: Checking if it's a timing issue..."
echo "Waiting 10 seconds and testing again..."
sleep 10
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000

# Step 13: Check container health
print_status "Step 13: Checking container health..."
docker exec eve-chatting-platform_frontend_1 ps aux | grep node

# Step 14: Check environment variables
print_status "Step 14: Checking environment variables..."
docker exec eve-chatting-platform_frontend_1 env | grep -E "(HOSTNAME|PORT|NEXT)"

echo ""
print_status "Debug information collected!"
echo ""
echo "🔧 Possible solutions:"
echo "   1. If container is not listening: Restart the container"
echo "   2. If port mapping is wrong: Check docker-compose.yml"
echo "   3. If firewall is blocking: sudo ufw allow 3000"
echo "   4. If network issue: Recreate the network"
echo "   5. If timing issue: Wait longer for Next.js to start"
echo "" 