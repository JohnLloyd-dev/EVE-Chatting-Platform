# EVE Chat Platform - VPS Deployment Guide

## 🚀 Quick VPS Deployment

This guide will help you deploy the EVE Chat Platform to your VPS and restore the database from `final123.sql`.

## 📋 Prerequisites

- VPS with Ubuntu 20.04+ or similar Linux distribution
- Docker and Docker Compose installed
- Git installed
- At least 2GB RAM and 10GB storage

## 🔧 Step 1: Install Dependencies on VPS

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git
sudo apt install git -y

# Logout and login again for Docker group to take effect
exit
# SSH back into your VPS
```

## 📥 Step 2: Clone and Deploy

```bash
# Clone the repository
git clone <your-repo-url>
cd eve

# Make the deployment script executable
chmod +x deploy_to_vps.sh

# Run the deployment script
./deploy_to_vps.sh
```

## 🔄 Alternative: Manual Deployment

If you prefer to deploy manually, follow these steps:

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd eve
```

### 2. Ensure final123.sql is present

```bash
ls -la final123.sql
```

### 3. Start Services

```bash
# Start all services with production configuration
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Restore Database

```bash
# Run the database restoration script
chmod +x restore_final123.sh
./restore_final123.sh
```

## 🌐 Step 3: Configure Firewall

```bash
# Allow necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 3000/tcp  # Frontend
sudo ufw allow 8001/tcp  # Backend API
sudo ufw enable
```

## 🔧 Step 4: Environment Configuration

Create a `.env.prod` file for production settings:

```bash
# Create production environment file
cat > .env.prod << EOF
POSTGRES_PASSWORD=your-secure-password
AI_MODEL_URL=http://your-ai-vps-ip:8000
AI_MODEL_AUTH_USERNAME=adam
AI_MODEL_AUTH_PASSWORD=eve2025
JWT_SECRET_KEY=your-very-long-and-random-secret-key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
NEXT_PUBLIC_API_URL=http://your-vps-ip:8001
EOF
```

## ✅ Step 5: Verify Deployment

### Check Services

```bash
# Check if all containers are running
docker ps

# Check service logs
docker-compose -f docker-compose.prod.yml logs

# Test backend health
curl http://localhost:8001/health

# Test frontend
curl -I http://localhost:3000
```

### Check Database

```bash
# Verify database restoration
docker exec eve-postgres-1 psql -U postgres -d chatting_platform -c "SELECT COUNT(*) FROM users;"
```

## 🌐 Access Points

Once deployed, your application will be available at:

- **Frontend**: `http://your-vps-ip:3000`
- **Backend API**: `http://your-vps-ip:8001`
- **Admin Dashboard**: `http://your-vps-ip:3000/admin`
- **API Documentation**: `http://your-vps-ip:8001/docs`

## 🔐 Admin Access

- **Username**: `admin`
- **Password**: `admin123`

## 📊 Database Status

After restoration, you should have:

- ✅ 16 users (EVE001-EVE016)
- ✅ 16 chat sessions
- ✅ 259 messages
- ✅ 1 admin user
- ✅ 16 Tally submissions
- ✅ 2 system prompts
- ✅ 62 active AI tasks

## 🔧 Troubleshooting

### Common Issues

1. **Port Already in Use**

   ```bash
   # Check what's using the port
   sudo netstat -tulpn | grep :3000
   # Kill the process or change ports in docker-compose.prod.yml
   ```

2. **Database Connection Failed**

   ```bash
   # Check PostgreSQL logs
   docker logs eve-postgres-1
   # Restart PostgreSQL
   docker restart eve-postgres-1
   ```

3. **Frontend Not Loading**

   ```bash
   # Check frontend logs
   docker logs eve-frontend-1
   # Rebuild frontend
   docker-compose -f docker-compose.prod.yml build frontend
   ```

4. **Backend API Errors**
   ```bash
   # Check backend logs
   docker logs eve-backend-1
   # Check AI model connection
   curl http://your-ai-vps-ip:8000/health
   ```

### Useful Commands

```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend

# Check database
docker exec eve-postgres-1 psql -U postgres -d chatting_platform -c '\dt'

# Backup database
docker exec eve-postgres-1 pg_dump -U postgres chatting_platform > backup_$(date +%Y%m%d_%H%M%S).sql

# Update application
git pull
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

## 🔒 Security Recommendations

1. **Change Default Passwords**

   - Update admin password
   - Use strong PostgreSQL password
   - Generate secure JWT secret

2. **SSL/HTTPS Setup**

   ```bash
   # Install Certbot for Let's Encrypt
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

3. **Firewall Configuration**
   ```bash
   # Only allow necessary ports
   sudo ufw default deny incoming
   sudo ufw default allow outgoing
   sudo ufw allow ssh
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

## 📞 Support

If you encounter issues:

1. Check the logs: `docker-compose -f docker-compose.prod.yml logs`
2. Verify all prerequisites are installed
3. Ensure `final123.sql` is in the project directory
4. Check firewall and port configurations

Your EVE Chat Platform should now be fully operational on your VPS! 🎉
