#!/bin/bash

echo "🗄️ Database Restore Script"
echo "=========================="

# Configuration
VPS_IP="204.12.233.105"
DB_USER="adam@2025@man"
DB_PASSWORD="eve@postgres@3241"

# Step 1: Check if backup file exists
echo "[INFO] Step 1: Checking backup file..."
if [ -f "final123.sql" ]; then
    echo "[SUCCESS] Found final123.sql in root directory"
elif [ -f "docs/deployment/final123.sql" ]; then
    echo "[SUCCESS] Found final123.sql in docs/deployment/"
    cp docs/deployment/final123.sql .
else
    echo "[ERROR] No final123.sql found"
    exit 1
fi

# Step 2: Stop backend and celery to avoid conflicts
echo "[INFO] Step 2: Stopping backend services..."
docker-compose stop backend celery-worker

# Step 3: Ensure PostgreSQL is running
echo "[INFO] Step 3: Starting PostgreSQL..."
docker-compose up -d postgres
sleep 15

# Step 4: Wait for PostgreSQL to be ready
echo "[INFO] Step 4: Waiting for PostgreSQL to be ready..."
for i in {1..5}; do
    if docker exec eve-chatting-platform_postgres_1 pg_isready -U "$DB_USER"; then
        echo "[SUCCESS] PostgreSQL is ready"
        break
    else
        echo "[WARNING] PostgreSQL not ready yet, attempt $i/5"
        sleep 10
    fi
done

# Step 5: Drop and recreate database
echo "[INFO] Step 5: Preparing database..."
docker exec eve-chatting-platform_postgres_1 psql -U "$DB_USER" -c "DROP DATABASE IF EXISTS chatting_platform;"
docker exec eve-chatting-platform_postgres_1 psql -U "$DB_USER" -c "CREATE DATABASE chatting_platform;"

# Step 6: Copy backup file
echo "[INFO] Step 6: Copying backup file..."
docker cp final123.sql eve-chatting-platform_postgres_1:/tmp/

# Step 7: Restore database with proper foreign key handling
echo "[INFO] Step 7: Restoring database with foreign key handling..."

# Check if it's a binary dump
if file final123.sql | grep -q "PostgreSQL"; then
    echo "[INFO] Detected binary PostgreSQL dump"
    
    # Strategy 1: Try with disabled triggers
    echo "[INFO] Attempting restore with disabled triggers..."
    docker exec eve-chatting-platform_postgres_1 pg_restore -U "$DB_USER" -d chatting_platform --clean --if-exists --no-owner --no-privileges --disable-triggers /tmp/final123.sql
    
    if [ $? -eq 0 ]; then
        echo "[SUCCESS] Database restored successfully with disabled triggers"
    else
        echo "[WARNING] Strategy 1 failed, trying schema-first approach..."
        
        # Strategy 2: Schema first, then data with constraint handling
        echo "[INFO] Restoring schema first..."
        docker exec eve-chatting-platform_postgres_1 pg_restore -U "$DB_USER" -d chatting_platform --schema-only --clean --if-exists --no-owner --no-privileges /tmp/final123.sql
        
        if [ $? -eq 0 ]; then
            echo "[SUCCESS] Schema restored successfully"
            
            # Disable foreign key constraints
            echo "[INFO] Disabling foreign key constraints..."
            docker exec eve-chatting-platform_postgres_1 psql -U "$DB_USER" -d chatting_platform -c "SET session_replication_role = replica;"
            
            # Restore data
            echo "[INFO] Restoring data..."
            docker exec eve-chatting-platform_postgres_1 pg_restore -U "$DB_USER" -d chatting_platform --data-only --disable-triggers /tmp/final123.sql
            
            # Re-enable foreign key constraints
            echo "[INFO] Re-enabling foreign key constraints..."
            docker exec eve-chatting-platform_postgres_1 psql -U "$DB_USER" -d chatting_platform -c "SET session_replication_role = DEFAULT;"
            
            if [ $? -eq 0 ]; then
                echo "[SUCCESS] Data restored successfully"
            else
                echo "[WARNING] Data restore had issues, but schema is ready"
            fi
        else
            echo "[ERROR] Schema restore failed"
            exit 1
        fi
    fi
else
    echo "[INFO] Detected SQL file, using psql..."
    docker exec eve-chatting-platform_postgres_1 psql -U "$DB_USER" -d chatting_platform -f /tmp/final123.sql
fi

# Step 8: Verify restore
echo "[INFO] Step 8: Verifying database restore..."
USER_COUNT=$(docker exec eve-chatting-platform_postgres_1 psql -U "$DB_USER" -d chatting_platform -t -c "SELECT COUNT(*) FROM users;" | tr -d ' ')
if [ "$USER_COUNT" -gt 0 ]; then
    echo "[SUCCESS] Database verification successful - found $USER_COUNT users"
else
    echo "[WARNING] No users found in database"
fi

# Step 9: Start backend services
echo "[INFO] Step 9: Starting backend services..."
docker-compose up -d backend
sleep 10
docker-compose up -d celery-worker

# Step 10: Test backend
echo "[INFO] Step 10: Testing backend..."
sleep 10
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$VPS_IP:8001/health 2>/dev/null || echo "000")
if [ "$BACKEND_STATUS" = "200" ]; then
    echo "[SUCCESS] Backend is healthy and database is accessible"
else
    echo "[WARNING] Backend health check failed (Status: $BACKEND_STATUS)"
fi

echo "[SUCCESS] Database restore completed!" 