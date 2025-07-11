#!/bin/bash

# Backup Script for Quest Education Platform
# Usage: ./scripts/backup.sh [environment] [backup-type]
# Example: ./scripts/backup.sh production full
# Example: ./scripts/backup.sh staging database

set -e

# Parameters
ENV=${1:-development}
BACKUP_TYPE=${2:-full}

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Backup configuration
BACKUP_DIR="/opt/quest-edu/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="quest-edu-${ENV}-${BACKUP_TYPE}-${TIMESTAMP}"

echo -e "${BLUE}💾 Starting backup process${NC}"
echo -e "${BLUE}Environment: $ENV${NC}"
echo -e "${BLUE}Backup Type: $BACKUP_TYPE${NC}"
echo -e "${BLUE}Backup Name: $BACKUP_NAME${NC}"

# Load environment configuration
if [ -f "$PROJECT_ROOT/scripts/load-env.sh" ]; then
    source "$PROJECT_ROOT/scripts/load-env.sh" "$ENV"
else
    echo -e "${RED}❌ Environment loader not found${NC}"
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
backup_database() {
    echo -e "\n${BLUE}🗄️  Backing up PostgreSQL database${NC}"
    
    local db_backup_file="$BACKUP_DIR/${BACKUP_NAME}-database.sql"
    
    # Set PGPASSWORD environment variable
    export PGPASSWORD="$POSTGRES_PASSWORD"
    
    # Create database dump
    if pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
               --verbose --clean --no-owner --no-privileges \
               --format=custom > "$db_backup_file.custom" 2>/dev/null; then
        
        # Also create a plain text version for easier inspection
        pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
                --verbose --clean --no-owner --no-privileges \
                --format=plain > "$db_backup_file" 2>/dev/null
        
        echo -e "${GREEN}✅ Database backup completed${NC}"
        echo -e "${GREEN}   Custom format: $db_backup_file.custom${NC}"
        echo -e "${GREEN}   Plain format: $db_backup_file${NC}"
        
        # Compress the backups
        gzip "$db_backup_file"
        gzip "$db_backup_file.custom"
        
        echo -e "${GREEN}✅ Database backups compressed${NC}"
    else
        echo -e "${RED}❌ Database backup failed${NC}"
        return 1
    fi
    
    # Unset password
    unset PGPASSWORD
}

# Backup Redis data
backup_redis() {
    echo -e "\n${BLUE}🔄 Backing up Redis data${NC}"
    
    local redis_backup_file="$BACKUP_DIR/${BACKUP_NAME}-redis.rdb"
    
    # Save Redis data
    if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" BGSAVE; then
        # Wait for background save to complete
        while [ "$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" LASTSAVE)" = "$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" LASTSAVE)" ]; do
            sleep 1
        done
        
        # Copy the RDB file
        if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" --rdb "$redis_backup_file"; then
            echo -e "${GREEN}✅ Redis backup completed: $redis_backup_file${NC}"
            gzip "$redis_backup_file"
            echo -e "${GREEN}✅ Redis backup compressed${NC}"
        else
            echo -e "${RED}❌ Redis backup copy failed${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Redis background save failed${NC}"
        return 1
    fi
}

# Backup uploaded files
backup_uploads() {
    echo -e "\n${BLUE}📁 Backing up uploaded files${NC}"
    
    local uploads_backup_file="$BACKUP_DIR/${BACKUP_NAME}-uploads.tar.gz"
    local uploads_dir="$PROJECT_ROOT/backend/uploads"
    
    if [ -d "$uploads_dir" ]; then
        tar -czf "$uploads_backup_file" -C "$PROJECT_ROOT/backend" uploads/
        echo -e "${GREEN}✅ Uploads backup completed: $uploads_backup_file${NC}"
    else
        echo -e "${YELLOW}⚠️  Uploads directory not found, skipping${NC}"
    fi
}

# Backup configuration files
backup_config() {
    echo -e "\n${BLUE}⚙️  Backing up configuration files${NC}"
    
    local config_backup_file="$BACKUP_DIR/${BACKUP_NAME}-config.tar.gz"
    
    # Create temporary directory for config files
    local temp_config_dir="/tmp/quest-edu-config-$TIMESTAMP"
    mkdir -p "$temp_config_dir"
    
    # Copy configuration files (excluding sensitive ones)
    cp -r "$PROJECT_ROOT/config" "$temp_config_dir/" 2>/dev/null || true
    cp "$PROJECT_ROOT/docker-compose.yml" "$temp_config_dir/" 2>/dev/null || true
    cp "$PROJECT_ROOT/docker-compose.*.yml" "$temp_config_dir/" 2>/dev/null || true
    cp "$PROJECT_ROOT/.env.example" "$temp_config_dir/" 2>/dev/null || true
    cp -r "$PROJECT_ROOT/nginx" "$temp_config_dir/" 2>/dev/null || true
    
    # Create archive
    tar -czf "$config_backup_file" -C "$temp_config_dir" .
    
    # Clean up
    rm -rf "$temp_config_dir"
    
    echo -e "${GREEN}✅ Configuration backup completed: $config_backup_file${NC}"
}

# Backup application code
backup_code() {
    echo -e "\n${BLUE}💻 Backing up application code${NC}"
    
    local code_backup_file="$BACKUP_DIR/${BACKUP_NAME}-code.tar.gz"
    
    # Create git archive if in git repository
    if [ -d "$PROJECT_ROOT/.git" ]; then
        cd "$PROJECT_ROOT"
        git archive --format=tar.gz --output="$code_backup_file" HEAD
        echo -e "${GREEN}✅ Code backup completed (git archive): $code_backup_file${NC}"
    else
        # Fallback to tar (excluding common ignore patterns)
        tar -czf "$code_backup_file" \
            --exclude=node_modules \
            --exclude=venv \
            --exclude=venv_* \
            --exclude=__pycache__ \
            --exclude=.git \
            --exclude=dist \
            --exclude=build \
            --exclude=logs \
            --exclude="*.log" \
            --exclude=".env*" \
            -C "$PROJECT_ROOT" .
        echo -e "${GREEN}✅ Code backup completed (tar): $code_backup_file${NC}"
    fi
}

# Backup logs
backup_logs() {
    echo -e "\n${BLUE}📋 Backing up logs${NC}"
    
    local logs_backup_file="$BACKUP_DIR/${BACKUP_NAME}-logs.tar.gz"
    local logs_dir="$PROJECT_ROOT/logs"
    
    if [ -d "$logs_dir" ]; then
        tar -czf "$logs_backup_file" -C "$PROJECT_ROOT" logs/
        echo -e "${GREEN}✅ Logs backup completed: $logs_backup_file${NC}"
    else
        echo -e "${YELLOW}⚠️  Logs directory not found, skipping${NC}"
    fi
}

# Backup Docker volumes
backup_docker_volumes() {
    echo -e "\n${BLUE}🐳 Backing up Docker volumes${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}⚠️  Docker not available, skipping volume backup${NC}"
        return
    fi
    
    local volumes_backup_dir="$BACKUP_DIR/${BACKUP_NAME}-volumes"
    mkdir -p "$volumes_backup_dir"
    
    # Get list of project volumes
    local project_volumes=$(docker volume ls --filter "name=quest" --format "{{.Name}}" 2>/dev/null || true)
    
    if [ -n "$project_volumes" ]; then
        for volume in $project_volumes; do
            echo -e "${BLUE}  Backing up volume: $volume${NC}"
            
            # Create a temporary container to backup the volume
            docker run --rm \
                -v "$volume:/data:ro" \
                -v "$volumes_backup_dir:/backup" \
                alpine tar -czf "/backup/${volume}.tar.gz" -C /data . 2>/dev/null || \
            echo -e "${YELLOW}    ⚠️  Failed to backup volume: $volume${NC}"
        done
        
        echo -e "${GREEN}✅ Docker volumes backup completed: $volumes_backup_dir${NC}"
    else
        echo -e "${YELLOW}⚠️  No project Docker volumes found${NC}"
    fi
}

# Upload to cloud storage (AWS S3)
upload_to_s3() {
    local backup_file="$1"
    
    if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$BACKUP_S3_BUCKET" ]; then
        echo -e "${YELLOW}⚠️  AWS credentials or S3 bucket not configured, skipping cloud upload${NC}"
        return
    fi
    
    echo -e "\n${BLUE}☁️  Uploading to S3: ${BACKUP_S3_BUCKET}${NC}"
    
    local s3_path="s3://${BACKUP_S3_BUCKET}/quest-edu/${ENV}/$(basename "$backup_file")"
    
    if aws s3 cp "$backup_file" "$s3_path" --no-progress; then
        echo -e "${GREEN}✅ Uploaded to S3: $s3_path${NC}"
    else
        echo -e "${RED}❌ Failed to upload to S3${NC}"
        return 1
    fi
}

# Clean old backups
cleanup_old_backups() {
    echo -e "\n${BLUE}🧹 Cleaning up old backups${NC}"
    
    local retention_days=${BACKUP_RETENTION_DAYS:-7}
    
    # Remove local backups older than retention period
    find "$BACKUP_DIR" -name "quest-edu-${ENV}-*" -mtime "+$retention_days" -type f -delete 2>/dev/null || true
    
    echo -e "${GREEN}✅ Cleaned up backups older than $retention_days days${NC}"
    
    # Clean up S3 backups if configured
    if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$BACKUP_S3_BUCKET" ]; then
        aws s3 ls "s3://${BACKUP_S3_BUCKET}/quest-edu/${ENV}/" | \
        while read -r line; do
            local file_date=$(echo "$line" | awk '{print $1}')
            local file_name=$(echo "$line" | awk '{print $4}')
            
            if [ -n "$file_date" ] && [ -n "$file_name" ]; then
                local file_age=$(( ($(date +%s) - $(date -d "$file_date" +%s)) / 86400 ))
                if [ $file_age -gt $retention_days ]; then
                    aws s3 rm "s3://${BACKUP_S3_BUCKET}/quest-edu/${ENV}/$file_name"
                    echo -e "${GREEN}✅ Removed old S3 backup: $file_name${NC}"
                fi
            fi
        done 2>/dev/null || true
    fi
}

# Main backup execution
case $BACKUP_TYPE in
    "full")
        echo -e "${BLUE}📦 Running full backup${NC}"
        backup_database
        backup_redis
        backup_uploads
        backup_config
        backup_code
        backup_logs
        backup_docker_volumes
        ;;
    "database")
        echo -e "${BLUE}🗄️  Running database-only backup${NC}"
        backup_database
        ;;
    "config")
        echo -e "${BLUE}⚙️  Running configuration-only backup${NC}"
        backup_config
        ;;
    "code")
        echo -e "${BLUE}💻 Running code-only backup${NC}"
        backup_code
        ;;
    "data")
        echo -e "${BLUE}📊 Running data-only backup${NC}"
        backup_database
        backup_redis
        backup_uploads
        ;;
    *)
        echo -e "${RED}❌ Invalid backup type: $BACKUP_TYPE${NC}"
        echo -e "Valid options: full, database, config, code, data"
        exit 1
        ;;
esac

# Create backup manifest
MANIFEST_FILE="$BACKUP_DIR/${BACKUP_NAME}-manifest.json"
cat > "$MANIFEST_FILE" << EOF
{
  "backup_name": "$BACKUP_NAME",
  "environment": "$ENV",
  "backup_type": "$BACKUP_TYPE",
  "timestamp": "$(date -Iseconds)",
  "files": [
$(find "$BACKUP_DIR" -name "${BACKUP_NAME}*" -type f | while read -r file; do
    echo "    {"
    echo "      \"name\": \"$(basename "$file")\","
    echo "      \"path\": \"$file\","
    echo "      \"size\": \"$(du -h "$file" | cut -f1)\","
    echo "      \"checksum\": \"$(md5sum "$file" | cut -d' ' -f1)\""
    echo "    },"
done | sed '$ s/,$//')
  ],
  "total_size": "$(du -sh "$BACKUP_DIR"/${BACKUP_NAME}* | awk '{sum+=$1} END {print sum "M"}')"
}
EOF

echo -e "\n${GREEN}✅ Backup manifest created: $MANIFEST_FILE${NC}"

# Upload to cloud storage
if [ "$ENV" = "production" ] || [ "$ENV" = "staging" ]; then
    for backup_file in "$BACKUP_DIR"/${BACKUP_NAME}*; do
        upload_to_s3 "$backup_file"
    done
fi

# Clean old backups
cleanup_old_backups

# Summary
echo -e "\n${BLUE}📊 Backup Summary${NC}"
echo -e "Backup completed successfully"
echo -e "Environment: $ENV"
echo -e "Type: $BACKUP_TYPE"
echo -e "Location: $BACKUP_DIR"
echo -e "Files created:"
ls -lah "$BACKUP_DIR"/${BACKUP_NAME}* | while read -r line; do
    echo -e "  $line"
done

echo -e "\n${GREEN}🎉 Backup process completed successfully!${NC}"

# Create symlink to latest backup
ln -sf "$MANIFEST_FILE" "$BACKUP_DIR/latest-${ENV}-${BACKUP_TYPE}-manifest.json"

exit 0