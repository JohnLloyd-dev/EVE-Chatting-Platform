#!/bin/bash

# EVE Chat Platform - VPS Initial Setup Script
# This script sets up a fresh VPS with all necessary development tools

set -e  # Exit on any error

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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root (use sudo)"
    exit 1
fi

print_status "Starting VPS initial setup for EVE Chat Platform..."

# Step 1: Update system
print_status "Step 1: Updating system packages..."
apt update && apt upgrade -y
print_success "System updated"

# Step 2: Install essential packages
print_status "Step 2: Installing essential packages..."
apt install -y \
    curl \
    wget \
    git \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    ufw \
    fail2ban
print_success "Essential packages installed"

# Step 3: Install Docker
print_status "Step 3: Installing Docker..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
print_success "Docker installed"

# Step 4: Configure Docker
print_status "Step 4: Configuring Docker..."
usermod -aG docker $SUDO_USER
systemctl enable docker
systemctl start docker
print_success "Docker configured"

# Step 5: Install NVIDIA drivers and CUDA (if GPU is available)
print_status "Step 5: Checking for NVIDIA GPU..."
if lspci | grep -i nvidia > /dev/null; then
    print_status "NVIDIA GPU detected. Installing drivers and CUDA..."
    
    # Install NVIDIA drivers
    apt install -y nvidia-driver-535
    
    # Install CUDA toolkit
    wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
    dpkg -i cuda-keyring_1.1-1_all.deb
    apt update
    apt install -y cuda-toolkit-12-1
    
    # Install NVIDIA Container Toolkit
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
    curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-docker-keyring.gpg
    curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-docker-keyring.gpg] https://#g' | tee /etc/apt/sources.list.d/nvidia-docker.list
    apt update
    apt install -y nvidia-container-toolkit
    systemctl restart docker
    
    print_success "NVIDIA drivers and CUDA installed"
else
    print_warning "No NVIDIA GPU detected. Skipping GPU setup."
fi

# Step 6: Configure firewall
print_status "Step 6: Configuring firewall..."
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 3000/tcp  # Frontend
ufw allow 8001/tcp  # Backend
ufw allow 8000/tcp  # AI Server
ufw --force enable
print_success "Firewall configured"

# Step 7: Configure Nginx
print_status "Step 7: Configuring Nginx..."
cat > /etc/nginx/sites-available/eve-platform << 'EOF'
server {
    listen 80;
    server_name _;
    
    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:8001/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # AI Server
    location /ai/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF

ln -sf /etc/nginx/sites-available/eve-platform /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
systemctl enable nginx
systemctl restart nginx
print_success "Nginx configured"

# Step 8: Install Node.js (for frontend development)
print_status "Step 8: Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs
print_success "Node.js installed"

# Step 9: Create application directory and clone repository
print_status "Step 9: Setting up application directory..."
cd /home/$SUDO_USER
if [ ! -d "EVE-Chatting-Platform" ]; then
    git clone https://github.com/JohnLloyd-dev/EVE-Chatting-Platform.git
    chown -R $SUDO_USER:$SUDO_USER EVE-Chatting-Platform
fi
print_success "Repository cloned"

# Step 10: Set up environment
print_status "Step 10: Setting up environment..."
cd EVE-Chatting-Platform

# Create .env.prod file
cat > .env.prod << 'EOF'
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=chatting_platform
DB_USER=adam@2025@man
DB_PASSWORD=eve@postgres@3241

# Admin Configuration
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@spice.ai
ADMIN_PASSWORD=adam@and@eve@3241

# Security Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# AI Model Configuration
AI_MODEL_URL=http://localhost:8000
AI_MODEL_AUTH_USERNAME=adam
AI_MODEL_AUTH_PASSWORD=eve2025

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8001

# Security Settings
ENCRYPTION_KEY=your-32-character-encryption-key-here
ENABLE_MFA=true
ENABLE_RATE_LIMITING=true
ENABLE_WAF=true
EOF

chown $SUDO_USER:$SUDO_USER .env.prod
print_success "Environment configured"

# Step 11: Make deployment script executable
print_status "Step 11: Setting up deployment script..."
chmod +x deploy.sh
print_success "Deployment script ready"

# Step 12: Final instructions
print_success "VPS setup completed!"
echo ""
echo "Next steps:"
echo "1. Reboot the system: sudo reboot"
echo "2. After reboot, switch to your user: su - $SUDO_USER"
echo "3. Navigate to the project: cd EVE-Chatting-Platform"
echo "4. Run the deployment: ./deploy.sh"
echo ""
echo "The system will be available at:"
echo "- Frontend: http://your-server-ip"
echo "- Backend API: http://your-server-ip:8001"
echo "- AI Server: http://your-server-ip:8000"
echo ""
echo "Admin credentials:"
echo "- Username: admin"
echo "- Password: adam@and@eve@3241" 