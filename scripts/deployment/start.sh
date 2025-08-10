#!/bin/bash

echo "🚀 Starting Chatting Platform..."
echo "=================================="

# Configuration
VPS_IP="204.12.233.105"

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
DATABASE_URL=postgresql://adam%402025%40man:eve%40postgres%403241@postgres:5432/chatting_platform
REDIS_URL=redis://redis:6379/0
AI_MODEL_URL=http://ai-server:8000
SECRET_KEY=eve-super-secure-jwt-secret-key-2025-production
ADMIN_USERNAME=admin
ADMIN_PASSWORD=adam@and@eve@3241
EOF
    echo "✅ Created backend/.env with production configuration"
fi

# Check if frontend/.env.local exists
if [ ! -f "frontend/.env.local" ]; then
    echo "⚠️  frontend/.env.local not found. Creating default..."
    cat > frontend/.env.local << EOF
NEXT_PUBLIC_API_URL=http://$VPS_IP:8001
EOF
    echo "✅ Created frontend/.env.local with correct API URL"
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
    echo "   Frontend:        http://$VPS_IP:3000"
    echo "   Admin Dashboard: http://$VPS_IP:3000/admin (admin/adam@and@eve@3241)"
    echo "   Backend API:     http://$VPS_IP:8001"
    echo "   API Docs:        http://$VPS_IP:8001/docs"
    echo ""
    echo "🔍 To view logs: docker-compose logs"
    echo "🛑 To stop:      docker-compose down"
    echo ""
    echo "✅ Configuration is set for production VPS deployment!"
else
    echo "❌ Failed to start services. Check the logs:"
    docker-compose logs
    exit 1
fi