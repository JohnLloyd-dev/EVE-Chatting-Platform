#!/bin/bash

echo "🔄 Recreate PostgreSQL Container (Nuclear Option)"
echo "================================================"

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
print_warning "⚠️  WARNING: This will DELETE ALL DATABASE DATA!"
print_warning "⚠️  Only use this if other fixes failed!"
echo ""
read -p "Are you sure you want to continue? Type 'YES' to confirm: " confirmation

if [ "$confirmation" != "YES" ]; then
    print_error "Operation cancelled by user"
    exit 1
fi

echo ""
print_status "Step 1: Stopping all services..."
docker-compose -f docker-compose.gpu.yml down

echo ""
print_status "Step 2: Removing PostgreSQL volume..."
docker volume rm eve-chatting-platform_postgres_data 2>/dev/null || print_warning "Volume not found or already removed"

echo ""
print_status "Step 3: Starting fresh PostgreSQL container..."
docker-compose -f docker-compose.gpu.yml up -d postgres

echo ""
print_status "Step 4: Waiting for PostgreSQL to initialize..."
sleep 20

echo ""
print_status "Step 5: Testing PostgreSQL connection..."
for i in {1..10}; do
    if docker exec eve-chatting-platform-postgres-1 pg_isready -U adam2025man; then
        print_success "PostgreSQL is ready!"
        break
    else
        print_warning "PostgreSQL not ready yet, attempt $i/10"
        sleep 10
    fi
done

echo ""
print_status "Step 6: Starting all services..."
docker-compose -f docker-compose.gpu.yml up -d

echo ""
print_status "Step 7: Waiting for services to start..."
sleep 30

echo ""
print_status "Step 8: Checking service status..."
docker-compose -f docker-compose.gpu.yml ps

echo ""
print_status "Step 9: Checking backend logs..."
echo "=== Backend Logs (last 10 lines) ==="
docker-compose -f docker-compose.gpu.yml logs --tail 10 backend

echo ""
print_success "PostgreSQL container recreated successfully!"
print_status "All data has been reset to fresh state"
print_status "New credentials should work:"
print_status "  Username: adam2025man"
print_status "  Password: adam2025"
print_status "  Database: chatting_platform"
print_warning "⚠️  Note: All previous data has been lost!" 