# 🚀 EVE Chat Platform - Deployment Guide

## Quick Deployment

### Prerequisites

- Docker and Docker Compose installed
- Git installed
- `final123.sql` database backup file (optional)

### One-Command Deployment

```bash
# 1. Clone the repository
git clone https://github.com/JohnLloyd-dev/EVE-Chatting-Platform.git
cd EVE-Chatting-Platform

# 2. Make the deployment script executable
chmod +x deploy.sh

# 3. Run the deployment script
./deploy.sh
```

That's it! The script will handle everything automatically.

## What the Deployment Script Does

1. **Pulls latest changes** from GitHub
2. **Stops all containers** and cleans up
3. **Restores database** from `final123.sql` (if available)
4. **Starts PostgreSQL** and Redis
5. **Builds and starts backend** with CORS fixes
6. **Builds and starts frontend** with external access
7. **Starts Celery worker** for background tasks
8. **Tests all services** and verifies connectivity
9. **Shows final status** with access URLs

## Access URLs

After deployment, you can access:

- **Frontend**: http://204.12.233.105:3000
- **Backend API**: http://204.12.233.105:8001
- **Admin Dashboard**: http://204.12.233.105:3000/admin

## Admin Credentials

- **Username**: admin
- **Password**: admin123

## Troubleshooting

### If deployment fails:

```bash
# Check container status
docker ps

# Check logs for specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres

# Restart specific service
docker-compose restart backend
docker-compose restart frontend

# Rebuild specific service
docker-compose build backend
docker-compose build frontend
```

### If services are not accessible:

```bash
# Check firewall status
sudo ufw status

# Allow ports if needed
sudo ufw allow 3000
sudo ufw allow 8001

# Check if ports are listening
netstat -tlnp | grep 3000
netstat -tlnp | grep 8001
```

### If database issues:

```bash
# Check database connection
docker exec eve-chatting-platform_postgres_1 pg_isready -U "adam@2025@man"

# Check database logs
docker-compose logs postgres
```

## Manual Deployment (Alternative)

If you prefer manual deployment:

```bash
# 1. Pull changes
git pull origin main

# 2. Stop all services
docker-compose down

# 3. Start services in order
docker-compose up -d postgres
sleep 15
docker-compose up -d redis
docker-compose up -d backend
sleep 20
docker-compose up -d celery-worker
docker-compose up -d frontend

# 4. Check status
docker ps
```

## Configuration

The deployment uses these default configurations:

- **Database User**: adam@2025@man
- **Database Password**: eve@postgres@3241
- **Backend Port**: 8001
- **Frontend Port**: 3000
- **VPS IP**: 204.12.223.76

## Security Features

The deployment includes:

- ✅ CORS configuration for frontend-backend communication
- ✅ External access for frontend
- ✅ Database security with restricted access
- ✅ Firewall configuration
- ✅ Secure environment variables

## Project Structure

```
├── backend/                 # FastAPI backend
├── frontend/               # Next.js frontend
├── docs/                   # Documentation
│   ├── deployment/         # Deployment guides (this folder)
│   ├── security/           # Security documentation
│   ├── testing/            # Test files
│   └── guides/             # General guides
├── old_scripts/            # Legacy scripts
├── deploy.sh              # Main deployment script
├── troubleshoot.sh        # Troubleshooting script
├── docker-compose.yml     # Docker configuration
└── README.md              # Main project README
```

## Support

If you encounter issues:

1. Check the logs: `docker-compose logs [service_name]`
2. Verify firewall settings: `sudo ufw status`
3. Test connectivity: `curl http://localhost:8001/health`
4. Check container status: `docker ps`
5. Run troubleshooting script: `./troubleshoot.sh`

## Related Documentation

- **[Security Documentation](../security/FINAL_SECURITY_SUMMARY.md)** - Security features and configuration
- **[VPS Setup Guide](VPS_SETUP_GUIDE.md)** - VPS-specific setup instructions
- **[Main README](../../README.md)** - Project overview and quick start
