#!/bin/bash

echo "🚀 Starting Chatting Platform..."
echo "=================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "❌ docker-compose not found. Please install docker-compose."
    exit 1
fi

# Navigate to project directory
cd "$(dirname "$0")"

echo "📋 Checking configuration..."

# Check if backend/.env exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  backend/.env not found. Creating default..."
    cat > backend/.env << EOF
DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/chatting_platform
REDIS_URL=redis://redis:6379/0
AI_MODEL_URL=http://your-vps-ip:port/v1/chat/completions
SECRET_KEY=your-secret-key-change-this-in-production
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
EOF
    echo "✅ Created backend/.env - Please update AI_MODEL_URL with your VPS URL"
fi

# Check if frontend/.env.local exists
if [ ! -f "frontend/.env.local" ]; then
    echo "⚠️  frontend/.env.local not found. Creating default..."
    cat > frontend/.env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
    echo "✅ Created frontend/.env.local"
fi

echo "🐳 Starting Docker services..."

# Start services
if docker-compose up -d; then
    echo ""
    echo "✅ Services started successfully!"
    echo ""
    echo "📊 Service Status:"
    docker-compose ps
    echo ""
    echo "🌐 Access URLs:"
    echo "   Frontend:        http://localhost:3000"
    echo "   Admin Dashboard: http://localhost:3000/admin (admin/admin123)"
    echo "   Backend API:     http://localhost:8000"
    echo "   API Docs:        http://localhost:8000/docs"
    echo ""
    echo "🔍 To view logs: docker-compose logs"
    echo "🛑 To stop:      docker-compose down"
    echo ""
    echo "⚠️  Don't forget to update AI_MODEL_URL in backend/.env with your VPS URL!"
else
    echo "❌ Failed to start services. Check the logs:"
    docker-compose logs
    exit 1
fi