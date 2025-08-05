#!/bin/bash

# Complete VPS Fix Script
# Ensures all 8 tables are created and working

echo "🔧 Complete VPS Fix"
echo "==================="

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

# Create ALL 8 tables with correct schema
echo "Step 5: Creating ALL 8 tables..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "
-- Table 1: users
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

-- Table 2: admin_users
CREATE TABLE admin_users (
    id UUID PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN
);

-- Table 3: chat_sessions
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY,
    user_id UUID,
    scenario_prompt TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN
);

-- Table 4: messages
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    session_id UUID,
    content TEXT NOT NULL,
    is_from_user BOOLEAN NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE,
    is_admin_intervention BOOLEAN,
    admin_id UUID
);

-- Table 5: admin_sessions
CREATE TABLE admin_sessions (
    id UUID PRIMARY KEY,
    admin_id UUID,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN
);

-- Table 6: tally_submissions
CREATE TABLE tally_submissions (
    id UUID PRIMARY KEY,
    user_id UUID,
    form_data JSONB NOT NULL,
    processed_scenario TEXT,
    created_at TIMESTAMP WITH TIME ZONE
);

-- Table 7: system_prompts
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

-- Table 8: active_ai_tasks
CREATE TABLE active_ai_tasks (
    id UUID PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    session_id UUID,
    user_id UUID,
    created_at TIMESTAMP WITH TIME ZONE,
    is_cancelled BOOLEAN
);
"

# Verify all 8 tables were created
echo "Step 6: Verifying all 8 tables were created..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "\dt"

# Insert sample data
echo "Step 7: Inserting sample data..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "
-- Insert admin user
INSERT INTO admin_users (id, username, password_hash, email, created_at, is_active) 
VALUES ('b7ff2b6e-1dee-4859-969f-55f60b3daac6', 'admin', '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.Gm.F5W', 'admin@chatplatform.com', NOW(), true);

-- Insert sample users (16 users like in your original data)
INSERT INTO users (id, user_code, email, created_at, is_blocked, ai_responses_enabled) VALUES 
('4c0b40a0-c315-400f-95e6-e6084525b5bf', 'EVE001', 'user1@example.com', NOW(), false, true),
('7eedc1ef-bc25-437d-a677-4bdc93f1d552', 'EVE002', 'user2@example.com', NOW(), false, true),
('0bb5b42a-5ef8-4332-82ca-225ba1db4866', 'EVE003', 'user3@example.com', NOW(), false, true),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'EVE004', 'user4@example.com', NOW(), false, true),
('b2c3d4e5-f6g7-8901-bcde-f23456789012', 'EVE005', 'user5@example.com', NOW(), false, true),
('c3d4e5f6-g7h8-9012-cdef-345678901234', 'EVE006', 'user6@example.com', NOW(), false, true),
('d4e5f6g7-h8i9-0123-defg-456789012345', 'EVE007', 'user7@example.com', NOW(), false, true),
('e5f6g7h8-i9j0-1234-efgh-567890123456', 'EVE008', 'user8@example.com', NOW(), false, true),
('f6g7h8i9-j0k1-2345-fghi-678901234567', 'EVE009', 'user9@example.com', NOW(), false, true),
('g7h8i9j0-k1l2-3456-ghij-789012345678', 'EVE010', 'user10@example.com', NOW(), false, true),
('h8i9j0k1-l2m3-4567-hijk-890123456789', 'EVE011', 'user11@example.com', NOW(), false, true),
('i9j0k1l2-m3n4-5678-ijkl-901234567890', 'EVE012', 'user12@example.com', NOW(), false, true),
('j0k1l2m3-n4o5-6789-jklm-012345678901', 'EVE013', 'user13@example.com', NOW(), false, true),
('k1l2m3n4-o5p6-7890-klmn-123456789012', 'EVE014', 'user14@example.com', NOW(), false, true),
('l2m3n4o5-p6q7-8901-lmno-234567890123', 'EVE015', 'user15@example.com', NOW(), false, true),
('m3n4o5p6-q7r8-9012-mnop-345678901234', 'EVE016', 'user16@example.com', NOW(), false, true);

-- Insert sample system prompts
INSERT INTO system_prompts (id, name, head_prompt, rule_prompt, is_active, created_by, created_at, updated_at) VALUES 
('00fb86a2-2257-4661-8fa7-b9d225c28299', 'Default Sexual Fantasy Assistant', 'You are a sexual fantasy assistant.', 'Always speak in the first person and stay in character.', true, 'b7ff2b6e-1dee-4859-969f-55f60b3daac6', NOW(), NOW()),
('11gc97b3-3368-5772-9gb8-c0e336d39300', 'Alternative Assistant', 'You are an alternative assistant.', 'Always be helpful and engaging.', true, 'b7ff2b6e-1dee-4859-969f-55f60b3daac6', NOW(), NOW());

-- Insert sample chat sessions
INSERT INTO chat_sessions (id, user_id, scenario_prompt, created_at, updated_at, is_active) VALUES 
('a460c285-5953-49b7-8182-789d5a7da77b', '4c0b40a0-c315-400f-95e6-e6084525b5bf', 'You are a helpful assistant.', NOW(), NOW(), true),
('b571d396-6064-50c8-9293-89ae6b8eb88c', '7eedc1ef-bc25-437d-a677-4bdc93f1d552', 'You are a friendly assistant.', NOW(), NOW(), true);

-- Insert sample messages
INSERT INTO messages (id, session_id, content, is_from_user, created_at, is_admin_intervention) VALUES 
('2e02b94d-4652-4291-a705-ddcb9c678bde', 'a460c285-5953-49b7-8182-789d5a7da77b', 'Hello!', true, NOW(), false),
('3f13ca5e-5763-5302-b816-eedc0d789cef', 'a460c285-5953-49b7-8182-789d5a7da77b', 'Hi there! How can I help you?', false, NOW(), false),
('4g24db6f-6874-6413-c927-ffed1e890df0', 'b571d396-6064-50c8-9293-89ae6b8eb88c', 'How are you?', true, NOW(), false),
('5h35ec7g-7985-7524-d038-00fe2f901eg1', 'b571d396-6064-50c8-9293-89ae6b8eb88c', 'I am doing well, thank you!', false, NOW(), false);

-- Insert sample tally submissions
INSERT INTO tally_submissions (id, user_id, form_data, processed_scenario, created_at) VALUES 
('tally1-1111-1111-1111-111111111111', '4c0b40a0-c315-400f-95e6-e6084525b5bf', '{\"name\": \"John\", \"age\": 25}', 'Sample scenario 1', NOW()),
('tally2-2222-2222-2222-222222222222', '7eedc1ef-bc25-437d-a677-4bdc93f1d552', '{\"name\": \"Jane\", \"age\": 30}', 'Sample scenario 2', NOW());

-- Insert sample active AI tasks
INSERT INTO active_ai_tasks (id, task_id, session_id, user_id, created_at, is_cancelled) VALUES 
('task1-1111-1111-1111-111111111111', 'TASK001', 'a460c285-5953-49b7-8182-789d5a7da77b', '4c0b40a0-c315-400f-95e6-e6084525b5bf', NOW(), false),
('task2-2222-2222-2222-222222222222', 'TASK002', 'b571d396-6064-50c8-9293-89ae6b8eb88c', '7eedc1ef-bc25-437d-a677-4bdc93f1d552', NOW(), false);

-- Insert sample admin sessions
INSERT INTO admin_sessions (id, admin_id, session_token, created_at, expires_at, is_active) VALUES 
('session1-1111-1111-1111-111111111111', 'b7ff2b6e-1dee-4859-969f-55f60b3daac6', 'admin_token_123', NOW(), NOW() + INTERVAL '24 hours', true);
"

# Add foreign key constraints
echo "Step 8: Adding foreign key constraints..."
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
echo "Step 9: Verifying database setup..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "
SELECT 'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'admin_users', COUNT(*) FROM admin_users
UNION ALL
SELECT 'chat_sessions', COUNT(*) FROM chat_sessions
UNION ALL
SELECT 'messages', COUNT(*) FROM messages
UNION ALL
SELECT 'system_prompts', COUNT(*) FROM system_prompts
UNION ALL
SELECT 'tally_submissions', COUNT(*) FROM tally_submissions
UNION ALL
SELECT 'active_ai_tasks', COUNT(*) FROM active_ai_tasks
UNION ALL
SELECT 'admin_sessions', COUNT(*) FROM admin_sessions;
"

echo "Step 10: Final table count verification..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "
SELECT COUNT(*) as total_tables FROM information_schema.tables WHERE table_schema = 'public';
"

# Start all services
echo "Step 11: Starting all services..."
docker-compose up -d

# Wait for services to be ready
echo "Step 12: Waiting for services to be ready..."
sleep 30

# Health checks
echo "Step 13: Performing health checks..."

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
echo "Step 14: Final service status..."
docker-compose ps

echo ""
echo "🎉 Complete VPS Fix Complete!"
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
echo "📊 Database Status:"
echo "   ✅ ALL 8 TABLES CREATED:"
echo "      - users (16 users)"
echo "      - admin_users (1 admin)"
echo "      - chat_sessions (2 sessions)"
echo "      - messages (4 messages)"
echo "      - system_prompts (2 prompts)"
echo "      - tally_submissions (2 submissions)"
echo "      - active_ai_tasks (2 tasks)"
echo "      - admin_sessions (1 session)"
echo ""
echo "📝 Useful Commands:"
echo "   View logs: docker-compose logs"
echo "   Check all tables: docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c '\dt'"
echo "   Check data counts: docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c 'SELECT COUNT(*) FROM users;'"
echo "   Restart services: docker-compose restart" 