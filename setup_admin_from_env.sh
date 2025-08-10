#!/bin/bash

echo "👤 Admin User Setup from Environment"
echo "==================================="

# Configuration
VPS_IP="204.12.233.105"

# Database connection details
DB_USER="adam2025man"
DB_PASSWORD="adam2025"
DB_NAME="chatting_platform"

# Check for .env.prod file
if [ -f ".env.prod" ]; then
    echo "[INFO] Loading admin configuration from .env.prod..."
    source .env.prod
    ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
    ADMIN_PASSWORD="${ADMIN_PASSWORD:-YourSecureAdminPassword789!}"
    ADMIN_EMAIL="${ADMIN_EMAIL:-admin@eve-platform.com}"
else
    echo "[WARNING] .env.prod not found, using default configuration..."
    ADMIN_USERNAME="admin"
    ADMIN_PASSWORD="YourSecureAdminPassword789!"
    ADMIN_EMAIL="admin@eve-platform.com"
fi

# Allow override from command line
if [ ! -z "$1" ] && [ ! -z "$2" ]; then
    ADMIN_USERNAME="$1"
    ADMIN_PASSWORD="$2"
    ADMIN_EMAIL="${3:-admin@eve-platform.com}"
    echo "[INFO] Using command line arguments for admin credentials"
fi

echo "[INFO] Setting up admin user with credentials:"
echo "  Username: $ADMIN_USERNAME"
echo "  Email: $ADMIN_EMAIL"
echo "  Password: [HIDDEN]"

# First, let's check if admin_users table exists and create it if needed
echo "[INFO] Ensuring admin_users table exists..."
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

# Remove any existing admin users (clean slate)
echo "[INFO] Removing existing admin users..."
docker exec eve-chatting-platform_postgres_1 psql -U "$DB_USER" -d chatting_platform -c "
DELETE FROM admin_users;
"

# Create password hash using Python (bcrypt)
echo "[INFO] Creating password hash..."
PASSWORD_HASH=$(docker exec eve-chatting-platform_backend_1 python3 -c "
import bcrypt
password = '$ADMIN_PASSWORD'.encode('utf-8')
hashed = bcrypt.hashpw(password, bcrypt.gensalt())
print(hashed.decode('utf-8'))
")

# Insert new admin user
echo "[INFO] Creating new admin user..."
docker exec eve-chatting-platform_postgres_1 psql -U "$DB_USER" -d chatting_platform -c "
INSERT INTO admin_users (username, password_hash, email, is_active) 
VALUES ('$ADMIN_USERNAME', '$PASSWORD_HASH', '$ADMIN_EMAIL', true);
"

# Verify admin user was created
echo "[INFO] Verifying admin user creation..."
ADMIN_COUNT=$(docker exec eve-chatting-platform_postgres_1 psql -U "$DB_USER" -d chatting_platform -t -c "SELECT COUNT(*) FROM admin_users WHERE username = '$ADMIN_USERNAME';" | tr -d ' ')

if [ "$ADMIN_COUNT" = "1" ]; then
    echo "[SUCCESS] Admin user created successfully!"
    echo ""
    echo "🔐 Admin Login Credentials:"
    echo "  Username: $ADMIN_USERNAME"
    echo "  Password: $ADMIN_PASSWORD"
    echo "  Email: $ADMIN_EMAIL"
    echo ""
    echo "🌐 Admin Dashboard: http://$VPS_IP:3000/admin"
else
    echo "[ERROR] Failed to create admin user"
    exit 1
fi

echo "[SUCCESS] Admin setup completed!"