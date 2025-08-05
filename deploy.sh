#!/bin/bash

echo "🚀 EVE Chat Platform - Complete Deployment"
echo "=========================================="

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

# Configuration
VPS_IP="204.12.223.76"
DB_USER="adam@2025@man"
DB_PASSWORD="eve@postgres@3241"

# Step 1: Pull latest changes
print_status "Step 1: Pulling latest changes..."
git pull origin main
if [ $? -ne 0 ]; then
    print_error "Failed to pull changes"
    exit 1
fi
print_success "Latest changes pulled"

# Step 2: Stop all containers
print_status "Step 2: Stopping all containers..."
docker-compose down
print_success "All containers stopped"

# Step 3: Clean up any orphaned containers
print_status "Step 3: Cleaning up orphaned containers..."
docker container prune -f
docker network prune -f
print_success "Cleanup completed"

# Step 4: Check if final123.sql exists
print_status "Step 4: Checking database backup..."
if [ -f "final123.sql" ]; then
    print_success "Found final123.sql backup file"
    DB_RESTORE_NEEDED=true
else
    print_warning "No final123.sql found - skipping database restore"
    DB_RESTORE_NEEDED=false
fi

# Step 5: Start PostgreSQL and restore database if needed
if [ "$DB_RESTORE_NEEDED" = true ]; then
    print_status "Step 5: Starting PostgreSQL and restoring database..."
    
    # Start PostgreSQL only
    docker-compose up -d postgres
    
    # Wait for PostgreSQL to be ready
    print_status "Waiting for PostgreSQL to be ready..."
    sleep 15
    
    # Check if PostgreSQL is ready
    if docker exec eve-chatting-platform_postgres_1 pg_isready -U "$DB_USER"; then
        print_success "PostgreSQL is ready"
        
        # Restore database
        print_status "Restoring database from final123.sql..."
        docker cp final123.sql eve-chatting-platform_postgres_1:/tmp/
        
        # Convert and restore
        docker exec eve-chatting-platform_postgres_1 pg_restore -U "$DB_USER" -d chatting_platform --clean --if-exists /tmp/final123.sql
        
        if [ $? -eq 0 ]; then
            print_success "Database restored successfully"
        else
            print_warning "Database restore had some issues, but continuing..."
        fi
    else
        print_error "PostgreSQL failed to start"
        exit 1
    fi
else
    print_status "Step 5: Starting PostgreSQL..."
    docker-compose up -d postgres
    sleep 10
fi

# Step 6: Start Redis
print_status "Step 6: Starting Redis..."
docker-compose up -d redis
sleep 5

# Step 7: Build and start backend
print_status "Step 7: Building and starting backend..."
docker-compose build backend
docker-compose up -d backend

# Wait for backend to be ready
print_status "Waiting for backend to be ready..."
sleep 20

# Check backend health
print_status "Checking backend health..."
for i in {1..5}; do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health | grep -q "200"; then
        print_success "Backend is healthy"
        break
    else
        print_warning "Backend not ready yet, attempt $i/5"
        sleep 10
    fi
done

# Step 8: Start Celery worker
print_status "Step 8: Starting Celery worker..."
docker-compose up -d celery-worker
sleep 5

# Step 9: Build and start frontend
print_status "Step 9: Building and starting frontend..."
docker-compose build frontend
docker-compose up -d frontend

# Wait for frontend to be ready
print_status "Waiting for frontend to be ready..."
sleep 20

# Step 10: Verify all services
print_status "Step 10: Verifying all services..."

# Check all containers are running
print_status "Checking container status..."
docker ps

# Test backend access
print_status "Testing backend access..."
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health)
if [ "$BACKEND_STATUS" = "200" ]; then
    print_success "Backend accessible locally"
else
    print_error "Backend not accessible locally (Status: $BACKEND_STATUS)"
fi

# Test external backend access
EXTERNAL_BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$VPS_IP:8001/health)
if [ "$EXTERNAL_BACKEND_STATUS" = "200" ]; then
    print_success "Backend accessible externally"
else
    print_warning "Backend not accessible externally (Status: $EXTERNAL_BACKEND_STATUS)"
fi

# Test frontend access
print_status "Testing frontend access..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
if [ "$FRONTEND_STATUS" = "200" ]; then
    print_success "Frontend accessible locally"
else
    print_warning "Frontend not accessible locally (Status: $FRONTEND_STATUS)"
fi

# Test external frontend access
EXTERNAL_FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$VPS_IP:3000)
if [ "$EXTERNAL_FRONTEND_STATUS" = "200" ]; then
    print_success "Frontend accessible externally"
else
    print_warning "Frontend not accessible externally (Status: $EXTERNAL_FRONTEND_STATUS)"
fi

# Step 11: Test CORS
print_status "Step 11: Testing CORS configuration..."
CORS_TEST=$(curl -s -H "Origin: http://$VPS_IP:3000" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://localhost:8001/health)
if [ $? -eq 0 ]; then
    print_success "CORS preflight test passed"
else
    print_warning "CORS preflight test failed"
fi

# Step 12: Final status report
echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo ""
echo "📋 Service Status:"
echo "   Backend API: http://$VPS_IP:8001"
echo "   Frontend: http://$VPS_IP:3000"
echo "   Admin Dashboard: http://$VPS_IP:3000/admin"
echo ""
echo "🔐 Admin Credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "📊 Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "🔧 Troubleshooting:"
echo "   If services are not accessible:"
echo "   1. Check firewall: sudo ufw status"
echo "   2. Check logs: docker-compose logs [service_name]"
echo "   3. Restart service: docker-compose restart [service_name]"
echo "   4. Rebuild service: docker-compose build [service_name]"
echo ""
echo "🌐 Access URLs:"
echo "   Local Backend: http://localhost:8001"
echo "   Local Frontend: http://localhost:3000"
echo "   External Backend: http://$VPS_IP:8001"
echo "   External Frontend: http://$VPS_IP:3000"
echo ""

print_success "Deployment completed successfully!" 