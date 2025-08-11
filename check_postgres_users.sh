#!/bin/bash

echo "🔍 PostgreSQL Container Diagnostic"
echo "=================================="

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

echo ""
print_status "Step 1: Finding PostgreSQL container..."
POSTGRES_CONTAINER=$(docker ps --format "{{.Names}}" | grep "postgres" | head -1)
if [ -z "$POSTGRES_CONTAINER" ]; then
    print_error "PostgreSQL container not found"
    exit 1
fi
print_success "Found container: $POSTGRES_CONTAINER"

echo ""
print_status "Step 2: Checking container environment variables..."
echo "=== Environment Variables ==="
docker exec "$POSTGRES_CONTAINER" env | grep -E "(POSTGRES|PG)" || echo "No PostgreSQL environment variables found"

echo ""
print_status "Step 3: Checking what users exist in PostgreSQL..."
echo "=== Attempting to list users ==="

# Try different approaches to connect and list users
for user in "postgres" "admin" "root" "postgresql" "adam@2025@man"; do
    echo "Trying user: $user"
    if docker exec "$POSTGRES_CONTAINER" pg_isready -U "$user" 2>/dev/null; then
        print_success "User '$user' can connect!"
        echo "Listing all users with '$user':"
        docker exec "$POSTGRES_CONTAINER" psql -U "$user" -d postgres -c "\du" 2>/dev/null || echo "Failed to list users"
        break
    else
        echo "User '$user' cannot connect"
    fi
done

echo ""
print_status "Step 4: Checking container logs..."
echo "=== Container Logs (last 20 lines) ==="
docker logs "$POSTGRES_CONTAINER" --tail 20

echo ""
print_status "Step 5: Checking container inspect..."
echo "=== Container Configuration ==="
docker inspect "$POSTGRES_CONTAINER" | grep -A 10 -B 10 "POSTGRES" || echo "No PostgreSQL config found in inspect"

echo ""
print_status "Diagnostic completed. Check the output above to understand your PostgreSQL setup." 