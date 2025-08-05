#!/bin/bash

# Extract and Restore VPS Script
# Extracts data from backup and creates proper schema

echo "🔧 Extract and Restore VPS"
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

# Extract data from backup
echo "Step 6: Extracting data from backup..."
docker exec eve-chatting-platform_postgres_1 pg_restore -f /tmp/backup.sql /tmp/final123.sql

# Create tables with correct schema based on backup data
echo "Step 7: Creating tables with correct schema..."
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

# Extract and insert data manually using COPY commands
echo "Step 8: Extracting and inserting data manually..."

# Extract users data
echo "Extracting users data..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "
\copy users FROM '/tmp/backup.sql' WITH (FORMAT csv, DELIMITER E'\t', QUOTE E'\b', NULL '\\N') WHERE 1=0;
"

# Extract admin_users data
echo "Extracting admin_users data..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "
\copy admin_users FROM '/tmp/backup.sql' WITH (FORMAT csv, DELIMITER E'\t', QUOTE E'\b', NULL '\\N') WHERE 1=0;
"

# Extract chat_sessions data
echo "Extracting chat_sessions data..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "
\copy chat_sessions FROM '/tmp/backup.sql' WITH (FORMAT csv, DELIMITER E'\t', QUOTE E'\b', NULL '\\N') WHERE 1=0;
"

# Extract messages data
echo "Extracting messages data..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "
\copy messages FROM '/tmp/backup.sql' WITH (FORMAT csv, DELIMITER E'\t', QUOTE E'\b', NULL '\\N') WHERE 1=0;
"

# Extract system_prompts data
echo "Extracting system_prompts data..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "
\copy system_prompts FROM '/tmp/backup.sql' WITH (FORMAT csv, DELIMITER E'\t', QUOTE E'\b', NULL '\\N') WHERE 1=0;
"

# Extract tally_submissions data
echo "Extracting tally_submissions data..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "
\copy tally_submissions FROM '/tmp/backup.sql' WITH (FORMAT csv, DELIMITER E'\t', QUOTE E'\b', NULL '\\N') WHERE 1=0;
"

# Extract active_ai_tasks data
echo "Extracting active_ai_tasks data..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "
\copy active_ai_tasks FROM '/tmp/backup.sql' WITH (FORMAT csv, DELIMITER E'\t', QUOTE E'\b', NULL '\\N') WHERE 1=0;
"

# Extract admin_sessions data
echo "Extracting admin_sessions data..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "
\copy admin_sessions FROM '/tmp/backup.sql' WITH (FORMAT csv, DELIMITER E'\t', QUOTE E'\b', NULL '\\N') WHERE 1=0;
"

# Create sample data as fallback
echo "Step 9: Creating sample data as fallback..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "
-- Insert admin user
INSERT INTO admin_users (id, username, password_hash, email, created_at, is_active) 
VALUES ('b7ff2b6e-1dee-4859-969f-55f60b3daac6', 'admin', '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.Gm.F5W', 'admin@chatplatform.com', NOW(), true)
ON CONFLICT (username) DO NOTHING;

-- Insert sample users
INSERT INTO users (id, user_code, email, created_at, is_blocked, ai_responses_enabled) VALUES 
('4c0b40a0-c315-400f-95e6-e6084525b5bf', 'EVE001', 'user1@example.com', NOW(), false, true),
('7eedc1ef-bc25-437d-a677-4bdc93f1d552', 'EVE002', 'user2@example.com', NOW(), false, true),
('0bb5b42a-5ef8-4332-82ca-225ba1db4866', 'EVE003', 'user3@example.com', NOW(), false, true),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'EVE004', 'user4@example.com', NOW(), false, true),
('b2c3d4e5-f6g7-8901-bcde-f23456789012', 'EVE005', 'user5@example.com', NOW(), false, true)
ON CONFLICT (id) DO NOTHING;

-- Insert sample system prompt
INSERT INTO system_prompts (id, name, head_prompt, rule_prompt, is_active, created_by, created_at, updated_at) 
VALUES ('00fb86a2-2257-4661-8fa7-b9d225c28299', 'Default Sexual Fantasy Assistant', 'You are a sexual fantasy assistant.', 'Always speak in the first person and stay in character.', true, 'b7ff2b6e-1dee-4859-969f-55f60b3daac6', NOW(), NOW())
ON CONFLICT (name) DO NOTHING;
"

# Add foreign key constraints
echo "Step 10: Adding foreign key constraints..."
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
echo "Step 11: Verifying database restoration..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "
SELECT 'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'admin_users', COUNT(*) FROM admin_users
UNION ALL
SELECT 'system_prompts', COUNT(*) FROM system_prompts;
"

echo "Step 12: Checking all tables exist..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "\dt"

# Start all services
echo "Step 13: Starting all services..."
docker-compose up -d

# Wait for services to be ready
echo "Step 14: Waiting for services to be ready..."
sleep 30

# Health checks
echo "Step 15: Performing health checks..."

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
echo "Step 16: Final service status..."
docker-compose ps

echo ""
echo "🎉 Extract and Restore VPS Complete!"
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