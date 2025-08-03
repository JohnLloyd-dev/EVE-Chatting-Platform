#!/bin/bash

# Manual VPS Database Restoration Script
# Run this step by step if the automated script fails

echo "🔧 Manual VPS Database Restoration"
echo "=================================="

echo "Step 1: Stop all containers"
docker stop $(docker ps -q) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true

echo "Step 2: Clean up volumes"
docker volume rm $(docker volume ls -q) 2>/dev/null || true

echo "Step 3: Start PostgreSQL 17 (compatible with your backup)"
docker run -d \
  --name temp-postgres \
  -e POSTGRES_DB=chatting_platform \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres123 \
  -v postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:17

echo "Step 4: Wait for PostgreSQL to start..."
sleep 30

echo "Step 5: Copy final123.sql to container"
docker cp final123.sql temp-postgres:/tmp/final123.sql

echo "Step 6: Create database schema"
docker exec temp-postgres psql -U postgres -d chatting_platform -c "
CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";

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

echo "Step 7: Try to restore data (multiple methods)"
echo "Method 1: Direct pg_restore"
docker exec temp-postgres pg_restore -U postgres -d chatting_platform --data-only /tmp/final123.sql || echo "Method 1 failed"

echo "Method 2: Convert to SQL and restore"
docker exec temp-postgres pg_restore -f /tmp/backup.sql /tmp/final123.sql && \
docker exec temp-postgres psql -U postgres -d chatting_platform -f /tmp/backup.sql || echo "Method 2 failed"

echo "Method 3: Create sample data if restore fails"
docker exec temp-postgres psql -U postgres -d chatting_platform -c "
INSERT INTO admin_users (id, username, password_hash, email, created_at, is_active) VALUES 
('b7ff2b6e-1dee-4859-969f-55f60b3daac6', 'admin', '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.Gm.F5W', 'admin@chatplatform.com', NOW(), true);

INSERT INTO users (id, user_code, email, created_at, is_blocked, ai_responses_enabled) VALUES 
('4c0b40a0-c315-400f-95e6-e6084525b5bf', 'EVE001', 'user1@example.com', NOW(), false, true),
('7eedc1ef-bc25-437d-a677-4bdc93f1d552', 'EVE002', 'user2@example.com', NOW(), false, true),
('0bb5b42a-5ef8-4332-82ca-225ba1db4866', 'EVE003', 'user3@example.com', NOW(), false, true);

INSERT INTO system_prompts (id, name, head_prompt, rule_prompt, is_active, created_by, created_at, updated_at) VALUES 
('00fb86a2-2257-4661-8fa7-b9d225c28299', 'Default Sexual Fantasy Assistant', 'You are a sexual fantasy assistant.', 'Always speak in the first person and stay in character.', true, 'b7ff2b6e-1dee-4859-969f-55f60b3daac6', NOW(), NOW());
"

echo "Step 8: Add foreign key constraints"
docker exec temp-postgres psql -U postgres -d chatting_platform -c "
ALTER TABLE chat_sessions ADD CONSTRAINT chat_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE messages ADD CONSTRAINT messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE;
ALTER TABLE tally_submissions ADD CONSTRAINT tally_submissions_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE active_ai_tasks ADD CONSTRAINT active_ai_tasks_session_id_fkey FOREIGN KEY (session_id) REFERENCES chat_sessions(id);
ALTER TABLE active_ai_tasks ADD CONSTRAINT active_ai_tasks_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);
ALTER TABLE admin_sessions ADD CONSTRAINT admin_sessions_admin_id_fkey FOREIGN KEY (admin_id) REFERENCES admin_users(id) ON DELETE CASCADE;
ALTER TABLE system_prompts ADD CONSTRAINT system_prompts_created_by_fkey FOREIGN KEY (created_by) REFERENCES admin_users(id);
ALTER TABLE system_prompts ADD CONSTRAINT system_prompts_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);
"

echo "Step 9: Verify data"
docker exec temp-postgres psql -U postgres -d chatting_platform -c "
SELECT 'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'admin_users', COUNT(*) FROM admin_users
UNION ALL
SELECT 'system_prompts', COUNT(*) FROM system_prompts;
"

echo "Step 10: Stop temporary container"
docker stop temp-postgres
docker rm temp-postgres

echo "Step 11: Start all services"
docker-compose -f docker-compose.prod.yml up -d

echo "✅ Manual restoration complete!"
echo "Check the results above to see if data was restored successfully." 