#!/bin/bash

# Database backup script for production
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
BACKUP_DIR="/backups/postgresql"
S3_BUCKET="educational-rpg-backups"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="educational_rpg_backup_${TIMESTAMP}"

echo -e "${GREEN}🔄 Starting database backup...${NC}"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Get database credentials from AWS SSM
echo -e "${YELLOW}Fetching database credentials...${NC}"
DB_HOST=$(aws ssm get-parameter --name "/educational-rpg/production/db-host" --query 'Parameter.Value' --output text)
DB_NAME=$(aws ssm get-parameter --name "/educational-rpg/production/db-name" --query 'Parameter.Value' --output text)
DB_USER=$(aws ssm get-parameter --name "/educational-rpg/production/db-user" --query 'Parameter.Value' --output text)
DB_PASSWORD=$(aws ssm get-parameter --name "/educational-rpg/production/db-password" --with-decryption --query 'Parameter.Value' --output text)

# Export password for pg_dump
export PGPASSWORD=$DB_PASSWORD

# Perform backup
echo -e "${YELLOW}Creating database backup...${NC}"
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
    --verbose \
    --no-owner \
    --no-privileges \
    --format=custom \
    --compress=9 \
    > "$BACKUP_DIR/${BACKUP_NAME}.dump"

# Unset password
unset PGPASSWORD

# Create backup metadata
echo -e "${YELLOW}Creating backup metadata...${NC}"
cat > "$BACKUP_DIR/${BACKUP_NAME}.metadata.json" <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "database": "$DB_NAME",
  "host": "$DB_HOST",
  "size": $(stat -c%s "$BACKUP_DIR/${BACKUP_NAME}.dump"),
  "format": "custom",
  "compression": "9",
  "retention_days": $RETENTION_DAYS
}
EOF

# Compress backup with metadata
echo -e "${YELLOW}Compressing backup...${NC}"
tar -czf "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" \
    -C "$BACKUP_DIR" \
    "${BACKUP_NAME}.dump" \
    "${BACKUP_NAME}.metadata.json"

# Upload to S3
echo -e "${YELLOW}Uploading to S3...${NC}"
aws s3 cp "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" \
    "s3://$S3_BUCKET/postgresql/${BACKUP_NAME}.tar.gz" \
    --storage-class STANDARD_IA \
    --metadata "timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ),retention_days=$RETENTION_DAYS"

# Clean up local files
echo -e "${YELLOW}Cleaning up local files...${NC}"
rm -f "$BACKUP_DIR/${BACKUP_NAME}.dump"
rm -f "$BACKUP_DIR/${BACKUP_NAME}.metadata.json"
rm -f "$BACKUP_DIR/${BACKUP_NAME}.tar.gz"

# Remove old backups from S3
echo -e "${YELLOW}Removing old backups from S3...${NC}"
CUTOFF_DATE=$(date -u -d "$RETENTION_DAYS days ago" +%Y-%m-%d)
aws s3api list-objects-v2 \
    --bucket $S3_BUCKET \
    --prefix "postgresql/" \
    --query "Contents[?LastModified<'$CUTOFF_DATE'].Key" \
    --output text | \
    tr '\t' '\n' | \
    while read key; do
        if [ ! -z "$key" ]; then
            echo "Deleting old backup: $key"
            aws s3 rm "s3://$S3_BUCKET/$key"
        fi
    done

# Send notification
SLACK_WEBHOOK=$(aws ssm get-parameter --name "/educational-rpg/production/slack-webhook" --with-decryption --query 'Parameter.Value' --output text 2>/dev/null || echo "")
if [ ! -z "$SLACK_WEBHOOK" ]; then
    curl -X POST $SLACK_WEBHOOK \
        -H 'Content-type: application/json' \
        -d "{
            \"text\": \"✅ Database backup completed successfully\",
            \"attachments\": [{
                \"color\": \"good\",
                \"fields\": [
                    {\"title\": \"Backup Name\", \"value\": \"${BACKUP_NAME}\", \"short\": true},
                    {\"title\": \"Size\", \"value\": \"$(du -h $BACKUP_DIR/${BACKUP_NAME}.tar.gz | cut -f1)\", \"short\": true},
                    {\"title\": \"Location\", \"value\": \"s3://$S3_BUCKET/postgresql/\", \"short\": false}
                ]
            }]
        }" 2>/dev/null
fi

echo -e "${GREEN}✅ Database backup completed successfully!${NC}"