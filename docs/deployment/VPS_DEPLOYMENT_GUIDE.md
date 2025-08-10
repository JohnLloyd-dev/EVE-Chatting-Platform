# 🚀 VPS Deployment Guide - EVE Chatting Platform

## Prerequisites on VPS

1. **Docker & Docker Compose installed**
2. **Git installed**
3. **Ports 80, 443, 3000, 8001 open**

## 📋 Step-by-Step Deployment

### 1. Clone the Repository

```bash
# SSH into your VPS
ssh root@your-vps-ip

# Clone the project
git clone https://github.com/JohnLloyd-dev/EVE-Chatting-Platform.git
cd EVE-Chatting-Platform
```

### 2. Configure Environment Variables

```bash
# Copy and edit the production environment file
cp .env.prod .env

# Edit the environment variables
nano .env
```

**Update these variables in `.env`:**

```env
# Replace with your VPS IP or domain
NEXT_PUBLIC_API_URL=http://204.12.233.105:8001

# Database settings (keep as is or customize)
DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/chatting_platform
REDIS_URL=redis://redis:6379/0

# AI Model settings (already configured)
AI_MODEL_URL=http://204.12.233.105:8000
AI_MODEL_AUTH_USERNAME=adam
AI_MODEL_AUTH_PASSWORD=eve2025
```

### 3. Update Docker Compose for Production

```bash
# Edit docker-compose.yml
nano docker-compose.yml
```

**Update the frontend environment:**

```yaml
frontend:
  # ... other settings ...
  environment:
    - NEXT_PUBLIC_API_URL=http://204.12.233.105:8001 # Replace with your VPS IP
```

### 4. Deploy with Docker

```bash
# Make deployment script executable
chmod +x run-docker.sh

# Run the deployment
./run-docker.sh

# Or manually with docker-compose
docker-compose up -d --build
```

### 5. Initialize Database

```bash
# Create database tables
docker exec backend python -c "
from database import Base, engine
Base.metadata.create_all(bind=engine)
print('Database tables created successfully!')
"
```

### 6. Verify Deployment

```bash
# Check all containers are running
docker ps

# Test the API
curl http://localhost:8001/docs

# Test user creation
curl -X POST http://localhost:8001/user/device-session \
  -H "Content-Type: application/json" \
  -d '{"device_id": "test-device", "custom_prompt": "Hello"}'
```

## 🌐 Access Your Application

- **Frontend**: `http://YOUR_VPS_IP:3000`
- **Backend API**: `http://YOUR_VPS_IP:8001`
- **API Documentation**: `http://YOUR_VPS_IP:8001/docs`
- **Admin Dashboard**: `http://YOUR_VPS_IP:3000/admin`

## 🔧 Production Optimizations (Optional)

### 1. Use Nginx Reverse Proxy

```bash
# Install Nginx
apt update && apt install nginx

# Copy our nginx config
cp nginx.conf /etc/nginx/sites-available/eve-chat
ln -s /etc/nginx/sites-available/eve-chat /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default

# Update nginx.conf with your domain
nano /etc/nginx/sites-available/eve-chat

# Restart nginx
systemctl restart nginx
```

### 2. SSL Certificate (Let's Encrypt)

```bash
# Install certbot
apt install certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d your-domain.com

# Auto-renewal
crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 Monitoring & Maintenance

### Check Logs

```bash
# Backend logs
docker logs backend

# Frontend logs
docker logs frontend

# Database logs
docker logs postgres
```

### Update Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose up -d --build
```

### Backup Database

```bash
# Create backup
docker exec postgres pg_dump -U postgres chatting_platform > backup.sql

# Restore backup
docker exec -i postgres psql -U postgres chatting_platform < backup.sql
```

## 🎯 User Experience

Your users will now have:

- **Simple IDs**: EVE001, EVE002, EVE003, etc.
- **Easy Access**: Just enter their user code to chat
- **Persistent Sessions**: Conversations saved and accessible
- **Admin Management**: Easy user identification and management

## 🆘 Troubleshooting

### Common Issues:

1. **Port conflicts**: Make sure ports 3000, 8001, 5432, 6379 are available
2. **Database connection**: Check DATABASE_URL in environment
3. **API not accessible**: Verify NEXT_PUBLIC_API_URL matches your VPS IP
4. **Containers not starting**: Check `docker logs container-name`

### Quick Fixes:

```bash
# Restart all services
docker-compose restart

# Rebuild everything
docker-compose down
docker-compose up -d --build

# Check container status
docker ps -a
```

## ✅ Deployment Complete!

Your EVE Chatting Platform is now live on your VPS with:

- ✅ Docker containerization
- ✅ Simple user codes (EVE001, EVE002...)
- ✅ Full chat functionality
- ✅ Admin dashboard
- ✅ Production-ready setup

Users can now access your platform and get memorable user IDs instead of complex UUIDs!
