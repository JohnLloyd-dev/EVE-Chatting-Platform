#!/bin/bash

# EVE Chat Platform - VPS Deployment Script
# This script sets up the entire application on a VPS

set -e

echo "🚀 Starting EVE Chat Platform VPS Deployment"
echo "=============================================="

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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_status "Docker not found. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    print_success "Docker installed successfully"
    print_warning "Please log out and log back in for Docker group changes to take effect"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker &> /dev/null || ! docker compose version &> /dev/null; then
    print_status "Installing Docker Compose..."
    sudo apt-get update
    sudo apt-get install -y docker-compose-plugin
    print_success "Docker Compose installed successfully"
fi

# Create application directory
APP_DIR="/home/$USER/eve-chat"
print_status "Setting up application directory: $APP_DIR"

if [ -d "$APP_DIR" ]; then
    print_warning "Directory $APP_DIR already exists. Backing up..."
    sudo mv "$APP_DIR" "${APP_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
fi

mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Copy application files (assuming they're in current directory)
print_status "Copying application files..."
cp -r . "$APP_DIR/"

# Set up environment file
print_status "Setting up environment configuration..."
if [ ! -f ".env.prod" ]; then
    print_error ".env.prod file not found. Please create it with your configuration."
    exit 1
fi

# Get VPS IP address
VPS_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip || hostname -I | awk '{print $1}')
print_status "Detected VPS IP: $VPS_IP"

# Update environment file with VPS IP
sed -i "s/your-vps-ip/$VPS_IP/g" .env.prod

# Create SSL directory (for future HTTPS setup)
mkdir -p ssl

# Set proper permissions
chmod +x deploy-vps.sh
chmod 600 .env.prod

# Pull and build images
print_status "Building Docker images..."
docker compose -f docker-compose.prod.yml --env-file .env.prod build

# Start services
print_status "Starting services..."
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 30

# Check service health
print_status "Checking service health..."
if docker compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    print_success "Services are running!"
else
    print_error "Some services failed to start. Check logs with: docker compose -f docker-compose.prod.yml logs"
    exit 1
fi

# Run database migrations
print_status "Running database setup..."
docker compose -f docker-compose.prod.yml exec backend python -c "
from database import engine, Base
Base.metadata.create_all(bind=engine)
print('Database tables created successfully')
"

# Create admin user
print_status "Setting up admin user..."
docker compose -f docker-compose.prod.yml exec backend python -c "
from database import SessionLocal, AdminUser
from auth import get_password_hash
import os

db = SessionLocal()
admin_username = os.getenv('ADMIN_USERNAME', 'admin')
admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')

# Check if admin exists
existing_admin = db.query(AdminUser).filter(AdminUser.username == admin_username).first()
if not existing_admin:
    admin_user = AdminUser(
        username=admin_username,
        email=f'{admin_username}@eve-chat.local',
        password_hash=get_password_hash(admin_password),
        is_active=True
    )
    db.add(admin_user)
    db.commit()
    print(f'Admin user {admin_username} created successfully')
else:
    print(f'Admin user {admin_username} already exists')
db.close()
"

# Display deployment information
echo ""
echo "🎉 Deployment Complete!"
echo "======================"
print_success "EVE Chat Platform is now running on your VPS!"
echo ""
echo "📋 Access Information:"
echo "   Frontend: http://$VPS_IP:3000"
echo "   Backend API: http://$VPS_IP:8001"
echo "   Admin Panel: http://$VPS_IP:3000/admin"
echo ""
echo "🔐 Admin Credentials:"
echo "   Username: $(grep ADMIN_USERNAME .env.prod | cut -d'=' -f2)"
echo "   Password: $(grep ADMIN_PASSWORD .env.prod | cut -d'=' -f2)"
echo ""
echo "📝 Useful Commands:"
echo "   View logs: docker compose -f docker-compose.prod.yml logs"
echo "   Stop services: docker compose -f docker-compose.prod.yml down"
echo "   Restart services: docker compose -f docker-compose.prod.yml restart"
echo "   Update application: git pull && docker compose -f docker-compose.prod.yml up -d --build"
echo ""
print_warning "Remember to:"
print_warning "1. Set up a firewall (ufw enable, ufw allow 22,80,443,3000,8001)"
print_warning "2. Set up SSL certificates for HTTPS"
print_warning "3. Configure a domain name if needed"
print_warning "4. Set up regular backups"
echo ""
print_success "Happy chatting! 🤖💬"