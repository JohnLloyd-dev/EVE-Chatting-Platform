# EVE Chatting Platform - Project Structure

## 📁 Directory Structure

```
eve/
├── 📁 backend/                     # FastAPI Backend
│   ├── 🐳 Dockerfile
│   ├── ⚙️ main.py                  # Main FastAPI application
│   ├── 🗄️ database.py             # Database models & connection
│   ├── 🔐 auth.py                  # Authentication utilities
│   ├── ⚙️ config.py                # Configuration settings
│   ├── 📋 schemas.py               # Pydantic schemas
│   ├── 🔄 celery_app.py            # Celery configuration
│   ├── 📦 requirements.txt         # Python dependencies
│   └── 🔧 .env                     # Environment variables
│
├── 📁 frontend/                    # Next.js Frontend
│   ├── 🐳 Dockerfile
│   ├── 📁 pages/                   # Next.js pages
│   ├── 📁 components/              # React components
│   ├── 📁 lib/                     # Utility libraries
│   ├── 📁 styles/                  # CSS styles
│   ├── 📁 types/                   # TypeScript types
│   ├── 📦 package.json             # Node.js dependencies
│   └── ⚙️ next.config.js           # Next.js configuration
│
├── 📁 scripts/                     # Utility Scripts
│   ├── 📁 admin/                   # Admin management scripts
│   │   ├── fix_admin.py            # Create/fix admin user
│   │   └── fix_admin_password.py   # Reset admin password
│   │
│   ├── 📁 migration/               # Database migration scripts
│   │   ├── migrate_user_codes.py   # Full migration script
│   │   └── simple_user_codes.py    # Simple user code assignment
│   │
│   ├── 📁 testing/                 # Test scripts
│   │   ├── test_setup.py           # Complete system test
│   │   ├── test_user_chat.py       # Chat functionality test
│   │   ├── test_server.py          # Server test
│   │   └── main.py                 # Legacy test script
│   │
│   ├── 📁 deployment/              # Deployment scripts
│   │   ├── deploy.sh               # Main deployment script
│   │   ├── start.sh                # Start services script
│   │   ├── test.sh                 # Test deployment script
│   │   └── get-docker.sh           # Docker installation script
│   │
│   ├── 📁 utils/                   # Utility scripts
│   │   ├── user_scenario_manager.py # User & scenario management
│   │   ├── demo_user_management.py # Demo user creation
│   │   └── extract_tally.py        # Tally form data extraction
│   │
│   └── 📁 data/                    # Data files
│       ├── init.sql                # Database initialization
│       ├── tally_form.json         # Sample Tally form data
│       └── test_user.json          # Test user data
│
├── 📁 tests/                       # Test files
│   └── 📁 html/                    # HTML test files
│       └── test_chat_interface.html # Chat interface test
│
├── 📁 docs/                        # Documentation
│   ├── 📁 deployment/              # Deployment documentation
│   │   └── DEPLOYMENT_STATUS.md    # Deployment status
│   ├── GITHUB_PUSH_SUMMARY.md      # Git push summary
│   ├── RUN_INSTRUCTIONS.md         # How to run the project
│   └── USER_SCENARIO_MANAGEMENT.md # User scenario docs
│
├── 🐳 docker-compose.yml           # Docker Compose configuration
├── 📋 README.md                    # Project overview
├── 🔧 .gitignore                   # Git ignore rules
└── 📁 PROJECT_STRUCTURE.md         # This file
```

## 🚀 Quick Start

### 1. Development Setup

```bash
# Clone and navigate
git clone <repository-url>
cd eve

# Start services
docker-compose up -d

# Run migration (if needed)
docker exec eve-chatting-platform_backend_1 python /app/scripts/migration/simple_user_codes.py

# Create admin user
docker exec eve-chatting-platform_backend_1 python /app/scripts/admin/fix_admin.py
```

### 2. Testing

```bash
# Test complete setup
docker exec eve-chatting-platform_backend_1 python /app/scripts/testing/test_setup.py

# Test user chat functionality
docker exec eve-chatting-platform_backend_1 python /app/scripts/testing/test_user_chat.py

# Test user scenario management
docker exec eve-chatting-platform_backend_1 python /app/scripts/utils/user_scenario_manager.py
```

### 3. Admin Management

```bash
# Fix admin user
docker exec eve-chatting-platform_backend_1 python /app/scripts/admin/fix_admin.py

# Reset admin password
docker exec eve-chatting-platform_backend_1 python /app/scripts/admin/fix_admin_password.py
```

## 🔧 Key Components

### Backend (FastAPI)

- **API Endpoints**: Chat, Admin, Webhook
- **Database**: PostgreSQL with SQLAlchemy
- **Background Tasks**: Celery with Redis
- **Authentication**: JWT tokens

### Frontend (Next.js)

- **Pages**: Chat interface, Admin dashboard
- **Components**: Reusable React components
- **API Integration**: Axios for backend communication

### Scripts

- **Migration**: Database schema updates
- **Testing**: Automated testing scripts
- **Admin**: User management utilities
- **Deployment**: Production deployment tools

## 📱 Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Admin Dashboard**: http://localhost:3000/admin
- **API Docs**: http://localhost:8000/docs

## 🔐 Default Credentials

- **Admin Username**: admin
- **Admin Password**: admin123

## 📊 Database Tables

- **users**: User accounts and profiles
- **chat_sessions**: Chat sessions with AI
- **messages**: Chat messages and responses
- **admin_users**: Admin user accounts

## 🤖 AI Integration

- **AI Model URL**: Configurable in backend/.env
- **Authentication**: Basic auth (adam/eve2025)
- **Scenario Setting**: Dynamic AI personality configuration
- **Session Management**: Cookie-based AI sessions
