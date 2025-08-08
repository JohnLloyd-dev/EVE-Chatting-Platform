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
DB_USER="adam@2025@man"
DB_PASSWORD="eve@postgres@3241"

# Function to get the correct PostgreSQL container name
get_postgres_container() {
    # Try the new naming convention first (hyphens)
    if docker ps --format "table {{.Names}}" | grep -q "eve-chatting-platform-postgres-1"; then
        echo "eve-chatting-platform-postgres-1"
    # Try the old naming convention (underscores)
    elif docker ps --format "table {{.Names}}" | grep -q "eve-chatting-platform_postgres_1"; then
        echo "eve-chatting-platform_postgres_1"
    else
        # If neither exists, try to find any postgres container
        POSTGRES_CONTAINER=$(docker ps --format "table {{.Names}}" | grep -i postgres | head -1)
        if [ -n "$POSTGRES_CONTAINER" ]; then
            echo "$POSTGRES_CONTAINER"
        else
            echo ""
        fi
    fi
}

# Step 1: Check if backup file exists
print_status "Step 1: Checking backup file..."
if [ -f "final123.sql" ]; then
    print_success "Found final123.sql in root directory"
    DB_RESTORE_NEEDED=true
elif [ -f "docs/deployment/final123.sql" ]; then
    print_success "Found final123.sql in docs/deployment/"
    cp docs/deployment/final123.sql .
    DB_RESTORE_NEEDED=true
else
    print_warning "No final123.sql found, skipping database restore"
    DB_RESTORE_NEEDED=false
fi

# Step 2: Stop existing containers
print_status "Step 2: Stopping existing containers..."
docker-compose down

# Step 3: Build all services
print_status "Step 3: Building all services..."
docker-compose build --no-cache

if [ $? -ne 0 ]; then
    print_error "Build failed"
    exit 1
fi

# Step 4: Start PostgreSQL and Redis first
print_status "Step 4: Starting PostgreSQL and Redis..."
docker-compose up -d postgres redis

# Wait for PostgreSQL to be ready
print_status "Waiting for PostgreSQL to be ready..."
sleep 20

# Get the correct container name
POSTGRES_CONTAINER=$(get_postgres_container)
if [ -z "$POSTGRES_CONTAINER" ]; then
    print_error "Could not find PostgreSQL container"
    exit 1
fi

print_status "Using PostgreSQL container: $POSTGRES_CONTAINER"

for i in {1..5}; do
    if docker exec "$POSTGRES_CONTAINER" pg_isready -U "$DB_USER"; then
        print_success "PostgreSQL is ready"
        break
    else
        print_warning "PostgreSQL not ready yet, attempt $i/5"
        sleep 10
    fi
done

# Step 5: Start PostgreSQL and restore database if needed
if [ "$DB_RESTORE_NEEDED" = true ]; then
    print_status "Step 5: Starting PostgreSQL and restoring database..."
    
    # Start PostgreSQL only
    docker-compose up -d postgres
    
    # Wait for PostgreSQL to be ready
    print_status "Waiting for PostgreSQL to be ready..."
    sleep 20
    
    # Get the correct container name again
    POSTGRES_CONTAINER=$(get_postgres_container)
    if [ -z "$POSTGRES_CONTAINER" ]; then
        print_error "Could not find PostgreSQL container"
        exit 1
    fi
    
    # Check if PostgreSQL is ready
    for i in {1..5}; do
        if docker exec "$POSTGRES_CONTAINER" pg_isready -U "$DB_USER"; then
            print_success "PostgreSQL is ready"
            break
        else
            print_warning "PostgreSQL not ready yet, attempt $i/5"
            sleep 10
        fi
    done
    
    # Verify PostgreSQL is ready
    if docker exec "$POSTGRES_CONTAINER" pg_isready -U "$DB_USER"; then
        print_success "PostgreSQL is ready for database restore"
        
        # Drop and recreate database to ensure clean restore
        print_status "Preparing database for restore..."
        docker exec "$POSTGRES_CONTAINER" psql -U "$DB_USER" -c "DROP DATABASE IF EXISTS chatting_platform;"
        docker exec "$POSTGRES_CONTAINER" psql -U "$DB_USER" -c "CREATE DATABASE chatting_platform;"
        
        # Copy backup file to container
        print_status "Copying final123.sql to PostgreSQL container..."
        docker cp final123.sql "$POSTGRES_CONTAINER:/tmp/"
        
        # Check if it's a binary dump or SQL file
        if file final123.sql | grep -q "PostgreSQL"; then
            print_status "Detected binary PostgreSQL dump, using pg_restore with schema-only first..."
            
            # First, restore schema only (tables, constraints, etc.)
            print_status "Restoring database schema..."
            docker exec "$POSTGRES_CONTAINER" pg_restore -U "$DB_USER" -d chatting_platform --schema-only --clean --if-exists /tmp/final123.sql
            
            if [ $? -eq 0 ]; then
                print_success "Schema restored successfully"
                
                # Then restore data only
                print_status "Restoring database data..."
                docker exec "$POSTGRES_CONTAINER" pg_restore -U "$DB_USER" -d chatting_platform --data-only --disable-triggers /tmp/final123.sql
                
                if [ $? -eq 0 ]; then
                    print_success "Data restored successfully"
                else
                    print_warning "Data restore had issues, but continuing..."
                fi
            else
                print_error "Schema restore failed"
                exit 1
            fi
        else
            print_status "Detected SQL file, using psql..."
            docker exec "$POSTGRES_CONTAINER" psql -U "$DB_USER" -d chatting_platform -f /tmp/final123.sql
        fi
        
        if [ $? -eq 0 ]; then
            print_success "Database restored successfully"
            
            # Verify data was restored
            print_status "Verifying database restore..."
            USER_COUNT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$DB_USER" -d chatting_platform -t -c "SELECT COUNT(*) FROM users;" | tr -d ' ')
            if [ "$USER_COUNT" -gt 0 ]; then
                print_success "Database verification successful - found $USER_COUNT users"
            else
                print_warning "Database restore may not have worked - no users found"
            fi
        else
            print_error "Database restore failed"
            print_status "Attempting alternative restore method..."
            
            # Try alternative method with schema and data separation
            print_status "Trying schema-only restore first..."
            docker exec "$POSTGRES_CONTAINER" pg_restore -U "$DB_USER" -d chatting_platform --schema-only --clean --if-exists /tmp/final123.sql
            
            print_status "Adding missing columns..."
            docker exec "$POSTGRES_CONTAINER" psql -U "$DB_USER" -d chatting_platform -c "ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_responses_enabled BOOLEAN DEFAULT true;"
            
            print_status "Trying data-only restore with triggers disabled..."
            docker exec "$POSTGRES_CONTAINER" pg_restore -U "$DB_USER" -d chatting_platform --data-only --disable-triggers /tmp/final123.sql
            
            if [ $? -eq 0 ]; then
                print_success "Database restored with alternative method"
            else
                print_warning "Alternative restore had issues, but continuing..."
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

# Step 6: Start AI Server
print_status "Step 6: Starting AI Server..."
docker-compose up -d ai-server

# Wait for AI server to be ready (it takes time to load the model)
print_status "Waiting for AI Server to load model (this may take several minutes)..."
for i in {1..20}; do
    AI_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
    if [ "$AI_STATUS" = "200" ]; then
        print_success "AI Server is ready"
        break
    else
        print_warning "AI Server not ready yet, attempt $i/20 (Status: $AI_STATUS)"
        sleep 30
    fi
done

# Step 7: Start Backend and Celery
print_status "Step 7: Starting Backend and Celery..."
docker-compose up -d backend celery-worker

# Wait for backend to be ready
print_status "Waiting for Backend to be ready..."
sleep 15

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

# Step 8: Start Frontend
print_status "Step 8: Starting Frontend..."
docker-compose up -d frontend

# Wait for frontend to be ready
print_status "Waiting for Frontend to be ready..."
sleep 15

# Step 9: Final health checks
print_status "Step 9: Running final health checks..."

# Check all services
print_status "Checking all services..."
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
print_success "🚀 Deployment completed!"
echo ""
print_status "Access URLs:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8001"
echo "  AI Server: http://localhost:8000"
echo ""
print_status "For troubleshooting, run: ./troubleshoot.sh" 