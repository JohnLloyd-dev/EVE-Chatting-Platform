#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VPS_IP="204.12.233.105"

# Print functions
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

echo "👑 Setting up Admin User for EVE Chat Platform"
echo "=============================================="

# Check if backend is running
print_status "Checking if backend is running..."
BACKEND_CONTAINER=$(docker ps --filter "name=backend" --format "{{.Names}}" | head -1)

if [ -z "$BACKEND_CONTAINER" ]; then
    print_error "Backend container not found. Please start the platform first."
    echo "Run: ./deploy_gpu.sh or ./deploy.sh"
    exit 1
fi

print_success "Backend container found"
print_status "Using backend container: $BACKEND_CONTAINER"

# Check if admin user already exists
print_status "Checking if admin user already exists..."

ADMIN_EXISTS=$(docker exec $BACKEND_CONTAINER python3 -c "
import psycopg2
import os

try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM admin_users WHERE username = %s', ('admin',))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    print(count)
except Exception as e:
    print('ERROR:', str(e))
    exit(1)
")

if [ "$ADMIN_EXISTS" = "ERROR:"* ]; then
    print_error "Database error: $ADMIN_EXISTS"
    exit 1
fi

if [ "$ADMIN_EXISTS" -gt 0 ]; then
    print_warning "Admin user 'admin' already exists"
    read -p "Do you want to update the password? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Password update cancelled"
        echo ""
        echo "🌐 Admin Dashboard: http://$VPS_IP:3000/admin"
        echo "   Current credentials: admin / [existing password]"
        exit 0
    fi
fi

# Get admin credentials
echo ""
print_status "Enter admin credentials:"
read -p "Admin username (default: admin): " ADMIN_USERNAME
ADMIN_USERNAME=${ADMIN_USERNAME:-admin}

read -s -p "Admin password: " ADMIN_PASSWORD
echo
read -s -p "Confirm admin password: " ADMIN_PASSWORD_CONFIRM
echo

if [ "$ADMIN_PASSWORD" != "$ADMIN_PASSWORD_CONFIRM" ]; then
    print_error "Passwords do not match"
    exit 1
fi

if [ -z "$ADMIN_PASSWORD" ]; then
    print_error "Password cannot be empty"
    exit 1
fi

# Set up admin user
print_status "Setting up admin user..."

ADMIN_RESULT=$(docker exec $BACKEND_CONTAINER python3 -c "
import psycopg2
import os
import bcrypt

try:
    # Hash the password
    password_bytes = '$ADMIN_PASSWORD'.encode('utf-8')
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    if $ADMIN_EXISTS > 0:
        # Update existing admin user
        cur.execute('UPDATE admin_users SET password_hash = %s WHERE username = %s', (password_hash, '$ADMIN_USERNAME'))
        print('UPDATED')
    else:
        # Create new admin user
        cur.execute('INSERT INTO admin_users (username, password_hash, email) VALUES (%s, %s, %s)', 
                   ('$ADMIN_USERNAME', password_hash, 'admin@chatplatform.com'))
        print('CREATED')
    
    conn.commit()
    cur.close()
    conn.close()
    
except Exception as e:
    print('ERROR:', str(e))
    exit(1)
")

if [ "$ADMIN_RESULT" = "ERROR:"* ]; then
    print_error "Failed to set up admin user: $ADMIN_RESULT"
    exit 1
fi

print_success "Admin user $ADMIN_RESULT successfully"
echo ""
echo "🌐 Admin Dashboard: http://$VPS_IP:3000/admin"
echo "   Username: $ADMIN_USERNAME"
echo "   Password: [the password you entered]"
echo ""
echo "✅ Admin user setup complete!"