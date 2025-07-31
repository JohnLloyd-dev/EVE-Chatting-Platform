-- Comprehensive Migration: Create missing tables and columns
-- This migration ensures all required database objects exist

-- Migration 1: Add ai_responses_enabled column to users table
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'ai_responses_enabled'
    ) THEN
        ALTER TABLE users ADD COLUMN ai_responses_enabled BOOLEAN DEFAULT TRUE;
        UPDATE users SET ai_responses_enabled = TRUE WHERE ai_responses_enabled IS NULL;
        RAISE NOTICE 'Successfully added ai_responses_enabled column to users table';
    ELSE
        RAISE NOTICE 'Column ai_responses_enabled already exists in users table';
    END IF;
END $$;

-- Migration 2: Create active_ai_tasks table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name = 'active_ai_tasks'
    ) THEN
        CREATE TABLE active_ai_tasks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            task_id VARCHAR(255) UNIQUE NOT NULL,
            session_id UUID NOT NULL REFERENCES chat_sessions(id),
            user_id UUID NOT NULL REFERENCES users(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            is_cancelled BOOLEAN DEFAULT FALSE
        );
        RAISE NOTICE 'Successfully created active_ai_tasks table';
    ELSE
        RAISE NOTICE 'Table active_ai_tasks already exists';
    END IF;
END $$;

-- Migration 3: Create system_prompts table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name = 'system_prompts'
    ) THEN
        CREATE TABLE system_prompts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            is_active BOOLEAN DEFAULT FALSE,
            admin_id UUID REFERENCES admin_users(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            user_id UUID REFERENCES users(id)
        );
        RAISE NOTICE 'Successfully created system_prompts table';
    ELSE
        RAISE NOTICE 'Table system_prompts already exists';
    END IF;
END $$;