#!/bin/bash

# Restore final123.sql to VPS Database
echo "🔄 Starting final123.sql restore on VPS..."

# Check if final123.sql file exists
if [ ! -f "final123.sql" ]; then
    echo "❌ final123.sql not found!"
    echo "📝 Please copy the final123.sql file to this directory first."
    exit 1
fi

echo "📊 Found final123.sql file:"
ls -lh final123.sql

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

# Start PostgreSQL 15
echo "🚀 Starting PostgreSQL 15..."
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

# Copy final123.sql to container
echo "📁 Copying final123.sql to container..."
docker cp final123.sql temp-postgres:/tmp/final123.sql

# Restore the SQL file
echo "📥 Restoring final123.sql..."
docker exec temp-postgres psql -U postgres -d chatting_platform -f /tmp/final123.sql

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
SELECT 'tally_submissions', COUNT(*) FROM tally_submissions
UNION ALL
SELECT 'admin_users', COUNT(*) FROM admin_users;
"

# Stop temp container
echo "🛑 Stopping temporary container..."
docker stop temp-postgres
docker rm temp-postgres

# Update docker-compose to use PostgreSQL 15
echo "🔧 Updating docker-compose to use PostgreSQL 15..."
sed -i 's/postgres:17/postgres:15/g' docker-compose.prod.yml

# Start all services
echo "🚀 Starting all services..."
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

echo "✅ final123.sql restore completed!"
echo "🌐 Your application should be available shortly."
echo "📝 All your original data should now be restored."