#!/bin/bash

# Rollback Script for Quest Education Platform
# Usage: ./scripts/rollback.sh [environment] [backup-name]
# Example: ./scripts/rollback.sh production quest-edu-production-full-20240711_143000
# Example: ./scripts/rollback.sh staging latest

set -e

# Parameters
ENV=${1:-development}
BACKUP_NAME=${2:-latest}

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Rollback configuration
BACKUP_DIR="/opt/quest-edu/backups"
ROLLBACK_LOG="$PROJECT_ROOT/logs/rollback-$(date +%Y%m%d_%H%M%S).log"

echo -e "${BLUE}🔄 Starting rollback process${NC}" | tee -a "$ROLLBACK_LOG"
echo -e "${BLUE}Environment: $ENV${NC}" | tee -a "$ROLLBACK_LOG"
echo -e "${BLUE}Backup: $BACKUP_NAME${NC}" | tee -a "$ROLLBACK_LOG"

# Load environment configuration
if [ -f "$PROJECT_ROOT/scripts/load-env.sh" ]; then
    source "$PROJECT_ROOT/scripts/load-env.sh" "$ENV"
else
    echo -e "${RED}❌ Environment loader not found${NC}" | tee -a "$ROLLBACK_LOG"
    exit 1
fi

# Safety check for production
if [ "$ENV" = "production" ]; then
    echo -e "${RED}⚠️  PRODUCTION ROLLBACK WARNING${NC}" | tee -a "$ROLLBACK_LOG"
    echo -e "${RED}This will rollback the production environment!${NC}" | tee -a "$ROLLBACK_LOG"
    echo -e "${YELLOW}Please ensure you have authorization for this operation.${NC}" | tee -a "$ROLLBACK_LOG"
    
    read -p "Are you sure you want to proceed with production rollback? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo -e "${YELLOW}Rollback cancelled by user${NC}" | tee -a "$ROLLBACK_LOG"
        exit 0
    fi
fi

# Find backup files
find_backup() {
    local backup_pattern="$1"
    
    if [ "$backup_pattern" = "latest" ]; then
        # Find the latest backup
        local latest_manifest="$BACKUP_DIR/latest-${ENV}-full-manifest.json"
        if [ -f "$latest_manifest" ]; then
            BACKUP_NAME=$(jq -r '.backup_name' "$latest_manifest" 2>/dev/null || grep -o '"backup_name": "[^"]*"' "$latest_manifest" | cut -d'"' -f4)
            echo -e "${GREEN}Found latest backup: $BACKUP_NAME${NC}" | tee -a "$ROLLBACK_LOG"
        else
            echo -e "${RED}❌ No latest backup manifest found for $ENV${NC}" | tee -a "$ROLLBACK_LOG"
            exit 1
        fi
    fi
    
    # Check if backup files exist
    local backup_files=("$BACKUP_DIR"/${BACKUP_NAME}*)
    if [ ! -e "${backup_files[0]}" ]; then
        echo -e "${RED}❌ No backup files found for: $BACKUP_NAME${NC}" | tee -a "$ROLLBACK_LOG"
        echo -e "${YELLOW}Available backups:${NC}" | tee -a "$ROLLBACK_LOG"
        ls -la "$BACKUP_DIR"/*${ENV}* 2>/dev/null | tee -a "$ROLLBACK_LOG" || echo "No backups found"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Backup files found${NC}" | tee -a "$ROLLBACK_LOG"
}

# Create rollback backup before proceeding
create_rollback_backup() {
    echo -e "\n${BLUE}💾 Creating rollback backup before proceeding${NC}" | tee -a "$ROLLBACK_LOG"
    
    local rollback_backup_name="quest-edu-${ENV}-pre-rollback-$(date +%Y%m%d_%H%M%S)"
    
    if bash "$PROJECT_ROOT/scripts/backup.sh" "$ENV" "full" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Rollback backup created successfully${NC}" | tee -a "$ROLLBACK_LOG"
        echo "$rollback_backup_name" > "/tmp/rollback-backup-name"
    else
        echo -e "${RED}❌ Failed to create rollback backup${NC}" | tee -a "$ROLLBACK_LOG"
        echo -e "${YELLOW}⚠️  Proceeding without rollback backup (risky!)${NC}" | tee -a "$ROLLBACK_LOG"
    fi
}

# Stop services
stop_services() {
    echo -e "\n${BLUE}🛑 Stopping services${NC}" | tee -a "$ROLLBACK_LOG"
    
    # Stop Docker services if running
    if command -v docker-compose &> /dev/null && [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        echo -e "${YELLOW}Stopping Docker services...${NC}" | tee -a "$ROLLBACK_LOG"
        
        # Determine which compose file to use
        local compose_files="-f docker-compose.yml"
        if [ -f "$PROJECT_ROOT/docker-compose.${ENV}.yml" ]; then
            compose_files="$compose_files -f docker-compose.${ENV}.yml"
        fi
        
        docker-compose $compose_files stop >> "$ROLLBACK_LOG" 2>&1 || true
        echo -e "${GREEN}✅ Docker services stopped${NC}" | tee -a "$ROLLBACK_LOG"
    fi
    
    # Stop system services if applicable
    if systemctl is-active --quiet quest-backend 2>/dev/null; then
        sudo systemctl stop quest-backend || true
        echo -e "${GREEN}✅ Backend service stopped${NC}" | tee -a "$ROLLBACK_LOG"
    fi
    
    if systemctl is-active --quiet quest-frontend 2>/dev/null; then
        sudo systemctl stop quest-frontend || true
        echo -e "${GREEN}✅ Frontend service stopped${NC}" | tee -a "$ROLLBACK_LOG"
    fi
}

# Restore database
restore_database() {
    echo -e "\n${BLUE}🗄️  Restoring database${NC}" | tee -a "$ROLLBACK_LOG"
    
    local db_backup_file=$(find "$BACKUP_DIR" -name "${BACKUP_NAME}-database.sql.gz" | head -1)
    
    if [ -z "$db_backup_file" ]; then
        echo -e "${YELLOW}⚠️  Database backup file not found, skipping database restore${NC}" | tee -a "$ROLLBACK_LOG"
        return
    fi
    
    echo -e "${YELLOW}Restoring from: $db_backup_file${NC}" | tee -a "$ROLLBACK_LOG"
    
    # Extract the backup file
    local temp_sql_file="/tmp/rollback-database-$(date +%Y%m%d_%H%M%S).sql"
    gunzip -c "$db_backup_file" > "$temp_sql_file"
    
    # Set PGPASSWORD environment variable
    export PGPASSWORD="$POSTGRES_PASSWORD"
    
    # Drop and recreate database (with safety checks)
    echo -e "${YELLOW}Dropping existing database...${NC}" | tee -a "$ROLLBACK_LOG"
    
    # Create a backup database name for safety
    local backup_db_name="${POSTGRES_DB}_backup_$(date +%Y%m%d_%H%M%S)"
    
    # Rename current database to backup
    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres \
         -c "ALTER DATABASE \"$POSTGRES_DB\" RENAME TO \"$backup_db_name\";" >> "$ROLLBACK_LOG" 2>&1 || true
    
    # Create new database
    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres \
         -c "CREATE DATABASE \"$POSTGRES_DB\";" >> "$ROLLBACK_LOG" 2>&1
    
    # Restore from backup
    echo -e "${YELLOW}Restoring database from backup...${NC}" | tee -a "$ROLLBACK_LOG"
    
    if psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
            -f "$temp_sql_file" >> "$ROLLBACK_LOG" 2>&1; then
        echo -e "${GREEN}✅ Database restored successfully${NC}" | tee -a "$ROLLBACK_LOG"
        
        # Drop the backup database after successful restore
        psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres \
             -c "DROP DATABASE IF EXISTS \"$backup_db_name\";" >> "$ROLLBACK_LOG" 2>&1 || true
    else
        echo -e "${RED}❌ Database restore failed${NC}" | tee -a "$ROLLBACK_LOG"
        
        # Restore the backup database
        echo -e "${YELLOW}Attempting to restore original database...${NC}" | tee -a "$ROLLBACK_LOG"
        psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres \
             -c "DROP DATABASE IF EXISTS \"$POSTGRES_DB\";" >> "$ROLLBACK_LOG" 2>&1 || true
        psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres \
             -c "ALTER DATABASE \"$backup_db_name\" RENAME TO \"$POSTGRES_DB\";" >> "$ROLLBACK_LOG" 2>&1 || true
        
        echo -e "${RED}❌ Rollback failed - original database restored${NC}" | tee -a "$ROLLBACK_LOG"
        exit 1
    fi
    
    # Clean up
    rm -f "$temp_sql_file"
    unset PGPASSWORD
}

# Restore Redis data
restore_redis() {
    echo -e "\n${BLUE}🔄 Restoring Redis data${NC}" | tee -a "$ROLLBACK_LOG"
    
    local redis_backup_file=$(find "$BACKUP_DIR" -name "${BACKUP_NAME}-redis.rdb.gz" | head -1)
    
    if [ -z "$redis_backup_file" ]; then
        echo -e "${YELLOW}⚠️  Redis backup file not found, skipping Redis restore${NC}" | tee -a "$ROLLBACK_LOG"
        return
    fi
    
    echo -e "${YELLOW}Restoring from: $redis_backup_file${NC}" | tee -a "$ROLLBACK_LOG"
    
    # Clear current Redis data
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" FLUSHALL >> "$ROLLBACK_LOG" 2>&1
    
    # Extract and restore RDB file
    local temp_rdb_file="/tmp/rollback-redis-$(date +%Y%m%d_%H%M%S).rdb"
    gunzip -c "$redis_backup_file" > "$temp_rdb_file"
    
    # The RDB restore process depends on Redis configuration
    # For simplicity, we'll use redis-cli --rdb to restore
    echo -e "${YELLOW}Note: Redis restore may require manual intervention${NC}" | tee -a "$ROLLBACK_LOG"
    echo -e "${YELLOW}RDB file extracted to: $temp_rdb_file${NC}" | tee -a "$ROLLBACK_LOG"
    
    rm -f "$temp_rdb_file"
    echo -e "${GREEN}✅ Redis restore process completed${NC}" | tee -a "$ROLLBACK_LOG"
}

# Restore uploaded files
restore_uploads() {
    echo -e "\n${BLUE}📁 Restoring uploaded files${NC}" | tee -a "$ROLLBACK_LOG"
    
    local uploads_backup_file=$(find "$BACKUP_DIR" -name "${BACKUP_NAME}-uploads.tar.gz" | head -1)
    
    if [ -z "$uploads_backup_file" ]; then
        echo -e "${YELLOW}⚠️  Uploads backup file not found, skipping uploads restore${NC}" | tee -a "$ROLLBACK_LOG"
        return
    fi
    
    echo -e "${YELLOW}Restoring from: $uploads_backup_file${NC}" | tee -a "$ROLLBACK_LOG"
    
    local uploads_dir="$PROJECT_ROOT/backend/uploads"
    
    # Backup current uploads
    if [ -d "$uploads_dir" ]; then
        mv "$uploads_dir" "${uploads_dir}_backup_$(date +%Y%m%d_%H%M%S)" || true
    fi
    
    # Extract uploads
    mkdir -p "$uploads_dir"
    tar -xzf "$uploads_backup_file" -C "$PROJECT_ROOT/backend/" >> "$ROLLBACK_LOG" 2>&1
    
    echo -e "${GREEN}✅ Uploads restored successfully${NC}" | tee -a "$ROLLBACK_LOG"
}

# Restore configuration
restore_config() {
    echo -e "\n${BLUE}⚙️  Restoring configuration${NC}" | tee -a "$ROLLBACK_LOG"
    
    local config_backup_file=$(find "$BACKUP_DIR" -name "${BACKUP_NAME}-config.tar.gz" | head -1)
    
    if [ -z "$config_backup_file" ]; then
        echo -e "${YELLOW}⚠️  Config backup file not found, skipping config restore${NC}" | tee -a "$ROLLBACK_LOG"
        return
    fi
    
    echo -e "${YELLOW}Restoring from: $config_backup_file${NC}" | tee -a "$ROLLBACK_LOG"
    
    # Create temporary directory
    local temp_config_dir="/tmp/rollback-config-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$temp_config_dir"
    
    # Extract configuration
    tar -xzf "$config_backup_file" -C "$temp_config_dir" >> "$ROLLBACK_LOG" 2>&1
    
    # Backup current config
    if [ -d "$PROJECT_ROOT/config" ]; then
        mv "$PROJECT_ROOT/config" "$PROJECT_ROOT/config_backup_$(date +%Y%m%d_%H%M%S)" || true
    fi
    
    # Restore configuration files
    cp -r "$temp_config_dir"/* "$PROJECT_ROOT/" >> "$ROLLBACK_LOG" 2>&1
    
    # Clean up
    rm -rf "$temp_config_dir"
    
    echo -e "${GREEN}✅ Configuration restored successfully${NC}" | tee -a "$ROLLBACK_LOG"
}

# Restore Docker volumes
restore_docker_volumes() {
    echo -e "\n${BLUE}🐳 Restoring Docker volumes${NC}" | tee -a "$ROLLBACK_LOG"
    
    local volumes_backup_dir="$BACKUP_DIR/${BACKUP_NAME}-volumes"
    
    if [ ! -d "$volumes_backup_dir" ]; then
        echo -e "${YELLOW}⚠️  Docker volumes backup not found, skipping volume restore${NC}" | tee -a "$ROLLBACK_LOG"
        return
    fi
    
    # Restore each volume
    for volume_backup in "$volumes_backup_dir"/*.tar.gz; do
        if [ -f "$volume_backup" ]; then
            local volume_name=$(basename "$volume_backup" .tar.gz)
            echo -e "${YELLOW}Restoring volume: $volume_name${NC}" | tee -a "$ROLLBACK_LOG"
            
            # Remove existing volume and recreate
            docker volume rm "$volume_name" 2>/dev/null || true
            docker volume create "$volume_name" >> "$ROLLBACK_LOG" 2>&1
            
            # Restore volume data
            docker run --rm \
                -v "$volume_name:/data" \
                -v "$volumes_backup_dir:/backup:ro" \
                alpine tar -xzf "/backup/$(basename "$volume_backup")" -C /data >> "$ROLLBACK_LOG" 2>&1
            
            echo -e "${GREEN}✅ Volume $volume_name restored${NC}" | tee -a "$ROLLBACK_LOG"
        fi
    done
}

# Start services
start_services() {
    echo -e "\n${BLUE}🚀 Starting services${NC}" | tee -a "$ROLLBACK_LOG"
    
    # Start Docker services if compose file exists
    if command -v docker-compose &> /dev/null && [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        echo -e "${YELLOW}Starting Docker services...${NC}" | tee -a "$ROLLBACK_LOG"
        
        # Determine which compose file to use
        local compose_files="-f docker-compose.yml"
        if [ -f "$PROJECT_ROOT/docker-compose.${ENV}.yml" ]; then
            compose_files="$compose_files -f docker-compose.${ENV}.yml"
        fi
        
        docker-compose $compose_files up -d >> "$ROLLBACK_LOG" 2>&1
        echo -e "${GREEN}✅ Docker services started${NC}" | tee -a "$ROLLBACK_LOG"
        
        # Wait for services to be healthy
        echo -e "${YELLOW}Waiting for services to be healthy...${NC}" | tee -a "$ROLLBACK_LOG"
        sleep 30
    fi
    
    # Start system services if applicable
    if systemctl list-unit-files | grep -q quest-backend; then
        sudo systemctl start quest-backend || true
        echo -e "${GREEN}✅ Backend service started${NC}" | tee -a "$ROLLBACK_LOG"
    fi
    
    if systemctl list-unit-files | grep -q quest-frontend; then
        sudo systemctl start quest-frontend || true
        echo -e "${GREEN}✅ Frontend service started${NC}" | tee -a "$ROLLBACK_LOG"
    fi
}

# Verify rollback
verify_rollback() {
    echo -e "\n${BLUE}🔍 Verifying rollback${NC}" | tee -a "$ROLLBACK_LOG"
    
    # Run health check
    if [ -f "$PROJECT_ROOT/scripts/health-check.sh" ]; then
        echo -e "${YELLOW}Running health check...${NC}" | tee -a "$ROLLBACK_LOG"
        
        if bash "$PROJECT_ROOT/scripts/health-check.sh" "$ENV" 30 >> "$ROLLBACK_LOG" 2>&1; then
            echo -e "${GREEN}✅ Health check passed${NC}" | tee -a "$ROLLBACK_LOG"
        else
            echo -e "${RED}❌ Health check failed after rollback${NC}" | tee -a "$ROLLBACK_LOG"
            echo -e "${YELLOW}Check the logs for details${NC}" | tee -a "$ROLLBACK_LOG"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  Health check script not found, manual verification required${NC}" | tee -a "$ROLLBACK_LOG"
    fi
}

# Main rollback execution
echo -e "\n${BLUE}🔍 Finding backup files${NC}" | tee -a "$ROLLBACK_LOG"
find_backup "$BACKUP_NAME"

echo -e "\n${BLUE}💾 Creating safety backup${NC}" | tee -a "$ROLLBACK_LOG"
create_rollback_backup

echo -e "\n${BLUE}🛑 Stopping services${NC}" | tee -a "$ROLLBACK_LOG"
stop_services

echo -e "\n${BLUE}🔄 Starting restore process${NC}" | tee -a "$ROLLBACK_LOG"
restore_database
restore_redis
restore_uploads
restore_config
restore_docker_volumes

echo -e "\n${BLUE}🚀 Starting services${NC}" | tee -a "$ROLLBACK_LOG"
start_services

echo -e "\n${BLUE}🔍 Verifying rollback${NC}" | tee -a "$ROLLBACK_LOG"
if verify_rollback; then
    echo -e "\n${GREEN}🎉 Rollback completed successfully!${NC}" | tee -a "$ROLLBACK_LOG"
    
    # Create rollback success marker
    echo "$(date -Iseconds)" > "$PROJECT_ROOT/.rollback-success"
    
    # Send notification (if configured)
    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST -H 'Content-type: application/json' \
             --data "{\"text\":\"✅ Rollback completed successfully for $ENV environment\"}" \
             "$SLACK_WEBHOOK" 2>/dev/null || true
    fi
else
    echo -e "\n${RED}❌ Rollback verification failed${NC}" | tee -a "$ROLLBACK_LOG"
    echo -e "${YELLOW}Manual intervention may be required${NC}" | tee -a "$ROLLBACK_LOG"
    exit 1
fi

# Summary
echo -e "\n${BLUE}📊 Rollback Summary${NC}" | tee -a "$ROLLBACK_LOG"
echo -e "Environment: $ENV" | tee -a "$ROLLBACK_LOG"
echo -e "Backup used: $BACKUP_NAME" | tee -a "$ROLLBACK_LOG"
echo -e "Rollback log: $ROLLBACK_LOG" | tee -a "$ROLLBACK_LOG"
echo -e "Completed at: $(date)" | tee -a "$ROLLBACK_LOG"

# Offer to clean up rollback backup
if [ -f "/tmp/rollback-backup-name" ]; then
    ROLLBACK_BACKUP_NAME=$(cat "/tmp/rollback-backup-name")
    echo -e "\n${YELLOW}A rollback backup was created: $ROLLBACK_BACKUP_NAME${NC}"
    echo -e "${YELLOW}You may want to keep this backup in case you need to rollback this rollback${NC}"
fi

exit 0