#!/bin/bash

# VPS Database Restore Fix Script
echo "🔄 Starting VPS database restore fix..."

# Stop all containers
echo "🛑 Stopping all containers..."
docker compose -f docker-compose.prod.yml --env-file .env.prod down

# Clean up any existing temp containers
docker stop temp-postgres 2>/dev/null || true
docker rm temp-postgres 2>/dev/null || true

# Remove postgres volume
echo "🗑️ Removing postgres volume..."
docker volume rm eve-chatting-platform_postgres_data 2>/dev/null || true

# Create network if it doesn't exist
echo "🌐 Creating network..."
docker network create eve-chatting-platform_default 2>/dev/null || true

# Start PostgreSQL 15 (same version as backup)
echo "🚀 Starting PostgreSQL 15 (matching backup version)..."
docker run -d \
  --name temp-postgres \
  --network eve-chatting-platform_default \
  -e POSTGRES_DB=chatting_platform \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres123 \
  -v eve-chatting-platform_postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:15

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to start..."
sleep 30

# Test connection
echo "🔍 Testing PostgreSQL connection..."
for i in {1..10}; do
    if docker exec temp-postgres pg_isready -U postgres; then
        echo "✅ PostgreSQL is ready!"
        break
    else
        echo "⏳ Waiting for PostgreSQL to be ready... ($i/10)"
        sleep 5
    fi
done

# Copy backup file
echo "📁 Copying backup file..."
docker cp backup_for_vps.sql temp-postgres:/tmp/backup_for_vps.sql

# Restore the database (should work with matching version)
echo "📥 Restoring database with PostgreSQL 15..."
docker exec temp-postgres pg_restore -U postgres -d chatting_platform --verbose --no-owner --no-privileges /tmp/backup_for_vps.sql

# Check results
echo "📊 Checking restored data..."
docker exec temp-postgres psql -U postgres -d chatting_platform -c "
SELECT 'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'chat_sessions', COUNT(*) FROM chat_sessions
UNION ALL
SELECT 'messages', COUNT(*) FROM messages
UNION ALL
SELECT 'system_prompts', COUNT(*) FROM system_prompts
UNION ALL
SELECT 'tally_submissions', COUNT(*) FROM tally_submissions;
"

# Stop temp container
echo "🛑 Stopping temporary container..."
docker stop temp-postgres
docker rm temp-postgres

# Now update docker-compose to use PostgreSQL 15
echo "🔧 Updating docker-compose to use PostgreSQL 15..."
sed -i 's/postgres:17/postgres:15/g' docker-compose.prod.yml

# Start all services with PostgreSQL 15
echo "🚀 Starting all services with PostgreSQL 15..."
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

echo "✅ Database restore completed with PostgreSQL 15!"
echo "🌐 Your application should be available shortly."