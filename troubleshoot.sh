#!/bin/bash

echo "🔧 EVE Chat Platform - Troubleshooting"
echo "====================================="

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

# Check container status
print_status "Checking container status..."
docker ps

echo ""
print_status "Testing service connectivity..."

# Test backend
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health 2>/dev/null || echo "000")
if [ "$BACKEND_STATUS" = "200" ]; then
    print_success "Backend: OK (http://localhost:8001)"
else
    print_error "Backend: FAILED (Status: $BACKEND_STATUS)"
fi

# Test frontend
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    print_success "Frontend: OK (http://localhost:3000)"
else
    print_warning "Frontend: FAILED (Status: $FRONTEND_STATUS)"
fi

# Test external access
print_status "Testing external access..."
EXTERNAL_BACKEND=$(curl -s -o /dev/null -w "%{http_code}" http://204.12.223.76:8001/health 2>/dev/null || echo "000")
EXTERNAL_FRONTEND=$(curl -s -o /dev/null -w "%{http_code}" http://204.12.223.76:3000 2>/dev/null || echo "000")

if [ "$EXTERNAL_BACKEND" = "200" ]; then
    print_success "External Backend: OK"
else
    print_warning "External Backend: FAILED (Status: $EXTERNAL_BACKEND)"
fi

if [ "$EXTERNAL_FRONTEND" = "200" ]; then
    print_success "External Frontend: OK"
else
    print_warning "External Frontend: FAILED (Status: $EXTERNAL_FRONTEND)"
fi

echo ""
print_status "Quick fixes:"
echo "1. Restart all services: docker-compose restart"
echo "2. Rebuild services: docker-compose build"
echo "3. Check logs: docker-compose logs [service_name]"
echo "4. Check firewall: sudo ufw status"
echo "5. Full redeploy: ./deploy.sh"
echo ""
print_success "Troubleshooting completed!" 