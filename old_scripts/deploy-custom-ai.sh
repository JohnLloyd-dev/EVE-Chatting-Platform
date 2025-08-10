#!/bin/bash

# Deploy Custom AI Server to VPS
# This script deploys the custom AI server with GPU support

set -e

echo "🤖 Deploying Custom AI Server"
echo "============================="

# Configuration
VPS_IP="204.12.233.105"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if NVIDIA Docker runtime is available (for GPU support)
if ! docker info | grep -q nvidia; then
    echo "⚠️  NVIDIA Docker runtime not detected. GPU acceleration may not work."
    echo "   Install nvidia-docker2 for GPU support."
fi

# Create .env.prod file if it doesn't exist
if [ ! -f .env.prod ]; then
    echo "📝 Creating .env.prod file..."
    cat > .env.prod << EOF
# Database
POSTGRES_PASSWORD=postgres123

# AI Model Configuration
AI_MODEL_URL=http://custom-ai-server:8000
AI_MODEL_AUTH_USERNAME=adam
AI_MODEL_AUTH_PASSWORD=eve2025

# Admin Configuration
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# Security
JWT_SECRET_KEY=$(openssl rand -base64 32)

# Frontend
NEXT_PUBLIC_API_URL=http://$VPS_IP:8001
EOF
    echo "✅ Created .env.prod file"
fi

# Create environment file for frontend
cat > frontend/.env.local << EOF
NEXT_PUBLIC_API_URL=http://$VPS_IP:8001
EOF

# Build and start the custom AI server
echo "🔨 Building Custom AI Server..."
docker-compose -f docker-compose.prod.yml build custom-ai-server

echo "🚀 Starting Custom AI Server..."
docker-compose -f docker-compose.prod.yml up -d custom-ai-server

# Wait for AI server to be ready
echo "⏳ Waiting for AI server to be ready..."
while ! curl -s http://$VPS_IP:8002/ > /dev/null; do
    echo "   Waiting for AI server..."
    sleep 5
done

echo "✅ Custom AI deployment completed!"
echo ""
echo "🌐 Access URLs:"
echo "   - Custom AI Server: http://$VPS_IP:8002"
echo "   - Chat Interface: http://$VPS_IP:8002/"
echo "   - Test Interface: http://$VPS_IP:8002/test-bot"
echo ""
echo "📊 To check logs:"
echo "   docker-compose -f docker-compose.prod.yml logs -f custom-ai-server"
echo ""
echo "🛑 To stop:"
echo "   docker-compose -f docker-compose.prod.yml down"
echo ""
echo "🎉 Deployment complete!"