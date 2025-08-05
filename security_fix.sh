#!/bin/bash

# Security Fix Script
# Generates secure passwords and updates configurations

echo "🔒 Security Fix Script"
echo "====================="

# Use provided database credentials
echo "Step 1: Using provided database credentials..."

# Database credentials (provided by user)
DB_USERNAME="adam@2025@man"
DB_PASSWORD="eve@postgres@3241"
echo "Database Username: $DB_USERNAME"
echo "Database Password: $DB_PASSWORD"

# Generate secure passwords for other services
echo "Step 2: Generating secure passwords for other services..."

# Generate a secure admin password
ADMIN_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
echo "Generated Admin Password: $ADMIN_PASSWORD"

# Generate a secure AI model password
AI_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
echo "Generated AI Model Password: $AI_PASSWORD"

# Generate a secure JWT secret
JWT_SECRET=$(openssl rand -base64 64 | tr -d "=+/")
echo "Generated JWT Secret: $JWT_SECRET"

# Generate a secure Tally webhook secret
TALLY_SECRET=$(openssl rand -base64 32 | tr -d "=+/")
echo "Generated Tally Webhook Secret: $TALLY_SECRET"

# Create .env file with secure credentials
echo "Step 3: Creating secure .env file..."
cat > .env << EOF
# Database Configuration
POSTGRES_USER=$DB_USERNAME
POSTGRES_PASSWORD=$DB_PASSWORD
DATABASE_URL=postgresql://$DB_USERNAME:$DB_PASSWORD@postgres:5432/chatting_platform

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# AI Model Configuration
AI_MODEL_URL=http://204.12.223.76:8000
AI_MODEL_AUTH_USERNAME=adam
AI_MODEL_AUTH_PASSWORD=$AI_PASSWORD

# JWT Configuration
SECRET_KEY=$JWT_SECRET
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Admin Configuration
ADMIN_USERNAME=admin
ADMIN_PASSWORD=$ADMIN_PASSWORD

# Tally Webhook Security
TALLY_WEBHOOK_SECRET=$TALLY_SECRET

# Security Settings
ENVIRONMENT=production
DEBUG=false
NEXT_PUBLIC_API_URL=http://localhost:8001
EOF

echo "✅ Created secure .env file"

# Set proper permissions
echo "Step 4: Setting secure file permissions..."
chmod 600 .env
echo "✅ Set .env file permissions to 600 (owner read/write only)"

# Create secure docker-compose override
echo "Step 5: Creating secure docker-compose configuration..."
cp secure_docker_compose.yml docker-compose.secure.yml
echo "✅ Created secure docker-compose configuration"

# Update backend config to use environment variables
echo "Step 6: Updating backend configuration..."
cat > backend/config_secure.py << EOF
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://adam@2025@man:password@localhost:5432/chatting_platform")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # AI Model
    ai_model_url: str = os.getenv("AI_MODEL_URL", "http://204.12.223.76:8000")
    ai_model_auth_username: str = os.getenv("AI_MODEL_AUTH_USERNAME", "adam")
    ai_model_auth_password: str = os.getenv("AI_MODEL_AUTH_PASSWORD", "password")
    
    # JWT
    secret_key: str = os.getenv("SECRET_KEY", "change-this-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Admin
    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "password")
    
    # Tally webhook security
    tally_webhook_secret: Optional[str] = os.getenv("TALLY_WEBHOOK_SECRET")
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    class Config:
        env_file = ".env"

settings = Settings()
EOF

echo "✅ Created secure backend configuration"

# Create security checklist
echo "Step 7: Creating security checklist..."
cat > SECURITY_CHECKLIST.md << EOF
# Security Checklist

## ✅ Completed Security Measures

### 1. Password Security
- [x] Using provided database username: \`$DB_USERNAME\`
- [x] Using provided database password: \`$DB_PASSWORD\`
- [x] Generated secure admin password: \`$ADMIN_PASSWORD\`
- [x] Generated secure AI model password: \`$AI_PASSWORD\`
- [x] Generated secure JWT secret: \`$JWT_SECRET\`
- [x] Generated secure Tally webhook secret: \`$TALLY_SECRET\`

### 2. Configuration Security
- [x] Created secure .env file with proper permissions (600)
- [x] Updated docker-compose to use environment variables
- [x] Restricted database and Redis to localhost only
- [x] Created internal Docker network
- [x] Updated backend config to use environment variables

### 3. Network Security
- [x] Database port 5432 restricted to localhost
- [x] Redis port 6379 restricted to localhost
- [x] Internal Docker network created
- [x] No external access to internal services

## 🔒 Security Credentials

**IMPORTANT: Save these credentials securely!**

- **Database Username**: \`$DB_USERNAME\`
- **Database Password**: \`$DB_PASSWORD\`
- **Admin Password**: \`$ADMIN_PASSWORD\`
- **AI Model Password**: \`$AI_PASSWORD\`
- **JWT Secret**: \`$JWT_SECRET\`
- **Tally Webhook Secret**: \`$TALLY_SECRET\`

## 🚨 Next Steps

1. **Update your VPS** with the new secure configuration
2. **Change all passwords** in your production environment
3. **Monitor logs** for any suspicious activity
4. **Enable firewall** rules to restrict access
5. **Regular security audits** of your system

## 📋 Deployment Commands

\`\`\`bash
# Use secure configuration
cp docker-compose.secure.yml docker-compose.yml
cp backend/config_secure.py backend/config.py

# Start with secure environment
docker-compose --env-file .env up -d
\`\`\`

## 🔍 Monitoring Commands

\`\`\`bash
# Check for suspicious connections
netstat -tulpn | grep :5432
netstat -tulpn | grep :6379

# Monitor logs
docker-compose logs -f

# Check file permissions
ls -la .env
\`\`\`
EOF

echo "✅ Created security checklist"

# Create firewall rules
echo "Step 8: Creating firewall configuration..."
cat > firewall_rules.sh << 'EOF'
#!/bin/bash

# Firewall Security Rules
echo "🔒 Configuring firewall rules..."

# Allow SSH (port 22)
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS (ports 80, 443)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow application ports
sudo ufw allow 3000/tcp  # Frontend
sudo ufw allow 8001/tcp  # Backend

# Deny direct access to database and Redis
sudo ufw deny 5432/tcp   # PostgreSQL
sudo ufw deny 6379/tcp   # Redis

# Enable firewall
sudo ufw --force enable

echo "✅ Firewall configured securely"
EOF

chmod +x firewall_rules.sh
echo "✅ Created firewall configuration script"

echo ""
echo "🎉 Security Fix Complete!"
echo ""
echo "📋 Summary:"
echo "   ✅ Updated with provided database credentials"
echo "   ✅ Generated secure passwords for other services"
echo "   ✅ Created secure .env file"
echo "   ✅ Updated docker-compose configuration"
echo "   ✅ Created secure backend config"
echo "   ✅ Created security checklist"
echo "   ✅ Created firewall rules"
echo ""
echo "🔐 IMPORTANT CREDENTIALS:"
echo "   Database Username: $DB_USERNAME"
echo "   Database Password: $DB_PASSWORD"
echo "   Admin Password: $ADMIN_PASSWORD"
echo "   AI Model Password: $AI_PASSWORD"
echo ""
echo "📝 Next Steps:"
echo "   1. Save these credentials securely"
echo "   2. Update your VPS with new configuration"
echo "   3. Run: ./firewall_rules.sh"
echo "   4. Monitor for suspicious activity"
echo ""
echo "🚨 SECURITY ALERT:"
echo "   - Change all passwords immediately"
echo "   - Monitor system logs"
echo "   - Enable firewall rules"
echo "   - Consider reinstalling system if compromised" 