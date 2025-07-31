# VPS Deployment Commands

## Summary

The AI response control feature has been successfully implemented and pushed to the repository. Here are the commands to deploy it on your VPS:

## Commands to Run on VPS

### 1. Navigate to project directory and pull changes

```bash
cd /path/to/your/eve/project
git pull origin main
```

### 2. Run the database migration

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

### 3. Restart the services

```bash
docker compose restart backend celery-worker frontend
```

### 4. Verify deployment

```bash
# Check if services are running
docker compose ps

# Check backend logs
docker compose logs backend

# Check if the new API endpoint is working
curl -X GET http://localhost:8001/health
```

## What's New

### Admin Interface

- New "Enable AI" / "Disable AI" button next to the "Block User" button
- "AI Disabled" badge in the conversation list for users with disabled AI
- Separate control for AI responses vs user blocking

### Backend Changes

- New API endpoint: `POST /admin/toggle-ai-responses`
- AI model no longer receives admin messages in conversation context
- Users with disabled AI won't get AI responses but can still send messages

### Testing

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
