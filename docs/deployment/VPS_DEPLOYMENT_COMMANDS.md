# VPS Deployment Commands

## Summary

The Custom AI Server with Docker integration has been successfully implemented and pushed to the repository. This includes the AI response control feature and the new custom AI server. Here are the commands to deploy it on your VPS:

## Commands to Run on VPS

### 1. Navigate to project directory and pull changes

```bash
cd /path/to/your/eve/project
git pull origin main
```

### 2. Deploy Custom AI Server (NEW!)

```bash
# Make deployment script executable
chmod +x deploy-custom-ai.sh

# Deploy the custom AI server
./deploy-custom-ai.sh
```

**Alternative manual deployment:**

```bash
# Build and start custom AI server
docker-compose -f docker-compose.prod.yml build custom-ai-server
docker-compose -f docker-compose.prod.yml up -d custom-ai-server
```

### 3. Run the database migration

```bash
# Option A: Using the comprehensive Python migration script (recommended)
docker compose exec backend python run_migration.py

# Option B: Manual SQL commands to create missing tables (if Option A doesn't work)
docker compose exec postgres psql -U postgres -d chatting_platform -c "
-- Add ai_responses_enabled column
ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_responses_enabled BOOLEAN DEFAULT TRUE;

-- Create active_ai_tasks table
CREATE TABLE IF NOT EXISTS active_ai_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(255) UNIQUE NOT NULL,
    session_id UUID NOT NULL REFERENCES chat_sessions(id),
    user_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_cancelled BOOLEAN DEFAULT FALSE
);

-- Create system_prompts table if missing
CREATE TABLE IF NOT EXISTS system_prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    admin_id UUID REFERENCES admin_users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id UUID REFERENCES users(id)
);
"
```

### 4. Restart the services

```bash
docker compose restart backend celery-worker frontend
```

### 5. Verify deployment

```bash
# Check if services are running
docker compose ps

# Check backend logs
docker compose logs backend

# Check if the new API endpoint is working
curl -X GET http://localhost:8001/health

# Check Custom AI Server (NEW!)
curl http://localhost:8002/
docker-compose -f docker-compose.prod.yml logs -f custom-ai-server
```

## What's New

### Custom AI Server (NEW!)

- **Standalone AI Server**: `custom_server.py` with FastAPI and transformers
- **Docker Integration**: Containerized with GPU support
- **Web Interfaces**: Chat interface at `:8002/` and test interface at `:8002/test-bot`
- **API Endpoints**: `/scenario`, `/chat`, `/tally-scenario`
- **Authentication**: Built-in HTTP Basic Auth (adam/eve2025)
- **Memory Optimized**: 4-bit quantization for efficient GPU usage

### Admin Interface

- New "Enable AI" / "Disable AI" button next to the "Block User" button
- "AI Disabled" badge in the conversation list for users with disabled AI
- Separate control for AI responses vs user blocking

### Backend Changes

- New API endpoint: `POST /admin/toggle-ai-responses`
- AI model no longer receives admin messages in conversation context
- Users with disabled AI won't get AI responses but can still send messages

### Testing

**Custom AI Server:**

1. Visit `http://your-vps-ip:8002/` for chat interface
2. Visit `http://your-vps-ip:8002/test-bot` for test interface
3. Test authentication with adam/eve2025
4. Set scenarios and test chat functionality

**Admin Interface:**

1. Go to admin panel → Conversations
2. Select a conversation
3. You should see both "Block User" and "Enable/Disable AI" buttons
4. Test toggling AI responses
5. Send admin messages and verify they don't appear in AI context

## Troubleshooting

If migration fails:

```bash
# Check database connection
docker compose exec postgres psql -U postgres -d chatting_platform -c "SELECT version();"

# Manual column addition if needed
docker compose exec postgres psql -U postgres -d chatting_platform -c "ALTER TABLE users ADD COLUMN ai_responses_enabled BOOLEAN DEFAULT TRUE;"
```

If services don't start:

```bash
# Check logs
docker compose logs backend
docker compose logs celery-worker
docker compose logs frontend

# Rebuild if needed
docker compose build --no-cache
docker compose up -d
```
