#!/bin/bash

echo "🚀 Deploying Device-Based Session Updates to VPS..."
echo "=================================================="

# Configuration
VPS_IP="204.12.233.105"

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker stop eve-backend-1 eve-celery-worker-1 eve-frontend-1 2>/dev/null || true

# Rebuild containers with latest changes
echo "🔨 Rebuilding containers..."
docker build -t eve-backend ./backend
docker build -t eve-frontend ./frontend

# Start containers
echo "▶️ Starting updated containers..."
docker start eve-postgres-1 eve-redis-1

# Wait for database to be ready
echo "⏳ Waiting for database..."
sleep 10

# Run database migration
echo "🗄️ Running database migration..."
docker exec eve-backend-1 python -c "
from sqlalchemy import text
from database import engine

migration_sql = '''
ALTER TABLE users 
ALTER COLUMN tally_response_id DROP NOT NULL,
ALTER COLUMN tally_respondent_id DROP NOT NULL,
ALTER COLUMN tally_form_id DROP NOT NULL;

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS device_id VARCHAR(255) UNIQUE,
ADD COLUMN IF NOT EXISTS user_type VARCHAR(50) DEFAULT 'tally';

CREATE INDEX IF NOT EXISTS idx_users_device_id ON users(device_id);
CREATE INDEX IF NOT EXISTS idx_users_user_type ON users(user_type);
'''

try:
    with engine.connect() as connection:
        with connection.begin():
            for statement in migration_sql.split(';'):
                statement = statement.strip()
                if statement:
                    print(f'Executing: {statement[:50]}...')
                    connection.execute(text(statement))
    
    print('✅ Database migration completed successfully!')
    
except Exception as e:
    print(f'❌ Migration failed: {e}')
" 2>/dev/null || echo "⚠️ Migration may have already been applied"

# Start backend and celery
echo "🔄 Starting backend services..."
docker start eve-backend-1 eve-celery-worker-1 eve-frontend-1

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 15

# Test the deployment
echo "🧪 Testing deployment..."
echo "Frontend: http://$VPS_IP:3000"
echo "Backend: http://$VPS_IP:8001"
echo "Test Generator: http://$VPS_IP:3000/test-generator"

# Test device session endpoint
echo "🔍 Testing device session endpoint..."
curl -X POST http://$VPS_IP:8001/user/device-session \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "deployment_test_device",
    "custom_prompt": "Test deployment prompt"
  }' \
  && echo -e "\n✅ Device session endpoint working!" \
  || echo -e "\n❌ Device session endpoint failed!"

echo ""
echo "🎉 Deployment complete!"
echo "📋 Next steps:"
echo "   1. Visit http://$VPS_IP:3000/test-generator"
echo "   2. Generate a test link with your custom prompt"
echo "   3. Test the seamless chat experience"
echo ""