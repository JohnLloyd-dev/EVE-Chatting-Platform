#!/bin/bash

# Create SQL Backup Script (run this locally)
echo "🔄 Creating SQL format backup for VPS..."

# Check if containers are running
if ! docker compose ps | grep -q "Up"; then
    echo "🚀 Starting containers first..."
    docker compose up -d
    sleep 30
fi

# Create SQL dump (plain text format)
echo "📦 Creating SQL dump..."
docker compose exec postgres pg_dump -U postgres -d chatting_platform \
    --no-owner \
    --no-privileges \
    --data-only \
    --inserts \
    --column-inserts > backup_for_vps_sql.sql

# Check if backup was created successfully
if [ -f "backup_for_vps_sql.sql" ] && [ -s "backup_for_vps_sql.sql" ]; then
    echo "✅ SQL backup created successfully: backup_for_vps_sql.sql"
    echo "📊 Backup size: $(du -h backup_for_vps_sql.sql | cut -f1)"
    echo "📝 First few lines:"
    head -10 backup_for_vps_sql.sql
    echo ""
    echo "🚀 Now copy this file to your VPS and use it instead of backup_for_vps.sql"
else
    echo "❌ Failed to create SQL backup"
    exit 1
fi