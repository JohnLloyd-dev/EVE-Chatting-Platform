#!/bin/bash

echo "🔍 Debugging System Prompts Database..."

echo "📋 Checking table structure:"
docker-compose exec db psql -U postgres -d eve_db -c "\d system_prompts"

echo ""
echo "📊 Checking existing data:"
docker-compose exec db psql -U postgres -d eve_db -c "SELECT id, name, head_prompt, rule_prompt, is_active, created_at FROM system_prompts ORDER BY created_at DESC;"

echo ""
echo "🔢 Counting total records:"
docker-compose exec db psql -U postgres -d eve_db -c "SELECT COUNT(*) as total_prompts FROM system_prompts;"

echo ""
echo "🔍 Checking for any records with NULL values:"
docker-compose exec db psql -U postgres -d eve_db -c "SELECT id, name, head_prompt IS NULL as head_null, rule_prompt IS NULL as rule_null FROM system_prompts;"