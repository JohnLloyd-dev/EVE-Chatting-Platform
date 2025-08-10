#!/bin/bash

echo "👑 Setting up Admin User for EVE Chat Platform"
echo "=============================================="

# Configuration
VPS_IP="204.12.233.105"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if backend is running
print_status "Checking if backend is running..."
if ! docker ps | grep -q "backend"; then
    print_error "Backend container not found. Please start the services first."
    echo "Run: docker-compose up -d"
    exit 1
fi

print_success "Backend container found"

# Get backend container name
BACKEND_CONTAINER=$(docker ps --format "{{.Names}}" | grep "backend" | head -1)
print_status "Using backend container: $BACKEND_CONTAINER"

# Check if admin user already exists
print_status "Checking if admin user already exists..."
ADMIN_EXISTS=$(docker exec "$BACKEND_CONTAINER" python3 -c "
from database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM users WHERE username = \\'admin\\''))
        count = result.scalar()
        print(count)
except Exception as e:
    print('Error:', e)
    print(0)
" 2>/dev/null)

if [ "$ADMIN_EXISTS" = "1" ]; then
    print_warning "Admin user already exists"
    read -p "Do you want to update the admin password? (y/n): " update_password
    if [ "$update_password" != "y" ]; then
        print_status "Admin setup skipped"
        exit 0
    fi
fi

# Get admin credentials
echo ""
print_status "Enter admin credentials:"
read -p "Admin username (default: admin): " ADMIN_USERNAME
ADMIN_USERNAME=${ADMIN_USERNAME:-admin}

read -s -p "Admin password: " ADMIN_PASSWORD
echo ""
read -s -p "Confirm admin password: " ADMIN_PASSWORD_CONFIRM
echo ""

if [ "$ADMIN_PASSWORD" != "$ADMIN_PASSWORD_CONFIRM" ]; then
    print_error "Passwords do not match"
    exit 1
fi

if [ -z "$ADMIN_PASSWORD" ]; then
    print_error "Password cannot be empty"
    exit 1
fi

# Create or update admin user
print_status "Setting up admin user..."
docker exec "$BACKEND_CONTAINER" python3 -c "
from database import engine
from sqlalchemy import text
import hashlib
import os

def hash_password(password):
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + key.hex()

try:
    with engine.connect() as conn:
        # Check if admin user exists
        result = conn.execute(text('SELECT COUNT(*) FROM users WHERE username = \\'$ADMIN_USERNAME\\''))
        count = result.scalar()
        
        if count > 0:
            # Update existing admin user
            hashed_password = hash_password('$ADMIN_PASSWORD')
            conn.execute(text('''
                UPDATE users 
                SET password_hash = :password_hash, 
                    is_admin = true,
                    updated_at = CURRENT_TIMESTAMP
                WHERE username = :username
            '''), {'password_hash': hashed_password, 'username': '$ADMIN_USERNAME'})
            print('Admin user updated successfully')
        else:
            # Create new admin user
            hashed_password = hash_password('$ADMIN_PASSWORD')
            conn.execute(text('''
                INSERT INTO users (username, password_hash, is_admin, created_at, updated_at)
                VALUES (:username, :password_hash, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            '''), {'username': '$ADMIN_USERNAME', 'password_hash': hashed_password})
            print('Admin user created successfully')
        
        conn.commit()
        print('Admin setup completed!')
        
except Exception as e:
    print('Error setting up admin user:', e)
    exit(1)
"

if [ $? -eq 0 ]; then
    print_success "Admin user setup completed!"
    echo ""
    print_status "Admin Dashboard Access:"
    echo "  URL: http://$VPS_IP:3000/admin"
    echo "  Username: $ADMIN_USERNAME"
    echo "  Password: [the password you entered]"
    echo ""
    print_status "You can now log in to the admin dashboard!"
else
    print_error "Failed to set up admin user"
    exit 1
fi