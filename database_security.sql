-- Database Security Configuration
-- This script creates a secure database user with minimal privileges
-- and configures security settings to prevent SQL injection and unauthorized access

-- Create secure database user with minimal privileges
CREATE USER IF NOT EXISTS "adam@2025@man" WITH PASSWORD 'eve@postgres@3241';

-- Grant only necessary privileges to the application user
-- NO SUPERUSER, NO CREATEDB, NO CREATEROLE, NO INHERIT, NO LOGIN (initially)

-- Grant connect permission to the database
GRANT CONNECT ON DATABASE chatting_platform TO "adam@2025@man";

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO "adam@2025@man";

-- Grant specific table permissions (read/write only)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "adam@2025@man";

-- Grant sequence permissions for auto-incrementing IDs
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "adam@2025@man";

-- Grant permissions for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "adam@2025@man";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO "adam@2025@man";

-- Revoke dangerous permissions
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM "adam@2025@man";
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM "adam@2025@man";
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM "adam@2025@man";

-- Grant only necessary permissions back
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE users TO "adam@2025@man";
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE chat_sessions TO "adam@2025@man";
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE messages TO "adam@2025@man";
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE admin_users TO "adam@2025@man";
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE admin_sessions TO "adam@2025@man";
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE tally_submissions TO "adam@2025@man";
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE system_prompts TO "adam@2025@man";
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE active_ai_tasks TO "adam@2025@man";

-- Grant sequence permissions
GRANT USAGE, SELECT ON SEQUENCE IF EXISTS users_id_seq TO "adam@2025@man";
GRANT USAGE, SELECT ON SEQUENCE IF EXISTS chat_sessions_id_seq TO "adam@2025@man";
GRANT USAGE, SELECT ON SEQUENCE IF EXISTS messages_id_seq TO "adam@2025@man";
GRANT USAGE, SELECT ON SEQUENCE IF EXISTS admin_users_id_seq TO "adam@2025@man";
GRANT USAGE, SELECT ON SEQUENCE IF EXISTS admin_sessions_id_seq TO "adam@2025@man";
GRANT USAGE, SELECT ON SEQUENCE IF EXISTS tally_submissions_id_seq TO "adam@2025@man";
GRANT USAGE, SELECT ON SEQUENCE IF EXISTS system_prompts_id_seq TO "adam@2025@man";
GRANT USAGE, SELECT ON SEQUENCE IF EXISTS active_ai_tasks_id_seq TO "adam@2025@man";

-- Explicitly deny dangerous operations
REVOKE CREATE ON SCHEMA public FROM "adam@2025@man";
REVOKE USAGE ON SCHEMA information_schema FROM "adam@2025@man";
REVOKE USAGE ON SCHEMA pg_catalog FROM "adam@2025@man";

-- Deny access to system tables and functions
REVOKE ALL ON ALL TABLES IN SCHEMA pg_catalog FROM "adam@2025@man";
REVOKE ALL ON ALL TABLES IN SCHEMA information_schema FROM "adam@2025@man";
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA pg_catalog FROM "adam@2025@man";
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA information_schema FROM "adam@2025@man";

-- Deny access to dangerous functions
REVOKE EXECUTE ON FUNCTION pg_read_file(text) FROM "adam@2025@man";
REVOKE EXECUTE ON FUNCTION pg_read_file(text, bigint, bigint, boolean) FROM "adam@2025@man";
REVOKE EXECUTE ON FUNCTION pg_ls_dir(text) FROM "adam@2025@man";
REVOKE EXECUTE ON FUNCTION pg_ls_logdir() FROM "adam@2025@man";
REVOKE EXECUTE ON FUNCTION pg_ls_waldir() FROM "adam@2025@man";
REVOKE EXECUTE ON FUNCTION pg_ls_tmpdir() FROM "adam@2025@man";
REVOKE EXECUTE ON FUNCTION pg_ls_archive_statusdir() FROM "adam@2025@man";

-- Deny COPY FROM PROGRAM (dangerous file system access)
REVOKE EXECUTE ON FUNCTION pg_read_binary_file(text) FROM "adam@2025@man";
REVOKE EXECUTE ON FUNCTION pg_read_binary_file(text, bigint, bigint, boolean) FROM "adam@2025@man";

-- Deny access to pg_stat_activity (information disclosure)
REVOKE SELECT ON TABLE pg_stat_activity FROM "adam@2025@man";

-- Deny access to pg_stat_statements (if installed)
REVOKE SELECT ON TABLE pg_stat_statements FROM "adam@2025@man";

-- Configure PostgreSQL security settings
-- These settings should be added to postgresql.conf

-- Disable dangerous features
-- shared_preload_libraries = ''  -- Disable extensions that could be dangerous
-- log_statement = 'all'          -- Log all statements for security monitoring
-- log_connections = on           -- Log all connections
-- log_disconnections = on        -- Log all disconnections
-- log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '  -- Detailed logging

-- Security-related settings
-- ssl = on                       -- Enable SSL connections
-- ssl_ciphers = 'HIGH:!aNULL'    -- Use strong ciphers
-- ssl_prefer_server_ciphers = on -- Prefer server ciphers

-- Connection limits
-- max_connections = 100          -- Limit concurrent connections
-- superuser_reserved_connections = 3  -- Reserve connections for superuser

-- Statement timeout to prevent long-running queries
-- statement_timeout = '30s'      -- Kill queries that run too long

-- Create security logging function
CREATE OR REPLACE FUNCTION log_security_event(event_type text, event_details text, client_ip inet DEFAULT NULL)
RETURNS void AS $$
BEGIN
    -- Log security events to a dedicated table
    INSERT INTO security_events (event_type, event_details, client_ip, event_timestamp)
    VALUES (event_type, event_details, client_ip, CURRENT_TIMESTAMP);
    
    -- Also log to PostgreSQL log
    RAISE LOG 'SECURITY EVENT: % - % - Client: %', event_type, event_details, client_ip;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create security events table
CREATE TABLE IF NOT EXISTS security_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    event_details TEXT,
    client_ip INET,
    event_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    severity VARCHAR(20) DEFAULT 'INFO'
);

-- Grant permissions on security table
GRANT INSERT ON TABLE security_events TO "adam@2025@man";
GRANT SELECT ON TABLE security_events TO "adam@2025@man";

-- Create function to check for suspicious activity
CREATE OR REPLACE FUNCTION check_suspicious_activity(client_ip inet)
RETURNS boolean AS $$
DECLARE
    recent_events integer;
BEGIN
    -- Check for too many failed login attempts
    SELECT COUNT(*) INTO recent_events
    FROM security_events
    WHERE client_ip = $1
    AND event_type = 'FAILED_LOGIN'
    AND event_timestamp > CURRENT_TIMESTAMP - INTERVAL '15 minutes';
    
    IF recent_events > 5 THEN
        RETURN true;  -- Suspicious activity detected
    END IF;
    
    -- Check for too many SQL errors
    SELECT COUNT(*) INTO recent_events
    FROM security_events
    WHERE client_ip = $1
    AND event_type = 'SQL_ERROR'
    AND event_timestamp > CURRENT_TIMESTAMP - INTERVAL '5 minutes';
    
    IF recent_events > 10 THEN
        RETURN true;  -- Suspicious activity detected
    END IF;
    
    RETURN false;  -- No suspicious activity
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger to log all database operations
CREATE OR REPLACE FUNCTION log_database_operations()
RETURNS trigger AS $$
BEGIN
    -- Log the operation
    INSERT INTO security_events (event_type, event_details, event_timestamp)
    VALUES (
        'DB_OPERATION',
        TG_OP || ' on ' || TG_TABLE_NAME || ' by ' || current_user,
        CURRENT_TIMESTAMP
    );
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Apply trigger to all tables
CREATE TRIGGER log_users_operations
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION log_database_operations();

CREATE TRIGGER log_chat_sessions_operations
    AFTER INSERT OR UPDATE OR DELETE ON chat_sessions
    FOR EACH ROW EXECUTE FUNCTION log_database_operations();

CREATE TRIGGER log_messages_operations
    AFTER INSERT OR UPDATE OR DELETE ON messages
    FOR EACH ROW EXECUTE FUNCTION log_database_operations();

CREATE TRIGGER log_admin_users_operations
    AFTER INSERT OR UPDATE OR DELETE ON admin_users
    FOR EACH ROW EXECUTE FUNCTION log_database_operations();

CREATE TRIGGER log_admin_sessions_operations
    AFTER INSERT OR UPDATE OR DELETE ON admin_sessions
    FOR EACH ROW EXECUTE FUNCTION log_database_operations();

CREATE TRIGGER log_tally_submissions_operations
    AFTER INSERT OR UPDATE OR DELETE ON tally_submissions
    FOR EACH ROW EXECUTE FUNCTION log_database_operations();

CREATE TRIGGER log_system_prompts_operations
    AFTER INSERT OR UPDATE OR DELETE ON system_prompts
    FOR EACH ROW EXECUTE FUNCTION log_database_operations();

CREATE TRIGGER log_active_ai_tasks_operations
    AFTER INSERT OR UPDATE OR DELETE ON active_ai_tasks
    FOR EACH ROW EXECUTE FUNCTION log_database_operations();

-- Create view for security monitoring
CREATE OR REPLACE VIEW security_monitoring AS
SELECT 
    event_type,
    COUNT(*) as event_count,
    MIN(event_timestamp) as first_event,
    MAX(event_timestamp) as last_event,
    client_ip
FROM security_events
WHERE event_timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour'
GROUP BY event_type, client_ip
ORDER BY event_count DESC;

-- Grant read access to security monitoring view
GRANT SELECT ON security_monitoring TO "adam@2025@man";

-- Create function to clean old security events
CREATE OR REPLACE FUNCTION clean_old_security_events()
RETURNS void AS $$
BEGIN
    DELETE FROM security_events 
    WHERE event_timestamp < CURRENT_TIMESTAMP - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create a secure connection function
CREATE OR REPLACE FUNCTION require_ssl_connection()
RETURNS void AS $$
BEGIN
    IF NOT current_setting('ssl') = 'on' THEN
        RAISE EXCEPTION 'SSL connection required';
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Enable the secure user
ALTER USER "adam@2025@man" LOGIN;

-- Final security check
DO $$
BEGIN
    -- Verify user has correct permissions
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles 
        WHERE rolname = 'adam@2025@man' 
        AND rolcanlogin = true 
        AND rolsuper = false
    ) THEN
        RAISE EXCEPTION 'Security user not properly configured';
    END IF;
    
    RAISE NOTICE 'Database security configuration completed successfully';
END $$; 