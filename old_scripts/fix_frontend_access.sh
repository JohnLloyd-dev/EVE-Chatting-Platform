#!/bin/bash

# Fix Frontend Access Script
echo "🔧 Fixing Frontend Access Issues"
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

# Step 1: Check if frontend container is running
print_status "Step 1: Checking frontend container status..."
if docker ps | grep -q "frontend"; then
    print_success "Frontend container is running"
else
    print_error "Frontend container is not running"
    exit 1
fi

# Step 2: Check frontend logs
print_status "Step 2: Checking frontend logs..."
docker logs eve-chatting-platform_frontend_1 --tail 20

# Step 3: Check if port 3000 is accessible
print_status "Step 3: Checking port 3000 accessibility..."
if netstat -tlnp | grep -q ":3000"; then
    print_success "Port 3000 is listening"
else
    print_error "Port 3000 is not listening"
fi

# Step 4: Check firewall status
print_status "Step 4: Checking firewall status..."
if sudo ufw status | grep -q "Status: active"; then
    print_warning "Firewall is active - checking port 3000..."
    if sudo ufw status | grep -q "3000"; then
        print_success "Port 3000 is allowed in firewall"
    else
        print_warning "Port 3000 might be blocked by firewall"
        echo "To allow port 3000: sudo ufw allow 3000"
    fi
else
    print_warning "Firewall is not active"
fi

# Step 5: Test local access
print_status "Step 5: Testing local access..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200"; then
    print_success "Frontend is accessible locally"
else
    print_error "Frontend is not accessible locally"
fi

# Step 6: Check external access
print_status "Step 6: Checking external access..."
EXTERNAL_IP=$(curl -s ifconfig.me)
print_status "Your external IP is: $EXTERNAL_IP"

# Step 7: Restart frontend with proper configuration
print_status "Step 7: Restarting frontend with proper configuration..."

# Stop frontend
docker-compose stop frontend

# Remove frontend container
docker rm -f eve-chatting-platform_frontend_1

# Start frontend with proper port mapping
docker-compose up -d frontend

# Wait for frontend to start
sleep 10

# Step 8: Verify frontend is working
print_status "Step 8: Verifying frontend is working..."

# Check if frontend is running
if docker ps | grep -q "frontend"; then
    print_success "Frontend container is running"
else
    print_error "Frontend container failed to start"
    exit 1
fi

# Test local access
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200"; then
    print_success "Frontend is accessible locally"
else
    print_error "Frontend is not accessible locally"
fi

# Step 9: Provide access URLs
echo ""
echo "🌐 Frontend Access URLs:"
echo "   Local: http://localhost:3000"
echo "   External: http://$EXTERNAL_IP:3000"
echo "   VPS IP: http://204.12.223.76:3000"
echo ""

# Step 10: Check for common issues
print_status "Step 10: Checking for common issues..."

# Check if Next.js is running properly
if docker logs eve-chatting-platform_frontend_1 --tail 10 | grep -q "ready"; then
    print_success "Next.js is ready"
else
    print_warning "Next.js might not be fully ready yet"
fi

# Check for build errors
if docker logs eve-chatting-platform_frontend_1 --tail 20 | grep -q "error"; then
    print_warning "Found errors in frontend logs"
    docker logs eve-chatting-platform_frontend_1 --tail 10
fi

echo ""
print_success "Frontend access fix completed!"
echo ""
echo "🔧 If frontend is still not accessible:"
echo "   1. Check firewall: sudo ufw allow 3000"
echo "   2. Check VPS provider firewall settings"
echo "   3. Verify port 3000 is open in VPS control panel"
echo "   4. Try accessing from different network"
echo "" 