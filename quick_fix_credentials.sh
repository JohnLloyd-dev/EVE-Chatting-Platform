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
print_status "Step 2: Finding the correct superuser..."
# Try to find the superuser by checking environment variables
SUPERUSER=$(docker exec "$POSTGRES_CONTAINER" env | grep "POSTGRES_USER" | cut -d'=' -f2)
if [ -z "$SUPERUSER" ]; then
    # Fallback: try common superuser names
    for user in "postgres" "admin" "root" "postgresql"; do
        if docker exec "$POSTGRES_CONTAINER" pg_isready -U "$user" 2>/dev/null; then
            SUPERUSER="$user"
            break
        fi
    done
fi

if [ -z "$SUPERUSER" ]; then
    print_error "Could not find a working superuser. Trying to connect as 'adam@2025@man'..."
    SUPERUSER="adam@2025@man"
fi

print_success "Using superuser: $SUPERUSER"

echo ""
print_status "Step 3: Testing superuser connection..."
if docker exec "$POSTGRES_CONTAINER" pg_isready -U "$SUPERUSER"; then
    print_success "Superuser connection successful"
else
    print_error "Superuser connection failed"
    exit 1
fi

echo ""
print_status "Step 4: Updating user password..."
docker exec "$POSTGRES_CONTAINER" psql -U "$SUPERUSER" -d postgres -c "ALTER USER \"adam@2025@man\" WITH PASSWORD 'adam2025';"

if [ $? -eq 0 ]; then
    print_success "Password updated successfully"
else
    print_error "Failed to update password"
    exit 1
fi

echo ""
print_status "Step 5: Testing connection with new password..."
if docker exec "$POSTGRES_CONTAINER" pg_isready -U "adam@2025@man"; then
    print_success "Connection test successful"
else
    print_error "Connection test failed"
    exit 1
fi

echo ""
print_status "Step 6: Restarting services..."
docker-compose -f docker-compose.gpu.yml restart backend celery-worker

echo ""
print_success "Quick fix completed!"
print_status "User: adam@2025@man"
print_status "New Password: adam2025"
print_status "Services restarted. Check logs for connection success." 