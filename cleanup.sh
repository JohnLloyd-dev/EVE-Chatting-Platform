#!/bin/bash

echo "🧹 EVE Platform - System Cleanup Script"
echo "========================================"

# Function to print colored output
print_status() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

print_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

print_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

echo ""
print_status "Starting comprehensive cleanup..."

# 1. Docker cleanup
echo ""
print_status "Cleaning Docker resources..."
docker system prune -f
docker image prune -f
docker network prune -f
docker volume prune -f
print_success "Docker cleanup completed"

# 2. System temp files
echo ""
print_status "Cleaning system temporary files..."
rm -rf /tmp/*
rm -rf /var/tmp/*
print_success "System temp files cleaned"

# 3. User cache
echo ""
print_status "Cleaning user cache..."
rm -rf ~/.cache/*
print_success "User cache cleaned"

# 4. Package manager cache
echo ""
print_status "Cleaning package manager cache..."
apt clean -y 2>/dev/null || true
apt autoremove -y 2>/dev/null || true
print_success "Package cache cleaned"

# 5. AI model cache (if exists)
echo ""
print_status "Cleaning AI model cache..."
if docker volume ls | grep -q ai_model_cache; then
    docker volume rm eve-chatting-platform_ai_model_cache 2>/dev/null || true
    print_success "AI model cache cleaned"
else
    print_warning "AI model cache not found"
fi

# 6. Container logs cleanup
echo ""
print_status "Cleaning container logs..."
docker system prune -f
print_success "Container logs cleaned"

# 7. Show disk usage
echo ""
print_status "Current disk usage:"
df -h /

# 8. Show Docker disk usage
echo ""
print_status "Docker disk usage:"
docker system df

echo ""
print_success "Cleanup completed successfully!"
echo ""
print_status "To restart services, run:"
echo "  docker-compose -f docker-compose.gpu.yml up -d" 