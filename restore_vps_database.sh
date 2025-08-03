#!/bin/bash

# VPS Database Restore Script
# This script restores the database backup on the VPS

echo "🔄 Starting VPS database restore..."

# Check if backup file exists
if [ ! -f "backup_for_vps.sql" ]; then
    echo "❌ Error: backup_for_vps.sql not found!"
    echo "Make sure you've pulled the latest code with: git pull"
    exit 1
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker compose -f docker-compose.prod.yml --env-file .env.prod down

# Remove old postgres volume to ensure clean start
echo "🗑️ Removing old postgres volume..."
docker volume rm eve_postgres_data 2>/dev/null || true

# Start only postgres and redis first
echo "🚀 Starting PostgreSQL and Redis..."
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d postgres redis

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to start..."
sleep 30

# Wait for container to be fully running (not restarting)
echo "⏳ Waiting for PostgreSQL to stabilize..."
for i in {1..10}; do
    POSTGRES_CONTAINER=$(docker ps --format "table {{.Names}}" | grep postgres | head -1)
    if [ ! -z "$POSTGRES_CONTAINER" ]; then
        # Check if container is running (not restarting)
        STATUS=$(docker inspect --format='{{.State.Status}}' $POSTGRES_CONTAINER)
        if [ "$STATUS" = "running" ]; then
            echo "📋 Found PostgreSQL container: $POSTGRES_CONTAINER (Status: $STATUS)"
            break
        else
            echo "⏳ PostgreSQL container status: $STATUS, waiting..."
            sleep 10
        fi
    else
        echo "⏳ Waiting for PostgreSQL container to appear..."
        sleep 10
    fi
done

# Final check
if [ -z "$POSTGRES_CONTAINER" ]; then
    echo "❌ Error: PostgreSQL container not found!"
    exit 1
fi

# Copy backup file to container
echo "📁 Copying backup file to container..."
docker cp backup_for_vps.sql $POSTGRES_CONTAINER:/tmp/backup_for_vps.sql

# Run migrations first to ensure schema compatibility
echo "🔧 Running database migrations..."
docker cp scripts/migrations/comprehensive_migration.sql $POSTGRES_CONTAINER:/tmp/comprehensive_migration.sql
docker exec $POSTGRES_CONTAINER psql -U postgres -d chatting_platform -f /tmp/comprehensive_migration.sql

# Add missing columns for compatibility
echo "🔧 Adding missing columns..."
docker exec $POSTGRES_CONTAINER psql -U postgres -d chatting_platform -c "
ALTER TABLE users ADD COLUMN IF NOT EXISTS user_code VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS device_id VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS user_type VARCHAR(50) DEFAULT 'regular';
ALTER TABLE system_prompts ADD COLUMN IF NOT EXISTS head_prompt TEXT;
ALTER TABLE system_prompts ADD COLUMN IF NOT EXISTS rule_prompt TEXT;
ALTER TABLE system_prompts ADD COLUMN IF NOT EXISTS created_by UUID;
ALTER TABLE system_prompts ALTER COLUMN content DROP NOT NULL;
"

# Restore the database
echo "📥 Restoring database..."
docker exec $POSTGRES_CONTAINER pg_restore -U postgres -d chatting_platform --verbose --no-owner --no-privileges --clean --if-exists /tmp/backup_for_vps.sql

# Check restoration results
echo "📊 Checking restored data..."
docker exec $POSTGRES_CONTAINER psql -U postgres -d chatting_platform -c "
SELECT 'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'chat_sessions', COUNT(*) FROM chat_sessions
UNION ALL
SELECT 'messages', COUNT(*) FROM messages
UNION ALL
SELECT 'system_prompts', COUNT(*) FROM system_prompts
UNION ALL
SELECT 'tally_submissions', COUNT(*) FROM tally_submissions
UNION ALL
SELECT 'active_ai_tasks', COUNT(*) FROM active_ai_tasks;
"

# Start all services
echo "🚀 Starting all services..."
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

echo "✅ Database restore completed!"
echo "🌐 Your application should be available shortly."
echo ""
echo "Data restored:"
echo "- Users, chat sessions, messages"
echo "- System prompts and tally submissions"
echo "- Active AI tasks"