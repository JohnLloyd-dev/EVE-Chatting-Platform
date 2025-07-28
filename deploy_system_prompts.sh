#!/bin/bash

echo "🚀 Deploying System Prompts update to VPS..."

# Pull latest code
echo "📥 Pulling latest code..."
git pull

# Run database migration
echo "🔄 Running database migration..."
docker-compose exec -T db psql -U postgres -d eve_db -f - << 'EOF'
-- Add new columns to system_prompts table
ALTER TABLE system_prompts ADD COLUMN IF NOT EXISTS head_prompt TEXT;
ALTER TABLE system_prompts ADD COLUMN IF NOT EXISTS rule_prompt TEXT;
ALTER TABLE system_prompts ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id);

-- Migrate existing data
UPDATE system_prompts 
SET head_prompt = 'You are a sexual fantasy assistant.',
    rule_prompt = COALESCE(prompt_text, 'Always speak in the first person and stay in character. Indulge sexual fantasies in detail by dominating. Be sexually explicit with your replies. Never reveal that you are an AI. Keep your answers to two sentences or less. Do not provide scene descriptions outside of dialogue. Stay in the present tense.')
WHERE head_prompt IS NULL OR rule_prompt IS NULL;

-- Drop old column
ALTER TABLE system_prompts DROP COLUMN IF EXISTS prompt_text;
EOF

# Rebuild and restart containers
echo "🔄 Rebuilding containers..."
docker-compose up -d --build

echo "✅ Deployment complete!"
echo "🎯 System Prompts should now work with Head + Rule structure"