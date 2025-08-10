# 🚀 Chatting Platform - How to Run

## Prerequisites

1. **Docker & Docker Compose** installed on your system
2. **Git** (if cloning from repository)
3. **Your AI Model VPS URL** (Open-Hermes model endpoint)

## 📋 Quick Start Guide

### Step 1: Clone/Navigate to Project

```bash
cd /home/dev/Work/eve
```

### Step 2: Configure Environment Variables

#### Backend Configuration

Edit `backend/.env` and update:

```env
AI_MODEL_URL=http://your-vps-ip:port/v1/chat/completions
# Replace with your actual VPS URL where Open-Hermes is deployed
```

#### Frontend Configuration

Edit `frontend/.env.local` and verify:

```env
NEXT_PUBLIC_API_URL=http://204.12.233.105:8001
```

### Step 3: Start the Services

#### Option A: Start All Services (Recommended)

```bash
sudo docker-compose up -d
```

#### Option B: Start with Logs (for debugging)

```bash
sudo docker-compose up
```

#### Option C: Rebuild and Start (if you made changes)

```bash
sudo docker-compose up --build -d
```

### Step 4: Verify Services are Running

```bash
sudo docker-compose ps
```

You should see all 5 services running:

- ✅ postgres (healthy)
- ✅ redis (healthy)
- ✅ backend (up)
- ✅ celery-worker (up)
- ✅ frontend (up)

### Step 5: Access the Application

#### 🌐 Frontend (User Interface)

- **URL**: http://204.12.233.105:3000
- **Description**: Main chat interface where users interact

#### 👨‍💼 Admin Dashboard

- **URL**: http://204.12.233.105:3000/admin
- **Credentials**:
  - Username: `admin`
  - Password: `admin123`
- **Features**: Monitor conversations, intervene in chats, block users

#### 🔧 Backend API

- **URL**: http://204.12.233.105:8001
- **Docs**: http://204.12.233.105:8001/docs (Swagger UI)
- **Health Check**: http://204.12.233.105:8001/health

## 🧪 Testing the Setup

### Test 1: Backend Health

```bash
curl http://204.12.233.105:8001/health
```

Expected: `{"status": "healthy"}`

### Test 2: Tally Webhook (Simulate User Registration)

```bash
curl -X POST http://204.12.233.105:8001/webhook/tally \
  -H "Content-Type: application/json" \
  -d @tally_form.json
```

### Test 3: Frontend Access

Open browser and navigate to http://204.12.233.105:3000

### Test 4: Admin Login

1. Go to http://204.12.233.105:3000/admin
2. Login with admin/admin123
3. Check dashboard statistics

## 🔧 Troubleshooting

### Services Not Starting

```bash
# Check logs
sudo docker-compose logs [service-name]

# Restart specific service
sudo docker-compose restart [service-name]

# Rebuild if needed
sudo docker-compose build [service-name]
```

### Port Conflicts

If ports 3000, 8000, 5432, or 6379 are in use:

```bash
# Check what's using the ports
sudo ss -tlnp | grep -E ':(3000|8000|5432|6379)'

# Stop conflicting services or modify docker-compose.yml ports
```

### Database Issues

```bash
# Reset database
sudo docker-compose down -v
sudo docker-compose up -d
```

### Frontend Not Loading

```bash
# Check frontend logs
sudo docker-compose logs frontend

# Rebuild frontend
sudo docker-compose build frontend
sudo docker-compose restart frontend
```

## 📝 Configuration Details

### Environment Variables

#### Backend (.env)

```env
DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/chatting_platform
REDIS_URL=redis://redis:6379/0
AI_MODEL_URL=http://your-vps-ip:port/v1/chat/completions
SECRET_KEY=your-secret-key-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

#### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://204.12.233.105:8001
```

### Default Ports

- **Frontend**: 3000
- **Backend API**: 8000
- **PostgreSQL**: 5432
- **Redis**: 6379

## 🔄 Development Workflow

### Making Changes

1. **Backend Changes**: Files auto-reload (volume mounted)
2. **Frontend Changes**: Files auto-reload (volume mounted)
3. **Database Changes**: Run migrations or restart with `-v` flag

### Stopping Services

```bash
# Stop all services
sudo docker-compose down

# Stop and remove volumes (reset database)
sudo docker-compose down -v
```

### Viewing Logs

```bash
# All services
sudo docker-compose logs

# Specific service
sudo docker-compose logs backend
sudo docker-compose logs frontend
sudo docker-compose logs celery-worker
```

## 🌐 Production Deployment

### For VPS Deployment:

1. Update `AI_MODEL_URL` in docker-compose.yml
2. Update `NEXT_PUBLIC_API_URL` to your domain
3. Configure reverse proxy (nginx)
4. Set up SSL certificates
5. Use production database credentials
6. Set secure SECRET_KEY

### Tally Integration:

1. Set webhook URL to: `https://yourdomain.com/webhook/tally`
2. Configure webhook in your Tally form settings

## 📞 Support

If you encounter issues:

1. Check the logs: `sudo docker-compose logs`
2. Verify all services are healthy: `sudo docker-compose ps`
3. Ensure ports are not conflicting
4. Verify your AI model VPS is accessible

---

**🎉 Your chatting platform should now be running successfully!**
