#!/bin/bash

# Database restore script for production
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
RESTORE_DIR="/tmp/restore"
S3_BUCKET="educational-rpg-backups"

echo -e "${BLUE}🔄 Database Restore Tool${NC}"
echo -e "${BLUE}========================${NC}\n"

# Function to list available backups
list_backups() {
    echo -e "${YELLOW}Available backups:${NC}"
    aws s3 ls "s3://$S3_BUCKET/postgresql/" --recursive | \
        grep -E "\.tar\.gz$" | \
        sort -r | \
        awk '{print NR ". " $4 " (" $3 " bytes)"}'
}

# Function to get backup name by number
get_backup_name() {
    local num=$1
    aws s3 ls "s3://$S3_BUCKET/postgresql/" --recursive | \
        grep -E "\.tar\.gz$" | \
        sort -r | \
        awk -v n="$num" 'NR==n {print $4}'
}

# Check if backup file is provided as argument
if [ $# -eq 0 ]; then
    # Interactive mode
    list_backups
    echo
    read -p "Select backup number to restore (or 'q' to quit): " selection
    
    if [ "$selection" = "q" ]; then
        echo "Restore cancelled."
        exit 0
    fi
    
    BACKUP_FILE=$(get_backup_name $selection)
else
    # Direct mode with backup file argument
    BACKUP_FILE=$1
fi

if [ -z "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Invalid backup selection${NC}"
    exit 1
fi

echo -e "\n${RED}⚠️  WARNING: This will restore the database from backup!${NC}"
echo -e "Backup file: ${YELLOW}$BACKUP_FILE${NC}"
read -p "Are you sure you want to continue? (yes/no): " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Restore cancelled."
    exit 0
fi

# Create restore directory
mkdir -p $RESTORE_DIR

# Get database credentials
echo -e "${YELLOW}Fetching database credentials...${NC}"
DB_HOST=$(aws ssm get-parameter --name "/educational-rpg/production/db-host" --query 'Parameter.Value' --output text)
DB_NAME=$(aws ssm get-parameter --name "/educational-rpg/production/db-name" --query 'Parameter.Value' --output text)
DB_USER=$(aws ssm get-parameter --name "/educational-rpg/production/db-user" --query 'Parameter.Value' --output text)
DB_PASSWORD=$(aws ssm get-parameter --name "/educational-rpg/production/db-password" --with-decryption --query 'Parameter.Value' --output text)

# Download backup from S3
echo -e "${YELLOW}Downloading backup from S3...${NC}"
aws s3 cp "s3://$S3_BUCKET/$BACKUP_FILE" "$RESTORE_DIR/backup.tar.gz"

# Extract backup
echo -e "${YELLOW}Extracting backup...${NC}"
tar -xzf "$RESTORE_DIR/backup.tar.gz" -C "$RESTORE_DIR"

# Find the dump file
DUMP_FILE=$(find $RESTORE_DIR -name "*.dump" -type f | head -1)
if [ -z "$DUMP_FILE" ]; then
    echo -e "${RED}Error: No dump file found in backup${NC}"
    exit 1
fi

# Show metadata if available
METADATA_FILE=$(find $RESTORE_DIR -name "*.metadata.json" -type f | head -1)
if [ -f "$METADATA_FILE" ]; then
    echo -e "${YELLOW}Backup metadata:${NC}"
    cat "$METADATA_FILE" | jq '.' || cat "$METADATA_FILE"
    echo
fi

# Create backup of current database before restore
echo -e "${YELLOW}Creating backup of current database...${NC}"
export PGPASSWORD=$DB_PASSWORD
CURRENT_BACKUP="/tmp/pre_restore_backup_$(date +%Y%m%d_%H%M%S).dump"
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
    --format=custom \
    --compress=9 \
    > "$CURRENT_BACKUP" || {
        echo -e "${RED}Error: Failed to backup current database${NC}"
        exit 1
    }
echo -e "${GREEN}Current database backed up to: $CURRENT_BACKUP${NC}"

# Terminate existing connections
echo -e "${YELLOW}Terminating existing database connections...${NC}"
psql -h $DB_HOST -U $DB_USER -d postgres <<EOF
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '$DB_NAME'
  AND pid <> pg_backend_pid();
EOF

# Drop and recreate database
echo -e "${YELLOW}Recreating database...${NC}"
psql -h $DB_HOST -U $DB_USER -d postgres <<EOF
DROP DATABASE IF EXISTS $DB_NAME;
CREATE DATABASE $DB_NAME;
EOF

# Restore from backup
echo -e "${YELLOW}Restoring database from backup...${NC}"
pg_restore -h $DB_HOST -U $DB_USER -d $DB_NAME \
    --verbose \
    --no-owner \
    --no-privileges \
    --if-exists \
    --clean \
    "$DUMP_FILE" || {
        echo -e "${RED}Error: Restore failed${NC}"
        echo -e "${YELLOW}You can restore the previous state from: $CURRENT_BACKUP${NC}"
        exit 1
    }

# Run post-restore tasks
echo -e "${YELLOW}Running post-restore tasks...${NC}"

# Update sequences
psql -h $DB_HOST -U $DB_USER -d $DB_NAME <<EOF
-- Reset all sequences to max values
DO \$\$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (
        SELECT 
            c.relname AS sequence_name,
            n.nspname AS schema_name
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relkind = 'S'
        AND n.nspname NOT IN ('pg_catalog', 'information_schema')
    )
    LOOP
        EXECUTE format('SELECT setval(''%I.%I'', COALESCE((SELECT MAX(id) FROM %I.%I), 1))',
            r.schema_name, r.sequence_name,
            r.schema_name, replace(r.sequence_name, '_id_seq', ''));
    END LOOP;
END \$\$;

-- Analyze all tables
ANALYZE;
EOF

# Clean up
echo -e "${YELLOW}Cleaning up...${NC}"
rm -rf $RESTORE_DIR
unset PGPASSWORD

# Send notification
SLACK_WEBHOOK=$(aws ssm get-parameter --name "/educational-rpg/production/slack-webhook" --with-decryption --query 'Parameter.Value' --output text 2>/dev/null || echo "")
if [ ! -z "$SLACK_WEBHOOK" ]; then
    curl -X POST $SLACK_WEBHOOK \
        -H 'Content-type: application/json' \
        -d "{
            \"text\": \"🔄 Database restore completed\",
            \"attachments\": [{
                \"color\": \"warning\",
                \"fields\": [
                    {\"title\": \"Restored From\", \"value\": \"$BACKUP_FILE\", \"short\": false},
                    {\"title\": \"Database\", \"value\": \"$DB_NAME\", \"short\": true},
                    {\"title\": \"Host\", \"value\": \"$DB_HOST\", \"short\": true},
                    {\"title\": \"Pre-restore Backup\", \"value\": \"$CURRENT_BACKUP\", \"short\": false}
                ]
            }]
        }" 2>/dev/null
fi

echo -e "${GREEN}✅ Database restore completed successfully!${NC}"
echo -e "${YELLOW}Pre-restore backup saved at: $CURRENT_BACKUP${NC}"