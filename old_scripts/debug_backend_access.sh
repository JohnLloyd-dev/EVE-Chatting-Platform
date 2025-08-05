#!/bin/bash

echo "🔍 Debugging Backend Access Issues"
echo "=================================="

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
docker ps | grep backend

# Step 2: Check backend logs
print_status "Step 2: Checking backend logs..."
docker logs eve-chatting-platform_backend_1 --tail 20

# Step 3: Check if backend is listening on port 8001
print_status "Step 3: Checking if backend is listening on port 8001..."
netstat -tlnp | grep 8001

# Step 4: Test local backend access
print_status "Step 4: Testing local backend access..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health
echo " - Local health check"

# Step 5: Test external backend access
print_status "Step 5: Testing external backend access..."
curl -s -o /dev/null -w "%{http_code}" http://204.12.223.76:8001/health
echo " - External health check"

# Step 6: Test admin login endpoint specifically
print_status "Step 6: Testing admin login endpoint..."
curl -X POST http://localhost:8001/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  -w "\nHTTP Status: %{http_code}\n"

# Step 7: Test CORS for admin login
print_status "Step 7: Testing CORS for admin login..."
curl -H "Origin: http://204.12.223.76:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://localhost:8001/admin/login

# Step 8: Check firewall status for port 8001
print_status "Step 8: Checking firewall status for port 8001..."
sudo ufw status | grep 8001

# Step 9: Test from inside the backend container
print_status "Step 9: Testing from inside backend container..."
docker exec eve-chatting-platform_backend_1 curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health
echo " - Internal health check"

# Step 10: Check backend environment variables
print_status "Step 10: Checking backend environment variables..."
docker exec eve-chatting-platform_backend_1 env | grep -E "(DATABASE_URL|REDIS_URL|SECRET_KEY)"

# Step 11: Test database connectivity
print_status "Step 11: Testing database connectivity..."
docker exec eve-chatting-platform_backend_1 python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://adam@2025@man:eve@postgres@3241@postgres:5432/chatting_platform')
    print('Database connection: SUCCESS')
    conn.close()
except Exception as e:
    print(f'Database connection: FAILED - {e}')
"

# Step 12: Check if backend is accessible from frontend container
print_status "Step 12: Testing backend access from frontend container..."
docker exec eve-chatting-platform_frontend_1 curl -s -o /dev/null -w "%{http_code}" http://backend:8000/health
echo " - Frontend to backend health check"

echo ""
print_status "Debug information collected!"
echo ""
echo "🔧 Possible solutions:"
echo "   1. If backend not running: docker-compose restart backend"
echo "   2. If port 8001 not accessible: Check firewall and port mapping"
echo "   3. If CORS blocking: Restart backend to apply CORS changes"
echo "   4. If database connection failed: Check database credentials"
echo "   5. If external access fails: Check VPS firewall settings"
echo "" 