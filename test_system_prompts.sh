#!/bin/bash

echo "🧪 Testing System Prompts API endpoints..."

# Replace with your actual admin token
ADMIN_TOKEN="your_admin_token_here"
API_URL="http://localhost:8000"

echo "📋 1. Getting all system prompts:"
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" "$API_URL/admin/system-prompts" | jq '.'

echo ""
echo "🔍 2. Getting active system prompt:"
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" "$API_URL/admin/system-prompts/active" | jq '.'

echo ""
echo "✅ Test completed! Check if:"
echo "   - System prompts are returned (not empty array)"
echo "   - Active prompt is shown"
echo "   - All fields (head_prompt, rule_prompt) are populated"