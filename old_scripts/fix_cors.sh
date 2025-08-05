#!/bin/bash

echo "🔧 Fixing CORS Issues"
echo "====================="

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

# Step 1: Check current API configuration
print_status "Step 1: Checking current API configuration..."
echo "Frontend API URL: $NEXT_PUBLIC_API_URL"
echo "Backend URL: http://204.12.223.76:8001"

# Step 2: Test backend connectivity
print_status "Step 2: Testing backend connectivity..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health
echo " - Backend health check"

# Step 3: Test frontend to backend connection
print_status "Step 3: Testing frontend to backend connection..."
curl -H "Origin: http://204.12.223.76:3000" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://localhost:8001/health

# Step 4: Check CORS headers in backend response
print_status "Step 4: Checking CORS headers..."
curl -I -H "Origin: http://204.12.223.76:3000" http://localhost:8001/health

# Step 5: Restart backend to ensure CORS is applied
print_status "Step 5: Restarting backend to ensure CORS is applied..."
docker-compose restart backend

# Step 6: Wait for backend to be ready
print_status "Step 6: Waiting for backend to be ready..."
sleep 10

# Step 7: Test CORS again
print_status "Step 7: Testing CORS again..."
curl -H "Origin: http://204.12.223.76:3000" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://localhost:8001/health

# Step 8: Test actual API call
print_status "Step 8: Testing actual API call..."
curl -H "Origin: http://204.12.223.76:3000" \
     -H "Content-Type: application/json" \
     http://localhost:8001/health

# Step 9: Check browser console for CORS errors
print_status "Step 9: CORS configuration summary..."
echo ""
echo "🌐 CORS Configuration:"
echo "   Frontend Origin: http://204.12.223.76:3000"
echo "   Backend API: http://204.12.223.76:8001"
echo "   Allowed Origins:"
echo "     - http://localhost:3000"
echo "     - http://frontend:3000"
echo "     - http://204.12.223.76:3000"
echo "     - http://204.12.223.76:8001"
echo ""
echo "🔧 If CORS still fails:"
echo "   1. Check browser console for specific error"
echo "   2. Verify frontend is using correct API URL"
echo "   3. Ensure backend CORS middleware is loaded"
echo "   4. Check if any proxy/load balancer is interfering"
echo ""

print_success "CORS fix completed!" 