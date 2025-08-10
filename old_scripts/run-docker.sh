#!/bin/bash

# Configuration
VPS_IP="204.12.233.105"

# Create network
docker network create eve-network 2>/dev/null || true

# Stop and remove existing containers
docker stop postgres redis backend frontend celery-worker 2>/dev/null || true
docker rm postgres redis backend frontend celery-worker 2>/dev/null || true

# Start PostgreSQL
echo "Starting PostgreSQL..."
docker run -d --name postgres --network eve-network \
  -e POSTGRES_DB=chatting_platform \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres123 \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15

# Start Redis
echo "Starting Redis..."
docker run -d --name redis --network eve-network \
  -p 6379:6379 \
  redis:7-alpine

# Wait for databases to be ready
echo "Waiting for databases to be ready..."
sleep 10

# Build and start backend
echo "Building backend..."
cd backend
docker build -t eve-backend .
cd ..

echo "Starting backend..."
docker run -d --name backend --network eve-network \
  -p 8001:8000 \
  -e DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/chatting_platform \
  -e REDIS_URL=redis://redis:6379/0 \
  -e AI_MODEL_URL=http://204.12.223.76:8000 \
  -e AI_MODEL_AUTH_USERNAME=adam \
  -e AI_MODEL_AUTH_PASSWORD=eve2025 \
  -v $(pwd)/backend:/app \
  eve-backend uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Start Celery worker
echo "Starting Celery worker..."
docker run -d --name celery-worker --network eve-network \
  -e DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/chatting_platform \
  -e REDIS_URL=redis://redis:6379/0 \
  -e AI_MODEL_URL=http://204.12.223.76:8000 \
  -e AI_MODEL_AUTH_USERNAME=adam \
  -e AI_MODEL_AUTH_PASSWORD=eve2025 \
  -v $(pwd)/backend:/app \
  eve-backend celery -A celery_app worker --loglevel=info

# Build and start frontend
echo "Building frontend..."
cd frontend
docker build -t eve-frontend .
cd ..

echo "Starting frontend..."
docker run -d --name frontend --network eve-network \
  -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://$VPS_IP:8001 \
  -v $(pwd)/frontend:/app \
  -v /app/node_modules \
  eve-frontend npm run dev

echo "All services started!"
echo "Frontend: http://$VPS_IP:3000"
echo "Backend: http://$VPS_IP:8001"
echo "Admin: http://$VPS_IP:3000/admin"