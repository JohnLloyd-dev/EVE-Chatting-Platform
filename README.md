# EVE Chat Platform

A modern chat platform with AI integration, built with FastAPI, Next.js, PostgreSQL, and Redis.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/JohnLloyd-dev/EVE-Chatting-Platform.git
cd EVE-Chatting-Platform

# Deploy everything
chmod +x deploy.sh
./deploy.sh
```

## 📋 Services

- **Frontend**: Next.js application (Port 3000)
- **Backend**: FastAPI REST API (Port 8001)
- **AI Server**: Custom AI model server (Port 8000)
- **Database**: PostgreSQL (Port 5432)
- **Cache**: Redis (Port 6379)

## 🔧 AI Integration

The platform includes a custom AI server running the OpenHermes-2.5-Mistral-7B model with:
- 4-bit quantization for memory efficiency
- ChatML format support
- Session-based conversation history
- Token-based history trimming
- HTTP Basic authentication

## 📁 Project Structure

```
├── frontend/          # Next.js frontend application
├── backend/           # FastAPI backend API
├── ai_server/         # Custom AI model server
├── docs/              # Documentation and deployment files
├── deploy.sh          # Main deployment script
├── troubleshoot.sh    # Troubleshooting script
└── docker-compose.yml # Docker services configuration
```

## 🌐 Access URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **AI Server**: http://localhost:8000

## 🔐 Authentication

- **AI Server**: Username: `adam`, Password: `eve2025`
- **Admin Dashboard**: Username: `admin`, Password: `admin123`

## 🛠️ Troubleshooting

```bash
# Check service status
./troubleshoot.sh

# View logs
docker-compose logs [service_name]

# Restart services
docker-compose restart [service_name]
```

## 📚 Documentation

For detailed setup and deployment instructions, see the `docs/` directory.

## 🔄 Deployment

The `deploy.sh` script handles:
- Database restoration from backup
- Service building and startup
- Health checks and verification
- AI model loading and initialization

## 🚨 Requirements

- Docker and Docker Compose
- NVIDIA GPU with CUDA support (for AI server)
- At least 16GB RAM (8GB for AI model)
- 50GB+ free disk space
