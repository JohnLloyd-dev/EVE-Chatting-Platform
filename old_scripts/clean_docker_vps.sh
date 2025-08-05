#!/bin/bash

# Complete Docker Cleanup Script for VPS
echo "🧹 Starting complete Docker cleanup on VPS..."

# Stop all running containers
echo "🛑 Stopping all containers..."
docker stop $(docker ps -aq) 2>/dev/null || echo "No containers to stop"

# Remove all containers
echo "🗑️ Removing all containers..."
docker rm $(docker ps -aq) 2>/dev/null || echo "No containers to remove"

# Remove all images
echo "🖼️ Removing all images..."
docker rmi $(docker images -q) -f 2>/dev/null || echo "No images to remove"

# Remove all volumes
echo "💾 Removing all volumes..."
docker volume rm $(docker volume ls -q) 2>/dev/null || echo "No volumes to remove"

# Remove all networks (except default ones)
echo "🌐 Removing custom networks..."
docker network rm $(docker network ls -q --filter type=custom) 2>/dev/null || echo "No custom networks to remove"

# Clean up build cache
echo "🧽 Cleaning build cache..."
docker builder prune -af 2>/dev/null || echo "No build cache to clean"

# Clean up system
echo "🔧 Cleaning Docker system..."
docker system prune -af --volumes 2>/dev/null || echo "System already clean"

# Show final status
echo "📊 Final Docker status:"
echo "Containers:"
docker ps -a
echo ""
echo "Images:"
docker images
echo ""
echo "Volumes:"
docker volume ls
echo ""
echo "Networks:"
docker network ls
echo ""

echo "✅ Complete Docker cleanup finished!"
echo "🚀 Ready for fresh start!"