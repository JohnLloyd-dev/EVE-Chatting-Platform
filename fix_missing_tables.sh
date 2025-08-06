#!/bin/bash

echo "🔧 Fixing Missing Database Tables"
echo "================================="

# Database credentials
DB_USER="adam@2025@man"

# Add missing tables
echo "[INFO] Adding missing active_ai_tasks table..."
docker exec eve-chatting-platform_postgres_1 psql -U "$DB_USER" -d chatting_platform -c "
CREATE TABLE IF NOT EXISTS active_ai_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id VARCHAR(255) UNIQUE NOT NULL,
    session_id UUID REFERENCES chat_sessions(id),
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_cancelled BOOLEAN DEFAULT FALSE
);
"

echo "[INFO] Adding missing admin_sessions table..."
docker exec eve-chatting-platform_postgres_1 psql -U "$DB_USER" -d chatting_platform -c "
CREATE TABLE IF NOT EXISTS admin_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_id UUID REFERENCES admin_users(id),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);
"

echo "[INFO] Adding missing admin_users table..."
docker exec eve-chatting-platform_postgres_1 psql -U "$DB_USER" -d chatting_platform -c "
CREATE TABLE IF NOT EXISTS admin_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
"

echo "[INFO] Adding missing system_prompts table..."
docker exec eve-chatting-platform_postgres_1 psql -U "$DB_USER" -d chatting_platform -c "
CREATE TABLE IF NOT EXISTS system_prompts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    head_prompt TEXT NOT NULL,
    rule_prompt TEXT NOT NULL,
    user_id UUID REFERENCES users(id),
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"

echo "[INFO] Adding missing tally_submissions table..."
docker exec eve-chatting-platform_postgres_1 psql -U "$DB_USER" -d chatting_platform -c "
CREATE TABLE IF NOT EXISTS tally_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    form_data JSONB,
    processed_scenario TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"

echo "[INFO] Adding missing columns to users table..."
docker exec eve-chatting-platform_postgres_1 psql -U "$DB_USER" -d chatting_platform -c "
ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_responses_enabled BOOLEAN DEFAULT true;
ALTER TABLE users ADD COLUMN IF NOT EXISTS user_code VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS device_id VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS user_type VARCHAR(50) DEFAULT 'tally';
"

echo "[SUCCESS] All missing tables and columns added!"

# Restart backend to clear any cached schema
echo "[INFO] Restarting backend to refresh database connection..."
docker-compose restart backend

echo "[SUCCESS] Database fix completed!"