#!/bin/bash

echo "🔧 Fix PostgreSQL Connection Issues"
echo "=================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

echo ""
echo "Step 1: Finding PostgreSQL container..."
POSTGRES_CONTAINER=$(docker ps --format "{{.Names}}" | grep "postgres" | head -1)
if [ -z "$POSTGRES_CONTAINER" ]; then
    echo "PostgreSQL container not found"
    exit 1
fi
echo "Found container: $POSTGRES_CONTAINER"

echo ""
echo "Step 2: Checking container environment..."
POSTGRES_USER=$(docker exec "$POSTGRES_CONTAINER" env | grep "POSTGRES_USER" | cut -d'=' -f2)
POSTGRES_PASSWORD=$(docker exec "$POSTGRES_CONTAINER" env | grep "POSTGRES_PASSWORD" | cut -d'=' -f2)
POSTGRES_DB=$(docker exec "$POSTGRES_CONTAINER" env | grep "POSTGRES_DB" | cut -d'=' -f2)

echo "Container expects:"
echo "  User: $POSTGRES_USER"
echo "  Password: $POSTGRES_PASSWORD"
echo "  Database: $POSTGRES_DB"

echo ""
echo "Step 3: Testing direct psql connection..."
if docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT version();" 2>/dev/null; then
    echo "Direct connection successful!"
else
    echo "Direct connection failed, checking what's wrong..."
    
    echo ""
    echo "Step 4: Checking if database exists..."
    if docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -l 2>/dev/null; then
        echo "Database listing successful"
    else
        echo "Cannot list databases, checking if database exists..."
        
        # Try to connect to postgres database first
        if docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d postgres -c "SELECT 1;" 2>/dev/null; then
            echo "Can connect to postgres database"
            
            # Check if our target database exists
            if docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d postgres -c "SELECT datname FROM pg_database WHERE datname='$POSTGRES_DB';" 2>/dev/null | grep -q "$POSTGRES_DB"; then
                echo "Database '$POSTGRES_DB' exists"
            else
                echo "Database '$POSTGRES_DB' does not exist, creating it..."
                docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE \"$POSTGRES_DB\";"
            fi
        else
            echo "Cannot connect to any database as '$POSTGRES_USER'"
            
            echo ""
            echo "Step 5: Attempting to fix user permissions..."
            # Try to connect as postgres superuser
            if docker exec "$POSTGRES_CONTAINER" psql -U postgres -d postgres -c "SELECT 1;" 2>/dev/null; then
                echo "Connected as postgres superuser, fixing user..."
                docker exec "$POSTGRES_CONTAINER" psql -U postgres -d postgres << EOF
ALTER USER "$POSTGRES_USER" WITH PASSWORD '$POSTGRES_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE "$POSTGRES_DB" TO "$POSTGRES_USER";
ALTER USER "$POSTGRES_USER" CREATEDB;
EOF
            else
                echo "Cannot connect as postgres superuser either"
                echo "This suggests the container needs recreation"
                exit 1
            fi
        fi
    fi
fi

echo ""
echo "Step 6: Final connection test..."
if docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" 2>/dev/null; then
    echo "Final connection test successful!"
else
    echo "Final connection test failed"
    exit 1
fi

echo ""
echo "PostgreSQL connection issues fixed!"
echo "Username: $POSTGRES_USER"
echo "Password: $POSTGRES_PASSWORD"
echo "Database: $POSTGRES_DB"
echo "You can now restart your services:"
echo "  docker-compose -f docker-compose.gpu.yml restart backend celery-worker" 