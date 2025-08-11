#!/bin/bash

echo "🔐 Updating Database Credentials in Running Container"
echo "===================================================="

# Function to print colored output
print_status() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

print_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

print_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

echo ""
print_status "Step 1: Checking current PostgreSQL container status..."
if ! docker ps | grep -q "postgres"; then
    print_error "PostgreSQL container not found. Please start the services first."
    exit 1
fi

POSTGRES_CONTAINER=$(docker ps --format "{{.Names}}" | grep "postgres" | head -1)
print_success "Found PostgreSQL container: $POSTGRES_CONTAINER"

echo ""
print_status "Step 2: Testing current database connection..."
if docker exec "$POSTGRES_CONTAINER" pg_isready -U postgres; then
    print_success "PostgreSQL is running and accessible as superuser"
else
    print_error "Cannot connect to PostgreSQL as superuser"
    exit 1
fi

echo ""
print_status "Step 3: Checking if new user already exists..."
if docker exec "$POSTGRES_CONTAINER" psql -U postgres -d postgres -c "SELECT 1 FROM pg_roles WHERE rolname='adam2025man';" 2>/dev/null | grep -q "1"; then
    print_warning "User 'adam2025man' already exists, updating password..."
    docker exec "$POSTGRES_CONTAINER" psql -U postgres -d postgres -c "ALTER USER adam2025man WITH PASSWORD 'adam2025';"
else
    print_status "Creating new user 'adam2025man'..."
    docker exec "$POSTGRES_CONTAINER" psql -U postgres -d postgres -c "CREATE USER adam2025man WITH PASSWORD 'adam2025';"
fi

echo ""
print_status "Step 4: Granting necessary privileges..."
docker exec "$POSTGRES_CONTAINER" psql -U postgres -d postgres << 'EOF'
-- Grant necessary privileges
GRANT CONNECT ON DATABASE chatting_platform TO adam2025man;
GRANT USAGE ON SCHEMA public TO adam2025man;

-- Grant table permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO adam2025man;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO adam2025man;

-- Grant permissions for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO adam2025man;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO adam2025man;

-- Enable login
ALTER USER adam2025man LOGIN;
EOF

if [ $? -eq 0 ]; then
    print_success "Privileges granted successfully"
else
    print_error "Failed to grant privileges"
    exit 1
fi

echo ""
print_status "Step 5: Testing new user connection..."
if docker exec "$POSTGRES_CONTAINER" pg_isready -U adam2025man; then
    print_success "New user 'adam2025man' can connect successfully"
else
    print_error "New user 'adam2025man' cannot connect"
    exit 1
fi

echo ""
print_status "Step 6: Testing database access with new user..."
if docker exec "$POSTGRES_CONTAINER" psql -U adam2025man -d chatting_platform -c "SELECT 1;" 2>/dev/null | grep -q "1"; then
    print_success "New user can access chatting_platform database"
else
    print_error "New user cannot access chatting_platform database"
    exit 1
fi

echo ""
print_status "Step 7: Restarting backend and celery services to use new credentials..."
docker-compose -f docker-compose.gpu.yml restart backend celery-worker

echo ""
print_status "Step 8: Waiting for services to restart..."
sleep 15

echo ""
print_status "Step 9: Checking service status..."
docker-compose -f docker-compose.gpu.yml ps

echo ""
print_status "Step 10: Checking backend logs for connection success..."
echo "=== Backend Logs (last 10 lines) ==="
docker-compose -f docker-compose.gpu.yml logs --tail 10 backend

echo ""
print_success "Database credentials updated successfully!"
print_status "Username: adam2025man"
print_status "Password: adam2025"
print_status "All services should now be able to connect to the database." 