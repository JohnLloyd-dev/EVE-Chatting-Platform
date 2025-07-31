-- Migration: Add ai_responses_enabled column to users table
-- This migration adds a new column to control AI responses separately from user blocking

-- Check if column already exists and add it if it doesn't
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'ai_responses_enabled'
    ) THEN
        -- Add the column with default value TRUE
        ALTER TABLE users 
        ADD COLUMN ai_responses_enabled BOOLEAN DEFAULT TRUE;
        
        -- Update existing users to have AI responses enabled by default
        UPDATE users 
        SET ai_responses_enabled = TRUE 
        WHERE ai_responses_enabled IS NULL;
        
        RAISE NOTICE 'Successfully added ai_responses_enabled column to users table';
    ELSE
        RAISE NOTICE 'Column ai_responses_enabled already exists in users table';
    END IF;
END $$;