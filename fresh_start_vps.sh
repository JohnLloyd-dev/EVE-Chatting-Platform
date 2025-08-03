#!/bin/bash

# Fresh Start VPS Setup Script
echo "🚀 Starting fresh VPS setup..."

# Check if final123.sql exists
if [ ! -f "final123.sql" ]; then
    echo "❌ final123.sql not found!"
    echo "📝 Please copy final123.sql to this directory first:"
    echo "   scp final123.sql administrator@your-vps-ip:~/EVE-Chatting-Platform/"
    exit 1
fi

echo "✅ Found final123.sql file"
ls -lh final123.sql

# Update docker-compose to use PostgreSQL 15 from the start
echo "🔧 Updating docker-compose to use PostgreSQL 15..."
sed -i 's/postgres:17/postgres:15/g' docker-compose.prod.yml
sed -i 's/postgres:16/postgres:15/g' docker-compose.prod.yml

# Start services
echo "🚀 Starting all services with PostgreSQL 15..."
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 60

# Check if postgres is ready
echo "🔍 Checking PostgreSQL status..."
for i in {1..20}; do
    if docker compose -f docker-compose.prod.yml --env-file .env.prod exec postgres pg_isready -U postgres; then
        echo "✅ PostgreSQL is ready!"
        break
    else
        echo "⏳ Waiting for PostgreSQL... ($i/20)"
        sleep 10
    fi
done

# Copy and restore final123.sql
echo "📁 Copying final123.sql to postgres container..."
docker compose -f docker-compose.prod.yml --env-file .env.prod cp final123.sql postgres:/tmp/final123.sql

echo "📥 Restoring final123.sql..."
docker compose -f docker-compose.prod.yml --env-file .env.prod exec postgres psql -U postgres -d chatting_platform -f /tmp/final123.sql

# Check results
echo "📊 Checking restored data..."
docker compose -f docker-compose.prod.yml --env-file .env.prod exec postgres psql -U postgres -d chatting_platform -c "
SELECT 'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'chat_sessions', COUNT(*) FROM chat_sessions
UNION ALL
SELECT 'messages', COUNT(*) FROM messages
UNION ALL
SELECT 'system_prompts', COUNT(*) FROM system_prompts
UNION ALL
SELECT 'tally_submissions', COUNT(*) FROM tally_submissions
UNION ALL
SELECT 'admin_users', COUNT(*) FROM admin_users;
"

# Show running services
echo "📊 Services status:"
docker compose -f docker-compose.prod.yml --env-file .env.prod ps

echo "✅ Fresh VPS setup completed!"
echo "🌐 Your application should be available at your VPS IP address"
echo "📝 All your data has been restored from final123.sql"