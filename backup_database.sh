#!/bin/bash

# EVE Chat Platform - Database Backup Script
# This script creates backups of the database

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

echo "💾 EVE Chat Platform - Database Backup"
echo "======================================"

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

# Check if PostgreSQL container is running
if ! docker compose -f $COMPOSE_FILE $ENV_FILE ps | grep -q "postgres.*Up"; then
    print_error "PostgreSQL container is not running!"
    print_error "Start it with: docker compose -f $COMPOSE_FILE $ENV_FILE up -d postgres"
    exit 1
fi

# Database credentials
DB_NAME="chatting_platform"
DB_USER="postgres"

# Create backup directory if it doesn't exist
BACKUP_DIR="backups"
mkdir -p "$BACKUP_DIR"

# Generate backup filename with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/eve_database_backup_$TIMESTAMP.sql"

print_status "Creating database backup..."
print_status "Backup file: $BACKUP_FILE"

# Create the backup
if docker compose -f $COMPOSE_FILE $ENV_FILE exec -T postgres pg_dump -U $DB_USER $DB_NAME > "$BACKUP_FILE"; then
    print_success "Database backup created successfully!"
    
    # Get file size
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    print_status "Backup size: $BACKUP_SIZE"
    
    # Verify backup
    if [ -s "$BACKUP_FILE" ]; then
        print_success "Backup file verification passed"
        
        # Show some stats
        LINE_COUNT=$(wc -l < "$BACKUP_FILE")
        print_status "Backup contains $LINE_COUNT lines"
        
        # Check for key tables
        if grep -q "CREATE TABLE" "$BACKUP_FILE"; then
            TABLE_COUNT=$(grep -c "CREATE TABLE" "$BACKUP_FILE")
            print_status "Found $TABLE_COUNT tables in backup"
        fi
        
        if grep -q "INSERT INTO" "$BACKUP_FILE"; then
            INSERT_COUNT=$(grep -c "INSERT INTO" "$BACKUP_FILE")
            print_status "Found $INSERT_COUNT data insert statements"
        fi
        
    else
        print_error "Backup file is empty!"
        rm -f "$BACKUP_FILE"
        exit 1
    fi
    
else
    print_error "Failed to create database backup!"
    exit 1
fi

# Compress backup (optional)
read -p "Do you want to compress the backup? (y/n): " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Compressing backup..."
    if gzip "$BACKUP_FILE"; then
        COMPRESSED_FILE="${BACKUP_FILE}.gz"
        COMPRESSED_SIZE=$(du -h "$COMPRESSED_FILE" | cut -f1)
        print_success "Backup compressed to: $COMPRESSED_FILE"
        print_status "Compressed size: $COMPRESSED_SIZE"
        BACKUP_FILE="$COMPRESSED_FILE"
    else
        print_warning "Failed to compress backup, keeping uncompressed version"
    fi
fi

# Clean up old backups (keep last 5)
print_status "Cleaning up old backups (keeping last 5)..."
cd "$BACKUP_DIR"
ls -t eve_database_backup_*.sql* 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null || true
REMAINING_BACKUPS=$(ls -1 eve_database_backup_*.sql* 2>/dev/null | wc -l)
print_status "Remaining backups: $REMAINING_BACKUPS"
cd ..

echo ""
print_success "🎉 Database backup completed successfully!"
echo ""
print_status "📋 Backup Information:"
echo "   📁 File: $BACKUP_FILE"
echo "   📊 Size: $(du -h "$BACKUP_FILE" | cut -f1)"
echo "   📅 Created: $(date)"
echo ""
print_status "📝 To restore this backup:"
echo "   ./restore_database.sh $BACKUP_FILE"
echo ""
print_status "💡 Tip: Set up a cron job to run this script regularly:"
echo "   # Add to crontab (crontab -e):"
echo "   # Daily backup at 2 AM:"
echo "   0 2 * * * cd $(pwd) && ./backup_database.sh"
echo ""
print_success "Backup completed! 💾"