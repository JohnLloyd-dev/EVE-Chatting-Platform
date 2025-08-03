#!/bin/bash

# Simple VPS Complete Script
# Creates sample data and fixes frontend issues

echo "🚀 Simple VPS Complete"
echo "====================="

# Check if PostgreSQL is running
echo "Step 1: Checking PostgreSQL status..."
if docker exec eve-chatting-platform_postgres_1 pg_isready -U postgres >/dev/null 2>&1; then
    echo "✅ PostgreSQL is running!"
else
    echo "❌ PostgreSQL is not running. Exiting..."
    exit 1
fi

# Check what tables exist
echo "Step 2: Checking existing tables..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "\dt"

# Create missing tables if needed
echo "Step 3: Creating missing tables..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "
CREATE TABLE IF NOT EXISTS admin_users (
    id UUID PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN
);

CREATE TABLE IF NOT EXISTS system_prompts (
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
"

# Insert sample data
echo "Step 4: Inserting sample data..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "
-- Insert admin user if not exists
INSERT INTO admin_users (id, username, password_hash, email, created_at, is_active) 
VALUES ('b7ff2b6e-1dee-4859-969f-55f60b3daac6', 'admin', '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.Gm.F5W', 'admin@chatplatform.com', NOW(), true)
ON CONFLICT (username) DO NOTHING;

-- Insert sample users if not exists
INSERT INTO users (id, user_code, email, created_at, is_blocked, ai_responses_enabled) VALUES 
('4c0b40a0-c315-400f-95e6-e6084525b5bf', 'EVE001', 'user1@example.com', NOW(), false, true),
('7eedc1ef-bc25-437d-a677-4bdc93f1d552', 'EVE002', 'user2@example.com', NOW(), false, true),
('0bb5b42a-5ef8-4332-82ca-225ba1db4866', 'EVE003', 'user3@example.com', NOW(), false, true),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'EVE004', 'user4@example.com', NOW(), false, true),
('b2c3d4e5-f6g7-8901-bcde-f23456789012', 'EVE005', 'user5@example.com', NOW(), false, true)
ON CONFLICT (id) DO NOTHING;

-- Insert sample system prompt if not exists
INSERT INTO system_prompts (id, name, head_prompt, rule_prompt, is_active, created_by, created_at, updated_at) 
VALUES ('00fb86a2-2257-4661-8fa7-b9d225c28299', 'Default Sexual Fantasy Assistant', 'You are a sexual fantasy assistant.', 'Always speak in the first person and stay in character.', true, 'b7ff2b6e-1dee-4859-969f-55f60b3daac6', NOW(), NOW())
ON CONFLICT (name) DO NOTHING;
"

# Verify data
echo "Step 5: Verifying data..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "
SELECT 'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'admin_users', COUNT(*) FROM admin_users
UNION ALL
SELECT 'system_prompts', COUNT(*) FROM system_prompts;
"

# Fix frontend
echo "Step 6: Fixing frontend..."
docker-compose stop frontend
docker-compose rm frontend

# Rebuild frontend
echo "Step 7: Rebuilding frontend..."
docker-compose build frontend
docker-compose up -d frontend

# Wait for frontend to be ready
echo "Step 8: Waiting for frontend to be ready..."
sleep 30

# Check backend health
echo "Step 9: Checking backend health..."
if curl -s http://localhost:8001/health >/dev/null; then
    echo "✅ Backend is healthy!"
else
    echo "❌ Backend health check failed"
fi

# Check frontend
echo "Step 10: Checking frontend..."
if curl -s -I http://localhost:3000 | grep -q "200\|302"; then
    echo "✅ Frontend is responding!"
else
    echo "⚠️ Frontend may still be starting up"
fi

# Final status
echo "Step 11: Final service status..."
docker-compose ps

echo ""
echo "🎉 VPS Setup Complete!"
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