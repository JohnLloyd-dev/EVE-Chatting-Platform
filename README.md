# Chatting Platform

A comprehensive chatting platform that integrates with Tally forms and uses Open-Hermes AI model for conversations.

## Architecture

- **Backend**: FastAPI with PostgreSQL database
- **Frontend**: Next.js with TypeScript and Tailwind CSS
- **AI Integration**: Open-Hermes model via API
- **Background Tasks**: Celery with Redis
- **Containerization**: Docker & Docker Compose

## Features

### User Features

- Automatic user registration via Tally form webhook
- AI-powered chat sessions based on form responses
- Real-time messaging interface
- Scenario-based conversations

### Admin Features

- Dashboard with statistics and overview
- Real-time conversation monitoring
- Admin intervention in conversations
- User blocking/unblocking
- Message history tracking

## 📚 Documentation

- **[Setup Instructions](RUN_INSTRUCTIONS.md)** - Complete deployment guide
- **[User & Scenario Management](USER_SCENARIO_MANAGEMENT.md)** - How users and AI scenarios are managed

## Setup Instructions

### Prerequisites

- Docker and Docker Compose
- Your Open-Hermes model deployed on VPS

### 1. Environment Configuration

Update the following files with your specific configuration:

**Backend (.env)**:

```bash
# Update with your VPS details
AI_MODEL_URL=http://your-vps-ip:port
AI_MODEL_AUTH_USERNAME=adam
AI_MODEL_AUTH_PASSWORD=eve2025

# Generate a secure secret key
SECRET_KEY=your-very-long-and-random-secret-key
```

**Docker Compose**:
Update the `AI_MODEL_URL` in `docker-compose.yml` with your VPS URL.

### 2. Start the Application

```bash
# Clone and navigate to project
cd /home/dev/Work/eve

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Admin Dashboard**: http://localhost:3000/admin
  - Username: `admin`
  - Password: `admin123`

### 4. Tally Integration

Set up your Tally form webhook to point to:

```
http://your-domain:8000/webhook/tally
```

## API Endpoints

### Public Endpoints

- `POST /webhook/tally` - Tally form webhook
- `GET /chat/session/{user_id}` - Get user chat session
- `POST /chat/message/{session_id}` - Send message
- `GET /chat/response/{task_id}` - Check AI response status

### Admin Endpoints

- `POST /admin/login` - Admin login
- `GET /admin/conversations` - Get all conversations
- `GET /admin/conversation/{session_id}` - Get conversation details
- `POST /admin/intervene` - Send admin intervention
- `POST /admin/block-user` - Block/unblock user
- `GET /admin/stats` - Dashboard statistics

## Database Schema

The application uses PostgreSQL with the following main tables:

- `users` - User information from Tally forms
- `chat_sessions` - Chat sessions with AI scenarios
- `messages` - All chat messages
- `admin_users` - Admin user accounts
- `tally_submissions` - Raw Tally form data

## Development

### Backend Development

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Celery Worker

```bash
cd backend
celery -A celery_app worker --loglevel=info
```

## Production Deployment

1. Update environment variables for production
2. Use production-grade PostgreSQL and Redis instances
3. Set up proper SSL certificates
4. Configure reverse proxy (nginx)
5. Set up monitoring and logging

## Tally Form Integration

The system expects Tally webhooks with the following structure:

```json
{
  "eventId": "uuid",
  "eventType": "FORM_RESPONSE",
  "createdAt": "timestamp",
  "data": {
    "responseId": "string",
    "respondentId": "string",
    "formId": "string",
    "fields": [...]
  }
}
```

The `extract_tally.py` module processes this data to generate AI scenarios.

## Monitoring

- Check service health: `GET /health`
- Monitor Celery tasks via Redis
- Database connection status in admin dashboard
- Real-time conversation monitoring

## Security

- JWT-based admin authentication
- Password hashing with bcrypt
- SQL injection protection via SQLAlchemy
- CORS configuration for frontend
- Input validation and sanitization

## Troubleshooting

### Common Issues

1. **AI Model Connection Failed**

   - Check VPS is running and accessible
   - Verify AI_MODEL_URL in environment
   - Check authentication credentials

2. **Database Connection Error**

   - Ensure PostgreSQL container is running
   - Check DATABASE_URL configuration
   - Verify database initialization

3. **Celery Tasks Not Processing**

   - Check Redis connection
   - Verify Celery worker is running
   - Check task queue status

4. **Frontend API Calls Failing**
   - Check NEXT_PUBLIC_API_URL configuration
   - Verify backend is running on correct port
   - Check CORS settings

### Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs celery-worker
```
