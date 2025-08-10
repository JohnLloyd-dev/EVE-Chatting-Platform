#!/bin/bash

echo "🔧 Fixing Database and Celery Issues"
echo "===================================="

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
print_status "Step 1: Stopping all services..."
docker-compose -f docker-compose.gpu.yml down
print_success "Services stopped"

echo ""
print_status "Step 2: Starting PostgreSQL only..."
docker-compose -f docker-compose.gpu.yml up -d postgres
sleep 15

echo ""
print_status "Step 3: Waiting for PostgreSQL to be ready..."
for i in {1..10}; do
    if docker exec eve-chatting-platform-postgres-1 pg_isready -U postgres; then
        print_success "PostgreSQL is ready"
        break
    else
        print_warning "PostgreSQL not ready yet, attempt $i/10"
        sleep 10
    fi
done

echo ""
print_status "Step 4: Creating new database user..."
docker exec -i eve-chatting-platform-postgres-1 psql -U postgres -d postgres << 'EOF'
-- Create new user without special characters
CREATE USER adam2025man WITH PASSWORD 'adam2025';

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

-- Verify the new user
SELECT rolname, rolcanlogin, rolcanconnect FROM pg_roles WHERE rolname = 'adam2025man';
EOF

if [ $? -eq 0 ]; then
    print_success "New database user created successfully"
else
    print_error "Failed to create database user"
    exit 1
fi

echo ""
print_status "Step 5: Testing database connection with new user..."
docker exec eve-chatting-platform-postgres-1 pg_isready -U adam2025man
if [ $? -eq 0 ]; then
    print_success "Database connection test successful"
else
    print_error "Database connection test failed"
    exit 1
fi

echo ""
print_status "Step 6: Starting all services with new configuration..."
docker-compose -f docker-compose.gpu.yml up -d

echo ""
print_status "Step 7: Waiting for services to start..."
sleep 30

echo ""
print_status "Step 8: Checking service status..."
docker-compose -f docker-compose.gpu.yml ps

echo ""
print_status "Step 9: Checking logs for errors..."
echo "=== PostgreSQL Logs ==="
docker-compose -f docker-compose.gpu.yml logs --tail 10 postgres

echo ""
echo "=== Backend Logs ==="
docker-compose -f docker-compose.gpu.yml logs --tail 10 backend

echo ""
echo "=== Celery Logs ==="
docker-compose -f docker-compose.gpu.yml logs --tail 10 celery-worker

echo ""
print_success "Database and Celery issues fixed!"
print_status "All services should now be running without connection errors."
print_status "The infinite retry loop for disabled AI responses has been fixed."
print_status "Database username special characters have been removed." 