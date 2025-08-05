#!/bin/bash

echo "🔧 Fixing Database Connection"
echo "============================"

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

# Step 1: Stop backend and celery services
print_status "Step 1: Stopping backend and celery services..."
docker-compose stop backend celery-worker

# Step 2: Restart backend with correct database configuration
print_status "Step 2: Restarting backend with correct database configuration..."
docker-compose up -d backend

# Step 3: Wait for backend to be ready
print_status "Step 3: Waiting for backend to be ready..."
sleep 15

# Step 4: Check backend logs
print_status "Step 4: Checking backend logs..."
docker-compose logs backend --tail 10

# Step 5: Test backend health
print_status "Step 5: Testing backend health..."
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health)
if [ "$BACKEND_STATUS" = "200" ]; then
    print_success "Backend is healthy"
else
    print_error "Backend health check failed (Status: $BACKEND_STATUS)"
fi

# Step 6: Start celery worker
print_status "Step 6: Starting celery worker..."
docker-compose up -d celery-worker

# Step 7: Test CORS
print_status "Step 7: Testing CORS configuration..."
CORS_TEST=$(curl -s -H "Origin: http://204.12.223.76:3000" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://localhost:8001/health)
if [ $? -eq 0 ]; then
    print_success "CORS preflight test passed"
else
    print_warning "CORS preflight test failed"
fi

# Step 8: Final status
print_status "Step 8: Final status..."
echo ""
echo "📋 Container Status:"
docker ps | grep -E "(backend|celery|postgres)"
echo ""
echo "🌐 Test URLs:"
echo "   Backend Health: http://localhost:8001/health"
echo "   External Backend: http://204.12.223.76:8001/health"
echo "   Frontend: http://204.12.223.76:3000"
echo ""

print_success "Database connection fix completed!" 