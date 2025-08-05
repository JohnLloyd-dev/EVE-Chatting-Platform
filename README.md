# 🚀 EVE Chat Platform

A modern chat platform with AI-powered responses, admin dashboard, and comprehensive security features.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Git
- `final123.sql` database backup (optional)

### Deploy in One Command

```bash
# Clone the repository
git clone https://github.com/JohnLloyd-dev/EVE-Chatting-Platform.git
cd EVE-Chatting-Platform

# Deploy everything
chmod +x deploy.sh
./deploy.sh
```

## 🌐 Access URLs

After deployment:

- **Frontend**: http://204.12.223.76:3000
- **Backend API**: http://204.12.223.76:8001
- **Admin Dashboard**: http://204.12.223.76:3000/admin

## 🔐 Admin Credentials

- **Username**: admin
- **Password**: admin123

## 🏗️ Architecture

- **Frontend**: Next.js with TypeScript
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Cache**: Redis
- **Background Tasks**: Celery
- **Containerization**: Docker & Docker Compose

## 📁 Project Structure

```
├── backend/                 # FastAPI backend
├── frontend/               # Next.js frontend
├── docs/                   # Documentation
│   ├── deployment/         # Deployment guides
│   ├── security/           # Security documentation
│   ├── testing/            # Test files
│   └── guides/             # General guides
├── old_scripts/            # Legacy scripts
├── deploy.sh              # Main deployment script
├── troubleshoot.sh        # Troubleshooting script
├── docker-compose.yml     # Docker configuration
└── README.md              # This file
```

## 🔧 Troubleshooting

If you encounter issues:

```bash
# Run the troubleshooting script
./troubleshoot.sh

# Check service logs
docker-compose logs [service_name]

# Restart services
docker-compose restart
```

## 📚 Documentation

- **[Deployment Guide](docs/deployment/DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[Security Documentation](docs/security/FINAL_SECURITY_SUMMARY.md)** - Security features and configuration
- **[VPS Setup Guide](docs/deployment/VPS_SETUP_GUIDE.md)** - VPS-specific setup instructions

## 🛡️ Security Features

- ✅ CORS configuration
- ✅ External access control
- ✅ Database security
- ✅ Firewall configuration
- ✅ Environment variable protection
- ✅ Input validation
- ✅ Rate limiting

## 🚀 Features

- **AI-Powered Chat**: Intelligent responses using AI models
- **Admin Dashboard**: User management and conversation monitoring
- **Real-time Messaging**: WebSocket-based communication
- **Background Processing**: Celery for async tasks
- **Database Management**: PostgreSQL with backup/restore
- **Containerized**: Easy deployment with Docker

## 🤝 Support

For issues or questions:

1. Check the troubleshooting script: `./troubleshoot.sh`
2. Review the deployment guide: `docs/deployment/DEPLOYMENT_GUIDE.md`
3. Check service logs: `docker-compose logs [service_name]`

## 📄 License

This project is proprietary software.
