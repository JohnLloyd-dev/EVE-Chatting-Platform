#!/bin/bash

# EVE Chat Platform - Setup Verification Script
# This script verifies that all required tools are properly installed

set -e

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

echo "=== EVE Chat Platform - Setup Verification ==="
echo ""

# Check system packages
print_status "Checking system packages..."
if command -v curl &> /dev/null; then
    print_success "curl: OK"
else
    print_error "curl: NOT FOUND"
fi

if command -v wget &> /dev/null; then
    print_success "wget: OK"
else
    print_error "wget: NOT FOUND"
fi

if command -v git &> /dev/null; then
    print_success "git: OK"
else
    print_error "git: NOT FOUND"
fi

# Check Python
print_status "Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    print_success "Python3: $PYTHON_VERSION"
else
    print_error "Python3: NOT FOUND"
fi

if command -v pip3 &> /dev/null; then
    print_success "pip3: OK"
else
    print_error "pip3: NOT FOUND"
fi

# Check Node.js
print_status "Checking Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version 2>&1)
    print_success "Node.js: $NODE_VERSION"
else
    print_error "Node.js: NOT FOUND"
fi

if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version 2>&1)
    print_success "npm: $NPM_VERSION"
else
    print_error "npm: NOT FOUND"
fi

# Check Docker
print_status "Checking Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version 2>&1)
    print_success "Docker: $DOCKER_VERSION"
else
    print_error "Docker: NOT FOUND"
fi

if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version 2>&1)
    print_success "Docker Compose: $COMPOSE_VERSION"
else
    print_error "Docker Compose: NOT FOUND"
fi

# Check Docker service
if systemctl is-active --quiet docker; then
    print_success "Docker service: RUNNING"
else
    print_error "Docker service: NOT RUNNING"
fi

# Check NVIDIA GPU and drivers
print_status "Checking NVIDIA GPU..."
if lspci | grep -i nvidia > /dev/null; then
    print_success "NVIDIA GPU: DETECTED"
    
    if command -v nvidia-smi &> /dev/null; then
        print_success "NVIDIA drivers: INSTALLED"
        GPU_INFO=$(nvidia-smi --query-gpu=name --format=csv,noheader,nounits | head -1)
        print_success "GPU: $GPU_INFO"
    else
        print_error "NVIDIA drivers: NOT INSTALLED"
    fi
    
    if command -v nvcc &> /dev/null; then
        CUDA_VERSION=$(nvcc --version | grep "release" | awk '{print $6}' | sed 's/,//')
        print_success "CUDA: $CUDA_VERSION"
    else
        print_error "CUDA: NOT INSTALLED"
    fi
    
    # Check NVIDIA Container Toolkit
    if docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi &> /dev/null; then
        print_success "NVIDIA Container Toolkit: WORKING"
    else
        print_error "NVIDIA Container Toolkit: NOT WORKING"
    fi
else
    print_warning "NVIDIA GPU: NOT DETECTED (CPU-only mode)"
fi

# Check Nginx
print_status "Checking Nginx..."
if command -v nginx &> /dev/null; then
    NGINX_VERSION=$(nginx -v 2>&1)
    print_success "Nginx: $NGINX_VERSION"
    
    if systemctl is-active --quiet nginx; then
        print_success "Nginx service: RUNNING"
    else
        print_error "Nginx service: NOT RUNNING"
    fi
else
    print_error "Nginx: NOT FOUND"
fi

# Check firewall
print_status "Checking firewall..."
if command -v ufw &> /dev/null; then
    UFW_STATUS=$(ufw status | head -1)
    print_success "UFW: $UFW_STATUS"
else
    print_error "UFW: NOT FOUND"
fi

# Check project directory
print_status "Checking project directory..."
if [ -d "/home/$USER/EVE-Chatting-Platform" ]; then
    print_success "Project directory: EXISTS"
    
    cd /home/$USER/EVE-Chatting-Platform
    
    if [ -f "docker-compose.yml" ]; then
        print_success "docker-compose.yml: EXISTS"
    else
        print_error "docker-compose.yml: NOT FOUND"
    fi
    
    if [ -f "deploy.sh" ]; then
        print_success "deploy.sh: EXISTS"
        if [ -x "deploy.sh" ]; then
            print_success "deploy.sh: EXECUTABLE"
        else
            print_error "deploy.sh: NOT EXECUTABLE"
        fi
    else
        print_error "deploy.sh: NOT FOUND"
    fi
    
    if [ -f ".env.prod" ]; then
        print_success ".env.prod: EXISTS"
    else
        print_error ".env.prod: NOT FOUND"
    fi
else
    print_error "Project directory: NOT FOUND"
fi

# Check network connectivity
print_status "Checking network connectivity..."
if ping -c 1 8.8.8.8 &> /dev/null; then
    print_success "Internet connectivity: OK"
else
    print_error "Internet connectivity: FAILED"
fi

# Check ports
print_status "Checking port availability..."
if netstat -tuln | grep ":80 " > /dev/null; then
    print_success "Port 80: IN USE"
else
    print_warning "Port 80: AVAILABLE"
fi

if netstat -tuln | grep ":3000 " > /dev/null; then
    print_success "Port 3000: IN USE"
else
    print_warning "Port 3000: AVAILABLE"
fi

if netstat -tuln | grep ":8001 " > /dev/null; then
    print_success "Port 8001: IN USE"
else
    print_warning "Port 8001: AVAILABLE"
fi

if netstat -tuln | grep ":8000 " > /dev/null; then
    print_success "Port 8000: IN USE"
else
    print_warning "Port 8000: AVAILABLE"
fi

echo ""
echo "=== Verification Complete ==="
echo ""
echo "If all checks passed, you can now run:"
echo "cd /home/$USER/EVE-Chatting-Platform"
echo "./deploy.sh"
echo ""
echo "If there are any errors, please run the setup script again:"
echo "sudo ./vps_initial_setup.sh" 