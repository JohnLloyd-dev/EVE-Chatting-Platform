#!/bin/bash

# Fix VPS Services Script
# This script fixes the service startup issues after database restoration

echo "🔧 Fixing VPS Services"
echo "====================="

# Stop all containers and remove orphans
echo "Step 1: Stopping all containers and removing orphans..."
docker-compose down --remove-orphans
docker stop $(docker ps -q) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true

# Clean up networks
echo "Step 2: Cleaning up networks..."
docker network prune -f

# Start only the essential services (without nginx)
echo "Step 3: Starting essential services..."
docker-compose up -d postgres redis

# Wait for PostgreSQL to be ready
echo "Step 4: Waiting for PostgreSQL to be ready..."
sleep 20

# Check if PostgreSQL is running
if docker exec eve-chatting-platform_postgres_1 pg_isready -U postgres >/dev/null 2>&1; then
    echo "✅ PostgreSQL is ready!"
else
    echo "❌ PostgreSQL is not ready. Checking logs..."
    docker logs eve-chatting-platform_postgres_1
    exit 1
fi

# Verify database data is still there
echo "Step 5: Verifying database data..."
docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c "SELECT COUNT(*) FROM users;"

# Start backend
echo "Step 6: Starting backend..."
docker-compose up -d backend

# Wait for backend to be ready
echo "Step 7: Waiting for backend to be ready..."
sleep 15

# Check backend health
if curl -s http://localhost:8001/health >/dev/null; then
    echo "✅ Backend is healthy!"
else
    echo "❌ Backend health check failed. Checking logs..."
    docker logs eve-chatting-platform_backend_1
fi

# Start celery worker
echo "Step 8: Starting celery worker..."
docker-compose up -d celery-worker

# Wait for celery to be ready
echo "Step 9: Waiting for celery worker to be ready..."
sleep 10

# Start frontend
echo "Step 10: Starting frontend..."
docker-compose up -d frontend

# Wait for frontend to be ready
echo "Step 11: Waiting for frontend to be ready..."
sleep 15

# Final status check
echo "Step 12: Final status check..."
docker-compose ps

echo ""
echo "🎉 Services should now be running!"
echo ""
echo "📋 Service Status:"
echo "   Backend API: http://your-vps-ip:8001"
echo "   Frontend: http://your-vps-ip:3000"
echo "   Admin Dashboard: http://your-vps-ip:3000/admin"
echo ""
echo "🔐 Admin Credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "📝 Useful Commands:"
echo "   View logs: docker-compose logs"
echo "   Check database: docker exec eve-chatting-platform_postgres_1 psql -U postgres -d chatting_platform -c 'SELECT COUNT(*) FROM users;'"
echo "   Restart services: docker-compose restart" 