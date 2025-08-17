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
VPS_IP="204.12.233.105"
COMPOSE_FILE="docker-compose.yml"

# Database configuration
DB_USER="adam2025man"
DB_PASSWORD="adam2025"
DB_NAME="chatting_platform"

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
docker-compose -f $COMPOSE_FILE down

# Step 3: Build all services
print_status "Step 3: Building all services..."
docker-compose -f $COMPOSE_FILE build --no-cache

if [ $? -ne 0 ]; then
    print_error "Build failed"
    exit 1
fi

# Step 4: Start PostgreSQL and Redis first
print_status "Step 4: Starting PostgreSQL and Redis..."
docker-compose -f $COMPOSE_FILE up -d postgres redis

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
    docker-compose -f $COMPOSE_FILE up -d postgres
    
    # Wait for PostgreSQL to be ready
    print_status "Waiting for PostgreSQL to be ready..."
    sleep 20
    
    # Get the correct container name again
    POSTGRES_CONTAINER=$(get_postgres_container)
    if [ -z "$POSTGRES_CONTAINER" ]; then
        print_error "Could not find PostgreSQL container"
        exit 1
    fi
    
    # Check if PostgreSQL is ready (connect using the configured user)
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
            print_status "Detected binary PostgreSQL dump, using pg_restore..."
            
            # Try verbose full restore with better error checking
            print_status "Attempting full restore with verbose output..."
            docker exec "$POSTGRES_CONTAINER" pg_restore -U "$DB_USER" -d chatting_platform --verbose --clean --if-exists --no-owner --no-privileges /tmp/final123.sql 2>&1
            RESTORE_EXIT_CODE=$?
            
            # Check if any tables were actually created
            TABLE_COUNT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$DB_USER" -d chatting_platform -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ' || echo "0")
            
            if [ "$RESTORE_EXIT_CODE" -eq 0 ] && [ "$TABLE_COUNT" -gt 0 ]; then
                print_success "Full restore completed successfully with $TABLE_COUNT tables"
            else
                print_warning "Full restore failed or incomplete (exit code: $RESTORE_EXIT_CODE, tables: $TABLE_COUNT)"
                print_status "Trying alternative restore methods..."
                
                # Method 1: Try restoring with create statements first
                print_status "Creating database schema manually..."
                docker exec "$POSTGRES_CONTAINER" pg_restore -U "$DB_USER" -d chatting_platform --schema-only --verbose --clean --if-exists --create /tmp/final123.sql 2>&1
                
                # Check if tables were created
                TABLE_COUNT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$DB_USER" -d chatting_platform -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ' || echo "0")
                
                if [ "$TABLE_COUNT" -gt 0 ]; then
                    print_success "Schema created successfully with $TABLE_COUNT tables"
                    
                    # Now try to restore data
                    print_status "Restoring database data..."
                    docker exec "$POSTGRES_CONTAINER" pg_restore -U "$DB_USER" -d chatting_platform --data-only --verbose --disable-triggers /tmp/final123.sql 2>&1
                    
                    if [ $? -eq 0 ]; then
                        print_success "Data restored successfully"
                    else
                        print_warning "Data restore had issues, but continuing..."
                    fi
                else
                    print_error "Failed to create database schema. Showing pg_restore list:"
                    docker exec "$POSTGRES_CONTAINER" pg_restore --list /tmp/final123.sql | head -20
                    print_status "Attempting to extract SQL and import manually..."
                    
                    # Try extracting to SQL and importing
                    docker exec "$POSTGRES_CONTAINER" pg_restore -f /tmp/backup.sql /tmp/final123.sql
                    docker exec "$POSTGRES_CONTAINER" psql -U "$DB_USER" -d chatting_platform -f /tmp/backup.sql
                fi
            fi
        else
            print_status "Detected SQL file, using psql..."
            docker exec "$POSTGRES_CONTAINER" psql -U "$DB_USER" -d chatting_platform -f /tmp/final123.sql
        fi
        
        # Verify data was restored
        print_status "Verifying database restore..."
        USER_COUNT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$DB_USER" -d chatting_platform -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d ' ' | grep -E '^[0-9]+$' || echo "0")
        if [ "$USER_COUNT" -gt 0 ]; then
            print_success "Database verification successful - found $USER_COUNT users"
        else
            print_warning "Database restore may not have worked - no users found"
            print_status "Checking what tables exist..."
            docker exec "$POSTGRES_CONTAINER" psql -U "$DB_USER" -d chatting_platform -c "\dt"
        fi
    else
        print_error "PostgreSQL failed to start"
        exit 1
    fi
else
    print_status "Step 5: Starting PostgreSQL..."
    docker-compose -f $COMPOSE_FILE up -d postgres
    sleep 15
fi

# Step 6: AI Model is now integrated into Backend - no separate AI server needed
print_status "Step 6: AI Model is integrated into Backend (no separate AI server)"
print_status "The AI model will load when the backend starts up"

# Step 7: Start Backend and Celery (with integrated AI model)
print_status "Step 7: Starting Backend and Celery with integrated AI model..."
docker-compose -f $COMPOSE_FILE up -d backend celery-worker

# Wait for backend to be ready and AI model to load
print_status "Waiting for Backend to be ready and AI model to load..."
sleep 30

# Check backend health and AI model status
print_status "Checking backend health, database connection, and AI model status..."
for i in {1..8}; do
    BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$VPS_IP:8001/health 2>/dev/null || echo "000")
    AI_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$VPS_IP:8001/ai/health 2>/dev/null || echo "000")
    
    if [ "$BACKEND_STATUS" = "200" ] && [ "$AI_STATUS" = "200" ]; then
        print_success "Backend is healthy, database connected, and AI model loaded successfully"
        break
    else
        print_warning "Backend/AI not ready yet, attempt $i/8"
        print_warning "Backend Status: $BACKEND_STATUS, AI Status: $AI_STATUS"
        
        # Check backend logs for issues
        if [ $i -eq 4 ]; then
            print_status "Checking backend logs for issues..."
            docker-compose -f $COMPOSE_FILE logs backend --tail 10
        fi
        
        sleep 15
    fi
done

# If backend still not healthy, try restarting with database fix
if [ "$BACKEND_STATUS" != "200" ]; then
    print_warning "Backend not healthy, attempting database connection fix..."
    docker-compose -f $COMPOSE_FILE stop backend
    sleep 5
    docker-compose -f $COMPOSE_FILE up -d backend
    sleep 15
    
    # Check again
    BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$VPS_IP:8001/health 2>/dev/null || echo "000")
    if [ "$BACKEND_STATUS" = "200" ]; then
        print_success "Backend is now healthy after database fix"
    else
        print_error "Backend still not healthy after database fix (Status: $BACKEND_STATUS)"
        print_status "Check backend logs: docker-compose -f $COMPOSE_FILE logs backend"
    fi
fi

# Step 8: Start Frontend
print_status "Step 8: Starting Frontend..."
docker-compose -f $COMPOSE_FILE up -d frontend

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
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$VPS_IP:8001/health 2>/dev/null || echo "000")
if [ "$BACKEND_STATUS" = "200" ]; then
    print_success "Backend: OK (http://$VPS_IP:8001)"
else
    print_error "Backend: FAILED (Status: $BACKEND_STATUS)"
fi

# Test AI server
AI_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$VPS_IP:8000/health 2>/dev/null || echo "000")
if [ "$AI_STATUS" = "200" ]; then
    print_success "AI Server: OK (http://$VPS_IP:8000)"
else
    print_warning "AI Server: FAILED (Status: $AI_STATUS)"
fi

# Test frontend
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$VPS_IP:3000 2>/dev/null || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    print_success "Frontend: OK (http://$VPS_IP:3000)"
else
    print_warning "Frontend: FAILED (Status: $FRONTEND_STATUS)"
fi

echo ""
print_success "🚀 Deployment completed!"
echo ""
print_status "Access URLs:"
echo "  Frontend: http://$VPS_IP:3000"
echo "  Backend API: http://$VPS_IP:8001"
echo "  AI Server: http://$VPS_IP:8000"
echo ""
print_status "For troubleshooting, run: ./troubleshoot.sh" 