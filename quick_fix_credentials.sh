#!/bin/bash

echo "🔐 Quick Fix: Update Database User Password"
echo "============================================"

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
print_status "Step 2: Updating user password..."
docker exec "$POSTGRES_CONTAINER" psql -U postgres -d postgres -c "ALTER USER \"adam@2025@man\" WITH PASSWORD 'adam2025';"

if [ $? -eq 0 ]; then
    print_success "Password updated successfully"
else
    print_error "Failed to update password"
    exit 1
fi

echo ""
print_status "Step 3: Testing connection with new password..."
if docker exec "$POSTGRES_CONTAINER" pg_isready -U "adam@2025@man"; then
    print_success "Connection test successful"
else
    print_error "Connection test failed"
    exit 1
fi

echo ""
print_status "Step 4: Restarting services..."
docker-compose -f docker-compose.gpu.yml restart backend celery-worker

echo ""
print_success "Quick fix completed!"
print_status "User: adam@2025@man"
print_status "New Password: adam2025"
print_status "Services restarted. Check logs for connection success." 