#!/bin/bash

echo "🔍 EVE Platform Configuration Verification"
echo "========================================="

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

echo "📋 Checking configuration files for VPS IP: $VPS_IP"
echo ""

# Check Docker Compose files
print_status "Checking Docker Compose files..."

# Check docker-compose.yml
if grep -q "$VPS_IP" docker-compose.yml; then
    print_success "docker-compose.yml contains correct VPS IP"
else
    print_error "docker-compose.yml missing VPS IP"
fi

# Check docker-compose.prod.yml
if grep -q "$VPS_IP" docker-compose.prod.yml; then
    print_success "docker-compose.prod.yml contains correct VPS IP"
else
    print_error "docker-compose.prod.yml missing VPS IP"
fi

# Check docker-compose.gpu.yml
if grep -q "$VPS_IP" docker-compose.gpu.yml; then
    print_success "docker-compose.gpu.yml contains correct VPS IP"
else
    print_error "docker-compose.gpu.yml missing VPS IP"
fi

# Check secure_docker_compose.yml
if grep -q "$VPS_IP" secure_docker_compose.yml; then
    print_success "secure_docker_compose.yml contains correct VPS IP"
else
    print_error "secure_docker_compose.yml missing VPS IP"
fi

echo ""

# Check deployment scripts
print_status "Checking deployment scripts..."

# Check deploy.sh
if grep -q "$VPS_IP" deploy.sh; then
    print_success "deploy.sh contains correct VPS IP"
else
    print_error "deploy.sh missing VPS IP"
fi

# Check deploy_gpu.sh
if grep -q "$VPS_IP" deploy_gpu.sh; then
    print_success "deploy_gpu.sh contains correct VPS IP"
else
    print_error "deploy_gpu.sh missing VPS IP"
fi

# Check deploy_ai.sh
if grep -q "$VPS_IP" deploy_ai.sh; then
    print_success "deploy_ai.sh contains correct VPS IP"
else
    print_error "deploy_ai.sh missing VPS IP"
fi

# Check scripts/deployment/deploy.sh
if grep -q "$VPS_IP" scripts/deployment/deploy.sh; then
    print_success "scripts/deployment/deploy.sh contains correct VPS IP"
else
    print_error "scripts/deployment/deploy.sh missing VPS IP"
fi

# Check scripts/deployment/start.sh
if grep -q "$VPS_IP" scripts/deployment/start.sh; then
    print_success "scripts/deployment/start.sh contains correct VPS IP"
else
    print_error "scripts/deployment/start.sh missing VPS IP"
fi

# Check scripts/deployment/test.sh
if grep -q "$VPS_IP" scripts/deployment/test.sh; then
    print_success "scripts/deployment/test.sh contains correct VPS IP"
else
    print_error "scripts/deployment/test.sh missing VPS IP"
fi

echo ""

# Check other important scripts
print_status "Checking other important scripts..."

# Check troubleshoot.sh
if grep -q "$VPS_IP" troubleshoot.sh; then
    print_success "troubleshoot.sh contains correct VPS IP"
else
    print_error "troubleshoot.sh missing VPS IP"
fi

# Check setup_admin.sh
if grep -q "$VPS_IP" setup_admin.sh; then
    print_success "setup_admin.sh contains correct VPS IP"
else
    print_error "setup_admin.sh missing VPS IP"
fi

# Check setup_admin_from_env.sh
if grep -q "$VPS_IP" setup_admin_from_env.sh; then
    print_success "setup_admin_from_env.sh contains correct VPS IP"
else
    print_error "setup_admin_from_env.sh missing VPS IP"
fi

# Check restore_database.sh
if grep -q "$VPS_IP" restore_database.sh; then
    print_success "restore_database.sh contains correct VPS IP"
else
    print_error "restore_database.sh missing VPS IP"
fi

echo ""

# Check for any remaining localhost references
print_status "Checking for remaining localhost references..."

LOCALHOST_COUNT=$(grep -r "localhost" . --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=__pycache__ --exclude="*.pyc" --exclude="*.log" | grep -v "localhost:5432" | grep -v "localhost:6379" | wc -l)

if [ "$LOCALHOST_COUNT" -eq 0 ]; then
    print_success "No localhost references found in configuration files"
else
    print_warning "Found $LOCALHOST_COUNT localhost references (excluding database ports)"
    echo ""
    echo "Remaining localhost references:"
    grep -r "localhost" . --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=__pycache__ --exclude="*.pyc" --exclude="*.log" | grep -v "localhost:5432" | grep -v "localhost:6379" | head -10
fi

echo ""
print_status "Configuration verification completed!"
echo ""
echo "🌐 Expected Access URLs:"
echo "   Frontend:        http://$VPS_IP:3000"
echo "   Backend API:     http://$VPS_IP:8001"
echo "   AI Server:       http://$VPS_IP:8000"
echo "   Admin Dashboard: http://$VPS_IP:3000/admin"
echo ""
echo "📚 Next steps:"
echo "   1. Run: ./deploy_gpu.sh (for GPU deployment)"
echo "   2. Run: ./deploy.sh (for CPU deployment)"
echo "   3. Run: ./troubleshoot.sh (to verify deployment)"
echo "   4. Run: ./setup_admin.sh (to set up admin user)" 