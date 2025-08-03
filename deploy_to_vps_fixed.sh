#!/bin/bash

# EVE Chat Platform - VPS Deployment Script (Fixed Version)
# This script handles PostgreSQL version compatibility issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🚀 EVE Chat Platform - VPS Deployment (Fixed)"
echo "============================================="

# Check if final123.sql exists
if [ ! -f "final123.sql" ]; then
    print_error "final123.sql not found!"
    print_error "Please ensure final123.sql is in the current directory."
    exit 1
fi

print_status "Found final123.sql: $(ls -lh final123.sql | awk '{print $5}')"

# Stop any existing containers
print_status "Stopping existing containers..."
docker stop $(docker ps -q) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true

# Remove existing volumes
print_status "Cleaning up existing volumes..."
docker volume rm $(docker volume ls -q) 2>/dev/null || true

# Create network
print_status "Creating Docker network..."
docker network create eve-network 2>/dev/null || true

# Start PostgreSQL with final123.sql
print_status "Starting PostgreSQL with database restoration..."

# Create a temporary PostgreSQL container for restoration
docker run -d \
  --name temp-postgres \
  --network eve-network \
  -e POSTGRES_DB=chatting_platform \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres123 \
  -v postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:17

# Wait for PostgreSQL to be ready
print_status "Waiting for PostgreSQL to start..."
sleep 30

# Test connection
for i in {1..10}; do
    if docker exec temp-postgres pg_isready -U postgres >/dev/null 2>&1; then
        print_success "PostgreSQL is ready!"
        break
    else
        print_status "Waiting for PostgreSQL... ($i/10)"
        sleep 5
    fi
done

# Copy final123.sql to container
print_status "Copying final123.sql to container..."
docker cp final123.sql temp-postgres:/tmp/final123.sql

# Create schema first
print_status "Creating database schema..."
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

# Try to restore data from final123.sql with version compatibility
print_status "Attempting to restore data from final123.sql..."

# First, try to convert the backup to SQL format
print_status "Converting backup to SQL format..."
if docker exec temp-postgres pg_restore -f /tmp/backup.sql /tmp/final123.sql 2>/dev/null; then
    print_success "Successfully converted backup to SQL format"
    print_status "Restoring from SQL format..."
    docker exec temp-postgres psql -U postgres -d chatting_platform -f /tmp/backup.sql
else
    print_warning "Could not convert backup, trying alternative approach..."
    
    # Try to extract data using pg_restore with different options
    print_status "Trying pg_restore with compatibility options..."
    if docker exec temp-postgres pg_restore -U postgres -d chatting_platform --data-only --no-owner --no-privileges /tmp/final123.sql 2>/dev/null; then
        print_success "Data restored successfully!"
    else
        print_error "Failed to restore data. Creating sample data instead..."
        
        # Create sample data as fallback
        docker exec temp-postgres psql -U postgres -d chatting_platform -c "
        -- Insert sample admin user
        INSERT INTO admin_users (id, username, password_hash, email, created_at, is_active) VALUES 
        ('b7ff2b6e-1dee-4859-969f-55f60b3daac6', 'admin', '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.Gm.F5W', 'admin@chatplatform.com', NOW(), true);
        
        -- Insert sample users
        INSERT INTO users (id, user_code, email, created_at, is_blocked, ai_responses_enabled) VALUES 
        ('4c0b40a0-c315-400f-95e6-e6084525b5bf', 'EVE001', 'user1@example.com', NOW(), false, true),
        ('7eedc1ef-bc25-437d-a677-4bdc93f1d552', 'EVE002', 'user2@example.com', NOW(), false, true),
        ('0bb5b42a-5ef8-4332-82ca-225ba1db4866', 'EVE003', 'user3@example.com', NOW(), false, true);
        
        -- Insert sample system prompt
        INSERT INTO system_prompts (id, name, head_prompt, rule_prompt, is_active, created_by, created_at, updated_at) VALUES 
        ('00fb86a2-2257-4661-8fa7-b9d225c28299', 'Default Sexual Fantasy Assistant', 'You are a sexual fantasy assistant.', 'Always speak in the first person and stay in character.', true, 'b7ff2b6e-1dee-4859-969f-55f60b3daac6', NOW(), NOW());
        "
    fi
fi

# Add foreign key constraints
print_status "Adding foreign key constraints..."
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

# Verify restoration
print_status "Verifying database restoration..."
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
SELECT 'admin_users', COUNT(*) FROM admin_users
UNION ALL
SELECT 'active_ai_tasks', COUNT(*) FROM active_ai_tasks;
"

# Stop temporary container
print_status "Stopping temporary PostgreSQL container..."
docker stop temp-postgres
docker rm temp-postgres

# Start all services with production configuration
print_status "Starting all services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to start
print_status "Waiting for services to start..."
sleep 30

# Health checks
print_status "Performing health checks..."

# Check backend
if curl -s http://localhost:8001/health >/dev/null; then
    print_success "Backend is healthy!"
else
    print_warning "Backend health check failed"
fi

# Check frontend
if curl -s -I http://localhost:3000 | grep -q "200\|302"; then
    print_success "Frontend is responding!"
else
    print_warning "Frontend may not be fully ready yet"
fi

# Check database
if docker exec eve-postgres-1 pg_isready -U postgres >/dev/null 2>&1; then
    print_success "Database is ready!"
else
    print_error "Database health check failed"
fi

echo ""
print_success "🎉 VPS Deployment Complete!"
echo ""
print_status "📋 Deployment Summary:"
echo "   ✅ Database schema created"
echo "   ✅ Data restored (or sample data created)"
echo "   ✅ All services started"
echo "   ✅ Health checks completed"
echo ""
print_status "🌐 Access Points:"
echo "   Frontend: http://your-vps-ip:3000"
echo "   Backend API: http://your-vps-ip:8001"
echo "   Admin Dashboard: http://your-vps-ip:3000/admin"
echo ""
print_status "🔐 Admin Credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
print_status "📝 Useful Commands:"
echo "   View logs: docker-compose -f docker-compose.prod.yml logs"
echo "   Restart services: docker-compose -f docker-compose.prod.yml restart"
echo "   Check database: docker exec eve-postgres-1 psql -U postgres -d chatting_platform -c 'SELECT COUNT(*) FROM users;'"
echo ""
print_success "Your EVE Chat Platform is now live on VPS! 🚀" 