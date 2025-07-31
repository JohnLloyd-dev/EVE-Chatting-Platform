# AI Response Control Feature - Deployment Guide

## Overview

This update adds the ability to disable/enable AI model responses for individual users, separate from the user blocking functionality. It also fixes the issue where admin messages were being included in the AI model's conversation context.

## Changes Made

### Backend Changes

1. **Database Schema**: Added `ai_responses_enabled` column to `users` table
2. **API Endpoints**: Added `/admin/toggle-ai-responses` endpoint
3. **AI Processing**: Modified to exclude admin messages from AI context
4. **Celery Worker**: Added check for AI responses enabled before processing

### Frontend Changes

1. **Admin Interface**: Added AI toggle button next to block user button
2. **Visual Indicators**: Added "AI Disabled" badge in conversation list
3. **API Client**: Added `toggleAIResponses` method

## Deployment Steps

### 1. Pull Latest Changes

```bash
cd /path/to/eve
git pull origin main
```

### 2. Run Database Migration

```bash
# Option A: Using Docker (recommended)
docker compose exec backend python /app/run_migration.py

# Option B: Direct SQL execution
docker compose exec postgres psql -U postgres -d chatting_platform -f /docker-entrypoint-initdb.d/add_ai_responses_enabled.sql
```

### 3. Restart Services

```bash
docker compose restart backend celery-worker frontend
```

### 4. Verify Deployment

1. Check admin panel - should see new "Enable/Disable AI" buttons
2. Test AI toggle functionality
3. Verify admin messages don't appear in AI context
4. Check conversation list shows "AI Disabled" badges

## New Features

### Admin Panel

- **AI Toggle Button**: Next to block user button in conversation details
- **Visual Indicators**: "AI Disabled" badge in conversation list
- **Separate Control**: AI responses can be disabled without blocking the user

### API Endpoints

- `POST /admin/toggle-ai-responses`: Toggle AI responses for a user
  ```json
  {
    "user_id": "EVE001",
    "ai_responses_enabled": false
  }
  ```

### Behavior Changes

1. **AI Context**: Admin messages are now excluded from AI conversation history
2. **User Experience**: Users with disabled AI won't receive AI responses but can still chat
3. **Admin Control**: Separate controls for blocking users vs disabling AI responses

## Rollback Plan

If issues occur, you can rollback by:

1. `git checkout <previous-commit>`
2. `docker compose restart backend celery-worker frontend`
3. Optionally remove the database column: `ALTER TABLE users DROP COLUMN ai_responses_enabled;`

## Testing Checklist

- [ ] Admin can toggle AI responses for users
- [ ] AI disabled users don't receive AI responses
- [ ] Admin messages don't appear in AI context
- [ ] Visual indicators work correctly
- [ ] Existing functionality remains intact
