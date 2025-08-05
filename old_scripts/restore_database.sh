#!/bin/bash

# EVE Chat Platform - Database Restoration Script
# This script helps restore database from SQL backup files

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🔄 EVE Chat Platform - Database Restoration"
echo "==========================================="

# Check if backup file is provided
if [ $# -eq 0 ]; then
    print_error "Usage: $0 <backup_file.sql>"
    print_error "Example: $0 /path/to/your/backup.sql"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    print_error "Backup file not found: $BACKUP_FILE"
    exit 1
fi

print_status "Backup file: $BACKUP_FILE"

# Determine which docker-compose file to use
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=""

if [ -f "docker-compose.prod.yml" ]; then
    print_status "Production environment detected"
    COMPOSE_FILE="docker-compose.prod.yml"
    if [ -f ".env.prod" ]; then
        ENV_FILE="--env-file .env.prod"
    fi
else
    print_status "Development environment detected"
fi

print_status "Using compose file: $COMPOSE_FILE"

# Check if containers are running
print_status "Checking container status..."
if ! docker compose -f $COMPOSE_FILE $ENV_FILE ps | grep -q "postgres.*Up"; then
    print_warning "PostgreSQL container is not running. Starting services..."
    docker compose -f $COMPOSE_FILE $ENV_FILE up -d postgres
    
    print_status "Waiting for PostgreSQL to be ready..."
    sleep 10
    
    # Wait for PostgreSQL to be healthy
    for i in {1..30}; do
        if docker compose -f $COMPOSE_FILE $ENV_FILE exec postgres pg_isready -U postgres > /dev/null 2>&1; then
            print_success "PostgreSQL is ready!"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "PostgreSQL failed to start after 30 attempts"
            exit 1
        fi
        echo -n "."
        sleep 2
    done
fi

# Get database credentials
DB_NAME="chatting_platform"
DB_USER="postgres"

# Create a backup of current database (if it exists)
print_status "Creating backup of current database..."
CURRENT_BACKUP="backup_before_restore_$(date +%Y%m%d_%H%M%S).sql"
docker compose -f $COMPOSE_FILE $ENV_FILE exec -T postgres pg_dump -U $DB_USER $DB_NAME > "$CURRENT_BACKUP" 2>/dev/null || true
if [ -f "$CURRENT_BACKUP" ] && [ -s "$CURRENT_BACKUP" ]; then
    print_success "Current database backed up to: $CURRENT_BACKUP"
else
    print_warning "No existing database to backup or database is empty"
    rm -f "$CURRENT_BACKUP"
fi

# Ask for confirmation
echo ""
print_warning "⚠️  This will COMPLETELY REPLACE the current database!"
print_warning "⚠️  All existing data will be lost!"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    print_status "Operation cancelled by user"
    exit 0
fi

# Stop backend services to prevent connections
print_status "Stopping backend services..."
docker compose -f $COMPOSE_FILE $ENV_FILE stop backend celery-worker 2>/dev/null || true

# Drop and recreate database
print_status "Dropping existing database..."
docker compose -f $COMPOSE_FILE $ENV_FILE exec -T postgres psql -U $DB_USER -c "DROP DATABASE IF EXISTS $DB_NAME;"

print_status "Creating new database..."
docker compose -f $COMPOSE_FILE $ENV_FILE exec -T postgres psql -U $DB_USER -c "CREATE DATABASE $DB_NAME;"

# Restore from backup
print_status "Restoring database from backup file..."
if cat "$BACKUP_FILE" | docker compose -f $COMPOSE_FILE $ENV_FILE exec -T postgres psql -U $DB_USER -d $DB_NAME; then
    print_success "Database restored successfully!"
else
    print_error "Failed to restore database!"
    
    # Try to restore from current backup if it exists
    if [ -f "$CURRENT_BACKUP" ]; then
        print_status "Attempting to restore from current backup..."
        cat "$CURRENT_BACKUP" | docker compose -f $COMPOSE_FILE $ENV_FILE exec -T postgres psql -U $DB_USER -d $DB_NAME
        print_warning "Restored from current backup. Please check your backup file and try again."
    fi
    exit 1
fi

# Verify restoration
print_status "Verifying database restoration..."
TABLE_COUNT=$(docker compose -f $COMPOSE_FILE $ENV_FILE exec -T postgres psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' \n\r')

if [ "$TABLE_COUNT" -gt 0 ]; then
    print_success "Database verification passed. Found $TABLE_COUNT tables."
    
    # Show table list
    print_status "Tables in restored database:"
    docker compose -f $COMPOSE_FILE $ENV_FILE exec -T postgres psql -U $DB_USER -d $DB_NAME -c "\dt"
    
    # Show record counts
    echo ""
    print_status "Record counts:"
    docker compose -f $COMPOSE_FILE $ENV_FILE exec -T postgres psql -U $DB_USER -d $DB_NAME -c "
    SELECT 
        schemaname,
        tablename,
        n_tup_ins as records
    FROM pg_stat_user_tables 
    ORDER BY tablename;
    " 2>/dev/null || echo "Could not get record counts"
    
else
    print_error "Database verification failed. No tables found."
    exit 1
fi

# Restart backend services
print_status "Restarting backend services..."
docker compose -f $COMPOSE_FILE $ENV_FILE up -d backend celery-worker

# Wait for services to be ready
print_status "Waiting for services to restart..."
sleep 10

# Final health check
print_status "Performing final health check..."
if docker compose -f $COMPOSE_FILE $ENV_FILE ps | grep -q "backend.*Up"; then
    print_success "Backend services are running!"
else
    print_warning "Backend services may not be running properly. Check logs with:"
    echo "docker compose -f $COMPOSE_FILE $ENV_FILE logs backend"
fi

echo ""
print_success "🎉 Database restoration completed successfully!"
echo ""
print_status "📋 Summary:"
echo "   ✅ Database restored from: $BACKUP_FILE"
echo "   ✅ Found $TABLE_COUNT tables in database"
if [ -f "$CURRENT_BACKUP" ]; then
    echo "   ✅ Previous database backed up to: $CURRENT_BACKUP"
fi
echo ""
print_status "📝 Useful commands:"
echo "   View logs: docker compose -f $COMPOSE_FILE $ENV_FILE logs"
echo "   Access database: docker compose -f $COMPOSE_FILE $ENV_FILE exec postgres psql -U postgres -d chatting_platform"
echo "   Check tables: docker compose -f $COMPOSE_FILE $ENV_FILE exec postgres psql -U postgres -d chatting_platform -c '\dt'"
echo ""
print_success "Your database has been restored! 🚀"