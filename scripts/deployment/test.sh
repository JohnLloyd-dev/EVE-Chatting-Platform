#!/bin/bash

echo "🧪 Testing EVE Chat Platform Deployment"
echo "======================================"

# Configuration
VPS_IP="204.12.233.105"

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

# Function to test URL
test_url() {
    local url=$1
    local description=$2
    
    print_status "Testing $description: $url"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
        print_success "$description: OK (HTTP $HTTP_CODE)"
        return 0
    else
        print_error "$description: FAILED (HTTP $HTTP_CODE)"
        return 1
    fi
}

print_status "Starting tests for VPS: $VPS_IP"
echo ""

# Test all services
print_status "Testing service endpoints..."

test_url "http://$VPS_IP:8001/health" "Backend Health"
test_url "http://$VPS_IP:8001/docs" "Backend API Docs"
test_url "http://$VPS_IP:3000" "Frontend"
test_url "http://$VPS_IP:3000/admin" "Admin Page"

echo ""

# Test database connectivity
print_status "Testing database connectivity..."
if docker ps --format "{{.Names}}" | grep -q "postgres"; then
    POSTGRES_CONTAINER=$(docker ps --format "{{.Names}}" | grep "postgres" | head -1)
    if docker exec "$POSTGRES_CONTAINER" pg_isready -U "adam2025man" &> /dev/null; then
        print_success "Database: Connected successfully"
    else
        print_error "Database: Connection failed"
    fi
else
    print_warning "Database: PostgreSQL container not found"
fi

echo ""

# Manual testing instructions
print_status "Manual Testing Instructions:"
echo "1. Open http://$VPS_IP:3000 in your browser"
echo "2. Try admin login at http://$VPS_IP:3000/admin (admin/adam@and@eve@3241)"
echo "3. Test webhook endpoint:"
echo "   curl -X POST http://$VPS_IP:8001/webhook/tally -H 'Content-Type: application/json' -d @tally_form.json"

echo ""
print_status "Testing complete!"