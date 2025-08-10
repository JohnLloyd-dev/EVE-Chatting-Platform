-- Fix Database User Issue
-- This script creates a new database user without special characters

-- Connect as superuser first
-- psql -U postgres -d postgres

-- Create new user without special characters
CREATE USER adam2025man WITH PASSWORD 'adam2025';

-- Grant necessary privileges
GRANT CONNECT ON DATABASE chatting_platform TO adam2025man;
GRANT USAGE ON SCHEMA public TO adam2025man;

-- Grant table permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO adam2025man;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO adam2025man;

-- Grant permissions for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO adam2025man;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO adam2025man;

-- Enable login
ALTER USER adam2025man LOGIN;

-- Drop old user (optional - uncomment if you want to remove the old user)
-- DROP USER IF EXISTS "adam@2025@man";

-- Verify the new user
SELECT rolname, rolcanlogin, rolcanconnect FROM pg_roles WHERE rolname = 'adam2025man'; 