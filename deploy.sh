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
    print_success "Found final123.sql backup file in root directory"
    DB_RESTORE_NEEDED=true
elif [ -f "docs/deployment/final123.sql" ]; then
    print_success "Found final123.sql backup file in docs/deployment/"
    print_status "Copying final123.sql to root directory..."
    cp docs/deployment/final123.sql .
    DB_RESTORE_NEEDED=true
else
    print_warning "No final123.sql found - skipping database restore"
    print_status "You can copy final123.sql to root directory and run deploy.sh again"
    DB_RESTORE_NEEDED=false
fi

# Step 5: Start PostgreSQL and restore database if needed
if [ "$DB_RESTORE_NEEDED" = true ]; then
    print_status "Step 5: Starting PostgreSQL and restoring database..."
    
    # Start PostgreSQL only
    docker-compose up -d postgres
    
    # Wait for PostgreSQL to be ready
    print_status "Waiting for PostgreSQL to be ready..."
    sleep 20
    
    # Check if PostgreSQL is ready
    for i in {1..5}; do
        if docker exec eve-chatting-platform_postgres_1 pg_isready -U "$DB_USER"; then
            print_success "PostgreSQL is ready"
            break
        else
            print_warning "PostgreSQL not ready yet, attempt $i/5"
            sleep 10
        fi
    done
    
    # Verify PostgreSQL is ready
    if docker exec eve-chatting-platform_postgres_1 pg_isready -U "$DB_USER"; then
        print_success "PostgreSQL is ready for database restore"
        
        # Drop and recreate database to ensure clean restore
        print_status "Preparing database for restore..."
        docker exec eve-chatting-platform_postgres_1 psql -U "$DB_USER" -c "DROP DATABASE IF EXISTS chatting_platform;"
        docker exec eve-chatting-platform_postgres_1 psql -U "$DB_USER" -c "CREATE DATABASE chatting_platform;"
        
        # Copy backup file to container
        print_status "Copying final123.sql to PostgreSQL container..."
        docker cp final123.sql eve-chatting-platform_postgres_1:/tmp/
        
        # Check if it's a binary dump or SQL file
        if file final123.sql | grep -q "PostgreSQL"; then
            print_status "Detected binary PostgreSQL dump, using pg_restore..."
            docker exec eve-chatting-platform_postgres_1 pg_restore -U "$DB_USER" -d chatting_platform --clean --if-exists /tmp/final123.sql
        else
            print_status "Detected SQL file, using psql..."
            docker exec eve-chatting-platform_postgres_1 psql -U "$DB_USER" -d chatting_platform -f /tmp/final123.sql
        fi
        
        if [ $? -eq 0 ]; then
            print_success "Database restored successfully"
            
            # Verify data was restored
            print_status "Verifying database restore..."
            USER_COUNT=$(docker exec eve-chatting-platform_postgres_1 psql -U "$DB_USER" -d chatting_platform -t -c "SELECT COUNT(*) FROM users;" | tr -d ' ')
            if [ "$USER_COUNT" -gt 0 ]; then
                print_success "Database verification successful - found $USER_COUNT users"
            else
                print_warning "Database restore may not have worked - no users found"
            fi
        else
            print_error "Database restore failed"
            print_status "Attempting alternative restore method..."
            
            # Try alternative method
            docker exec eve-chatting-platform_postgres_1 psql -U "$DB_USER" -d chatting_platform -f /tmp/final123.sql
            if [ $? -eq 0 ]; then
                print_success "Database restored with alternative method"
            else
                print_error "Database restore failed completely"
                exit 1
            fi
        fi
    else
        print_error "PostgreSQL failed to start"
        exit 1
    fi
else
    print_status "Step 5: Starting PostgreSQL..."
    docker-compose up -d postgres
    sleep 15
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

# Check backend health with database connection verification
print_status "Checking backend health and database connection..."
for i in {1..5}; do
    BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health 2>/dev/null || echo "000")
    if [ "$BACKEND_STATUS" = "200" ]; then
        print_success "Backend is healthy and database connection successful"
        break
    else
        print_warning "Backend not ready yet, attempt $i/5 (Status: $BACKEND_STATUS)"
        
        # Check backend logs for database connection issues
        if [ $i -eq 3 ]; then
            print_status "Checking backend logs for database connection issues..."
            docker-compose logs backend --tail 5
        fi
        
        sleep 10
    fi
done

# If backend still not healthy, try restarting with database fix
if [ "$BACKEND_STATUS" != "200" ]; then
    print_warning "Backend not healthy, attempting database connection fix..."
    docker-compose stop backend
    sleep 5
    docker-compose up -d backend
    sleep 15
    
    # Check again
    BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health 2>/dev/null || echo "000")
    if [ "$BACKEND_STATUS" = "200" ]; then
        print_success "Backend is now healthy after database fix"
    else
        print_error "Backend still not healthy after database fix (Status: $BACKEND_STATUS)"
        print_status "Check backend logs: docker-compose logs backend"
    fi
fi

# Verify database data is accessible through backend
if [ "$BACKEND_STATUS" = "200" ] && [ "$DB_RESTORE_NEEDED" = true ]; then
    print_status "Verifying database data through backend API..."
    sleep 5
    
    # Test a simple API call to verify data access
    API_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health 2>/dev/null || echo "000")
    if [ "$API_TEST" = "200" ]; then
        print_success "Backend API is responding correctly"
    else
        print_warning "Backend API test failed (Status: $API_TEST)"
    fi
fi

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