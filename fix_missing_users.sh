#!/bin/bash

echo "🔧 Fix Missing PostgreSQL Users"
echo "==============================="

# Function to print colored output
print_status() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

print_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

echo ""
print_status "Step 1: Finding PostgreSQL container..."
POSTGRES_CONTAINER=$(docker ps --format "{{.Names}}" | grep "postgres" | head -1)
if [ -z "$POSTGRES_CONTAINER" ]; then
    print_error "PostgreSQL container not found"
    exit 1
fi
print_success "Found container: $POSTGRES_CONTAINER"

echo ""
print_status "Step 2: Checking container environment..."
POSTGRES_USER=$(docker exec "$POSTGRES_CONTAINER" env | grep "POSTGRES_USER" | cut -d'=' -f2)
POSTGRES_PASSWORD=$(docker exec "$POSTGRES_CONTAINER" env | grep "POSTGRES_PASSWORD" | cut -d'=' -f2)
POSTGRES_DB=$(docker exec "$POSTGRES_CONTAINER" env | grep "POSTGRES_DB" | cut -d'=' -f2)

print_success "Container expects:"
print_success "  User: $POSTGRES_USER"
print_success "  Password: $POSTGRES_PASSWORD"
print_success "  Database: $POSTGRES_DB"

echo ""
print_status "Step 3: Attempting to connect as superuser..."
# Try to connect as the expected user first
if docker exec "$POSTGRES_CONTAINER" pg_isready -U "$POSTGRES_USER" 2>/dev/null; then
    print_success "User '$POSTGRES_USER' already exists and can connect!"
else
    print_warning "User '$POSTGRES_USER' does not exist, need to create it"
fi

echo ""
print_status "Step 4: Creating missing users..."
# We need to access PostgreSQL as a superuser to create users
# Since the container was created with POSTGRES_USER=adam2025man, 
# PostgreSQL should have created this user during initialization
# Let's try to connect and create if needed

# First, try to connect as the expected user
if docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" 2>/dev/null; then
    print_success "Successfully connected as '$POSTGRES_USER'"
else
    print_warning "Cannot connect as '$POSTGRES_USER', trying to fix..."
    
    # Try to connect as postgres superuser (might exist from old setup)
    if docker exec "$POSTGRES_CONTAINER" psql -U postgres -d postgres -c "SELECT 1;" 2>/dev/null; then
        print_success "Connected as postgres superuser, creating missing user..."
        docker exec "$POSTGRES_CONTAINER" psql -U postgres -d postgres << EOF
CREATE USER "$POSTGRES_USER" WITH PASSWORD '$POSTGRES_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE "$POSTGRES_DB" TO "$POSTGRES_USER";
ALTER USER "$POSTGRES_USER" CREATEDB;
EOF
    else
        print_error "Cannot connect as any superuser. Container may need recreation."
        print_status "Trying to restart PostgreSQL container..."
        docker restart "$POSTGRES_CONTAINER"
        sleep 10
        
        # Try again after restart
        if docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" 2>/dev/null; then
            print_success "Successfully connected after restart!"
        else
            print_error "Still cannot connect. Container may need recreation with fresh volume."
            exit 1
        fi
    fi
fi

echo ""
print_status "Step 5: Testing final connection..."
if docker exec "$POSTGRES_CONTAINER" pg_isready -U "$POSTGRES_USER"; then
    print_success "Final connection test successful!"
else
    print_error "Final connection test failed"
    exit 1
fi

echo ""
print_status "Step 6: Restarting services to use new credentials..."
docker-compose -f docker-compose.gpu.yml restart backend celery-worker

echo ""
print_status "Step 7: Waiting for services to restart..."
sleep 15

echo ""
print_status "Step 8: Checking service status..."
docker-compose -f docker-compose.gpu.yml ps

echo ""
print_success "Missing users fixed successfully!"
print_status "Username: $POSTGRES_USER"
print_status "Password: $POSTGRES_PASSWORD"
print_status "Database: $POSTGRES_DB"
print_status "All services should now be able to connect." 