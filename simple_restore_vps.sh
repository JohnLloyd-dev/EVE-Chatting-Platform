#!/bin/bash

# Simple VPS Database Restore Script
echo "🔄 Starting simple VPS database restore..."

# Stop all containers
echo "🛑 Stopping all containers..."
docker compose -f docker-compose.prod.yml --env-file .env.prod down

# Remove postgres volume
echo "🗑️ Removing postgres volume..."
docker volume rm eve-chatting-platform_postgres_data 2>/dev/null || true

# Create network if it doesn't exist
echo "🌐 Creating network..."
docker network create eve-chatting-platform_default 2>/dev/null || true

# Start only postgres with basic configuration
echo "🚀 Starting PostgreSQL with basic config..."
docker run -d \
  --name temp-postgres \
  --network eve-chatting-platform_default \
  -e POSTGRES_DB=chatting_platform \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres123 \
  -v eve-chatting-platform_postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:16

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to start..."
sleep 45

# Check if container is running
if ! docker ps | grep temp-postgres; then
    echo "❌ PostgreSQL container failed to start. Checking logs..."
    docker logs temp-postgres
    exit 1
fi

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

# Run basic schema setup
echo "🔧 Setting up basic schema..."
docker exec temp-postgres psql -U postgres -d chatting_platform -c "
-- Create extensions
CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";

-- Create basic tables if they don't exist
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tally_response_id VARCHAR(255) NOT NULL UNIQUE,
    tally_respondent_id VARCHAR(255) NOT NULL,
    tally_form_id VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_blocked BOOLEAN DEFAULT false,
    last_active TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ai_responses_enabled BOOLEAN DEFAULT true,
    user_code VARCHAR(50),
    device_id VARCHAR(255),
    user_type VARCHAR(50) DEFAULT 'regular'
);

CREATE TABLE IF NOT EXISTS admin_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    is_user BOOLEAN NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tally_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    submission_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS system_prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    content TEXT,
    is_active BOOLEAN DEFAULT false,
    admin_id UUID REFERENCES admin_users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id UUID REFERENCES users(id),
    head_prompt TEXT,
    rule_prompt TEXT,
    created_by UUID
);

CREATE TABLE IF NOT EXISTS active_ai_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(255) NOT NULL,
    session_id UUID REFERENCES chat_sessions(id),
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_cancelled BOOLEAN DEFAULT false
);

CREATE TABLE IF NOT EXISTS admin_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_id UUID REFERENCES admin_users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"

# Restore the database
echo "📥 Restoring database data..."
docker exec temp-postgres pg_restore -U postgres -d chatting_platform --verbose --no-owner --no-privileges --data-only /tmp/backup_for_vps.sql

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
SELECT 'active_ai_tasks', COUNT(*) FROM active_ai_tasks;
"

# Stop temp container
echo "🛑 Stopping temporary container..."
docker stop temp-postgres
docker rm temp-postgres

# Start all services normally
echo "🚀 Starting all services..."
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

echo "✅ Database restore completed!"
echo "🌐 Your application should be available shortly."