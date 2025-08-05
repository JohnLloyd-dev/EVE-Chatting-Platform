-- Database initialization script with updated schema
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (updated with new columns)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_code VARCHAR(20) UNIQUE NOT NULL,
    tally_response_id VARCHAR(255) UNIQUE,
    tally_respondent_id VARCHAR(255),
    tally_form_id VARCHAR(255),
    device_id VARCHAR(255) UNIQUE,
    user_type VARCHAR(50) DEFAULT 'tally',
    email VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_blocked BOOLEAN DEFAULT FALSE,
    last_active TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Chat sessions table
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    scenario_prompt TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    is_from_user BOOLEAN NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_admin_intervention BOOLEAN DEFAULT FALSE,
    admin_id UUID NULL -- For tracking admin interventions
);

-- Admin users table
CREATE TABLE admin_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v5(),
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Admin sessions table for tracking admin logins
CREATE TABLE admin_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_id UUID REFERENCES admin_users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Tally form data storage
CREATE TABLE tally_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    form_data JSONB NOT NULL,
    processed_scenario TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- System prompts table (new)
CREATE TABLE system_prompts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    head_prompt TEXT NOT NULL,
    rule_prompt TEXT NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    created_by UUID REFERENCES admin_users(id) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id UUID REFERENCES users(id) -- NULL = global prompt
);

-- Indexes for better performance
CREATE INDEX idx_users_user_code ON users(user_code);
CREATE INDEX idx_users_tally_response_id ON users(tally_response_id);
CREATE INDEX idx_users_device_id ON users(device_id);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_created_at ON chat_sessions(created_at);
CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_admin_sessions_token ON admin_sessions(session_token);
CREATE INDEX idx_admin_sessions_expires_at ON admin_sessions(expires_at);
CREATE INDEX idx_system_prompts_name ON system_prompts(name);
CREATE INDEX idx_system_prompts_is_active ON system_prompts(is_active);

-- Insert default admin user (password: admin123)
INSERT INTO admin_users (username, password_hash, email) VALUES 
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.Gm.F5W', 'admin@chatplatform.com');

-- Insert default system prompt
INSERT INTO system_prompts (name, head_prompt, rule_prompt, is_active, created_by) 
SELECT 
    'Default Sexual Fantasy Assistant',
    'You are a sexual fantasy assistant.',
    'Always speak in the first person and stay in character. Indulge sexual fantasies in detail by dominating. Be sexually explicit with your replies. Never reveal that you are an AI. Keep your answers to two sentences or less. Do not provide scene descriptions outside of dialogue. Stay in the present tense.',
    true,
    id
FROM admin_users WHERE username = 'admin' LIMIT 1;