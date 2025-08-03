#!/bin/bash

# Proper VPS Restoration Script
# Correctly restores all data from final123.sql

echo "🔧 Proper VPS Restoration"
echo "========================="

# Check if PostgreSQL is running
echo "Step 1: Checking PostgreSQL status..."
if docker exec eve-chatting-platform_postgres_1 pg_isready -U postgres >/dev/null 2>&1; then
    echo "✅ PostgreSQL is running!"
else
    echo "❌ PostgreSQL is not running. Exiting..."
    exit 1
fi

# Stop all services except PostgreSQL
echo "Step 2: Stopping services..."
docker-compose stop backend celery-worker frontend

# Drop and recreate database
echo "Step 3: Dropping and recreating database..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -c "DROP DATABASE IF EXISTS chatting_platform;"
docker exec eve-chatting-platform_postgres_1 psql -U postgres -c "CREATE DATABASE chatting_platform;"

# Create extension
echo "Step 4: Creating UUID extension..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"

# Copy final123.sql to container
echo "Step 5: Copying final123.sql to container..."
docker cp final123.sql eve-chatting-platform_postgres_1:/tmp/final123.sql

# Convert backup to SQL format
echo "Step 6: Converting backup to SQL format..."
docker exec eve-chatting-platform_postgres_1 pg_restore -f /tmp/backup.sql /tmp/final123.sql

# Extract only the schema creation part
echo "Step 7: Creating database schema..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "
CREATE TABLE users (
    id UUID PRIMARY KEY,
    tally_response_id VARCHAR(255),
    tally_respondent_id VARCHAR(255),
    tally_form_id VARCHAR(255),
    email VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE,
    is_blocked BOOLEAN,
    last_active TIMESTAMP WITH TIME ZONE,
    user_code VARCHAR(20),
    device_id VARCHAR(255),
    user_type VARCHAR(50),
    ai_responses_enabled BOOLEAN
);

CREATE TABLE admin_users (
    id UUID PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN
);

CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY,
    user_id UUID,
    scenario_prompt TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN
);

CREATE TABLE messages (
    id UUID PRIMARY KEY,
    session_id UUID,
    content TEXT NOT NULL,
    is_from_user BOOLEAN NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE,
    is_admin_intervention BOOLEAN,
    admin_id UUID
);

CREATE TABLE admin_sessions (
    id UUID PRIMARY KEY,
    admin_id UUID,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN
);

CREATE TABLE tally_submissions (
    id UUID PRIMARY KEY,
    user_id UUID,
    form_data JSONB NOT NULL,
    processed_scenario TEXT,
    created_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE system_prompts (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    head_prompt TEXT NOT NULL,
    rule_prompt TEXT NOT NULL,
    is_active BOOLEAN,
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    user_id UUID
);

CREATE TABLE active_ai_tasks (
    id UUID PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    session_id UUID,
    user_id UUID,
    created_at TIMESTAMP WITH TIME ZONE,
    is_cancelled BOOLEAN
);
"

# Extract and insert data manually
echo "Step 8: Extracting data from backup..."
docker exec eve-chatting-platform_postgres_1 pg_restore -U postgres -d chatting_platform --data-only --disable-triggers /tmp/final123.sql

# Add foreign key constraints
echo "Step 9: Adding foreign key constraints..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "
ALTER TABLE chat_sessions ADD CONSTRAINT chat_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE messages ADD CONSTRAINT messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE;
ALTER TABLE tally_submissions ADD CONSTRAINT tally_submissions_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE active_ai_tasks ADD CONSTRAINT active_ai_tasks_session_id_fkey FOREIGN KEY (session_id) REFERENCES chat_sessions(id);
ALTER TABLE active_ai_tasks ADD CONSTRAINT active_ai_tasks_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);
ALTER TABLE admin_sessions ADD CONSTRAINT admin_sessions_admin_id_fkey FOREIGN KEY (admin_id) REFERENCES admin_users(id) ON DELETE CASCADE;
ALTER TABLE system_prompts ADD CONSTRAINT system_prompts_created_by_fkey FOREIGN KEY (created_by) REFERENCES admin_users(id);
ALTER TABLE system_prompts ADD CONSTRAINT system_prompts_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);
"

# Verify all tables and data
echo "Step 10: Verifying database restoration..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "
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
SELECT 'admin_users', COUNT(*) FROM admin_users
UNION ALL
SELECT 'active_ai_tasks', COUNT(*) FROM active_ai_tasks
UNION ALL
SELECT 'admin_sessions', COUNT(*) FROM admin_sessions;
"

echo "Step 11: Checking all tables exist..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "\dt"

# Start all services
echo "Step 12: Starting all services..."
docker-compose up -d

# Wait for services to be ready
echo "Step 13: Waiting for services to be ready..."
sleep 30

# Health checks
echo "Step 14: Performing health checks..."

# Check backend
if curl -s http://localhost:8001/health >/dev/null; then
    echo "✅ Backend is healthy!"
else
    echo "❌ Backend health check failed"
fi

# Check frontend
if curl -s -I http://localhost:3000 | grep -q "200\|302"; then
    echo "✅ Frontend is responding!"
else
    echo "⚠️ Frontend may still be starting up"
fi

# Final status
echo "Step 15: Final service status..."
docker-compose ps

echo ""
echo "🎉 Proper VPS Restoration Complete!"
echo ""
echo "📋 Service Status:"
echo "   Backend API: http://your-vps-ip:8001"
echo "   Frontend: http://your-vps-ip:3000"
echo "   Admin Dashboard: http://your-vps-ip:3000/admin"
echo ""
echo "🔐 Admin Credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "📝 Useful Commands:"
echo "   View logs: docker-compose logs"
echo "   Check database: docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c 'SELECT COUNT(*) FROM users;'"
echo "   Restart services: docker-compose restart" 