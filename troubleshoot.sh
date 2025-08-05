#!/bin/bash

echo "🔧 EVE Chat Platform - Troubleshooting"
echo "======================================"

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

# Test AI server
AI_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
if [ "$AI_STATUS" = "200" ]; then
    print_success "AI Server: OK (http://localhost:8000)"
else
    print_warning "AI Server: FAILED (Status: $AI_STATUS)"
fi

# Test frontend
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    print_success "Frontend: OK (http://localhost:3000)"
else
    print_warning "Frontend: FAILED (Status: $FRONTEND_STATUS)"
fi

echo ""
print_status "Quick fixes:"

# Check if containers are running
if ! docker ps | grep -q "eve-chatting-platform_backend_1"; then
    print_warning "Backend container not running"
    echo "  Fix: docker-compose up -d backend"
fi

if ! docker ps | grep -q "eve-chatting-platform_ai-server_1"; then
    print_warning "AI Server container not running"
    echo "  Fix: docker-compose up -d ai-server"
fi

if ! docker ps | grep -q "eve-chatting-platform_frontend_1"; then
    print_warning "Frontend container not running"
    echo "  Fix: docker-compose up -d frontend"
fi

if ! docker ps | grep -q "eve-chatting-platform_postgres_1"; then
    print_warning "PostgreSQL container not running"
    echo "  Fix: docker-compose up -d postgres"
fi

if ! docker ps | grep -q "eve-chatting-platform_redis_1"; then
    print_warning "Redis container not running"
    echo "  Fix: docker-compose up -d redis"
fi

echo ""
print_status "Useful commands:"
echo "  View logs: docker-compose logs [service_name]"
echo "  Restart service: docker-compose restart [service_name]"
echo "  Rebuild service: docker-compose build [service_name]"
echo "  Full restart: docker-compose down && docker-compose up -d"
echo "  Check AI model loading: docker-compose logs ai-server" 