#!/bin/bash

echo "🔧 Fixing Backend Access Issues"
echo "==============================="

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

# Step 1: Pull latest changes
print_status "Step 1: Pulling latest changes..."
git pull origin main

# Step 2: Rebuild backend with latest CORS changes
print_status "Step 2: Rebuilding backend..."
docker-compose build backend

# Step 3: Restart backend
print_status "Step 3: Restarting backend..."
docker-compose restart backend

# Step 4: Wait for backend to be ready
print_status "Step 4: Waiting for backend to be ready..."
sleep 15

# Step 5: Test backend health
print_status "Step 5: Testing backend health..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health
echo " - Local health check"

# Step 6: Test external access
print_status "Step 6: Testing external access..."
curl -s -o /dev/null -w "%{http_code}" http://204.12.223.76:8001/health
echo " - External health check"

# Step 7: Test admin login endpoint
print_status "Step 7: Testing admin login endpoint..."
curl -X POST http://localhost:8001/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  -w "\nHTTP Status: %{http_code}\n"

# Step 8: Test CORS preflight
print_status "Step 8: Testing CORS preflight..."
curl -H "Origin: http://204.12.223.76:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://localhost:8001/admin/login

# Step 9: Check container status
print_status "Step 9: Checking container status..."
docker ps | grep backend

# Step 10: Show final status
print_status "Step 10: Final status..."
echo ""
echo "🌐 Backend Access URLs:"
echo "   Local: http://localhost:8001"
echo "   External: http://204.12.223.76:8001"
echo "   Admin Login: http://204.12.223.76:8001/admin/login"
echo ""
echo "📋 Container Status:"
docker ps | grep backend
echo ""
echo "🔗 Port Mapping:"
docker port eve-chatting-platform_backend_1
echo ""

print_success "Backend access fix completed!" 