#!/bin/bash
#
# Mathvidya Database Backup Script (AWS EC2 + S3)
#
# This script runs ON the EC2 server to backup the PostgreSQL database
# and upload it to S3. It should be deployed to the EC2 instance and
# run via cron for automated backups.
#
# Usage (on EC2):
#   ./backup-aws.sh                    # Uses defaults from environment
#   ./backup-aws.sh mathvidya-backups  # Specify S3 bucket
#
# Environment variables (set in /opt/mathvidya/.env or export):
#   S3_BACKUP_BUCKET - S3 bucket name for backups
#   POSTGRES_USER    - Database username
#   POSTGRES_DB      - Database name
#   AWS_REGION       - AWS region (default: ap-south-1)

set -e

# Load environment variables from .env if it exists
if [ -f /opt/mathvidya/.env ]; then
    export $(grep -v '^#' /opt/mathvidya/.env | xargs)
fi

# Configuration
CONTAINER_NAME="mathvidya-postgres"
DB_NAME="${POSTGRES_DB:-mathvidya}"
DB_USER="${POSTGRES_USER:-mathvidya_user}"
S3_BUCKET="${1:-${S3_BACKUP_BUCKET:-mathvidya-backups}}"
AWS_REGION="${AWS_REGION:-ap-south-1}"
LOCAL_BACKUP_DIR="/opt/mathvidya/backups"
LOCAL_RETENTION=3  # Keep 3 local backups on EC2

# Date-based paths
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_FOLDER=$(date +%Y/%m)
BACKUP_FILE="mathvidya_backup_${TIMESTAMP}.sql.gz"
S3_KEY="db-backups/${DATE_FOLDER}/${BACKUP_FILE}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "${BLUE}========================================${NC}"
log "${BLUE}  Mathvidya Database Backup (AWS)${NC}"
log "${BLUE}========================================${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    log "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    log "${RED}Error: Container '${CONTAINER_NAME}' is not running${NC}"
    log "Start with: cd /opt/mathvidya && docker-compose -f docker-compose.prod.yml up -d"
    exit 1
fi

# Create local backup directory
mkdir -p "$LOCAL_BACKUP_DIR"

# Step 1: Create database backup
log "${YELLOW}Step 1: Creating database backup...${NC}"
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$LOCAL_BACKUP_DIR/$BACKUP_FILE"

# Verify backup was created
if [ ! -s "$LOCAL_BACKUP_DIR/$BACKUP_FILE" ]; then
    log "${RED}Error: Backup file is empty or was not created${NC}"
    exit 1
fi

BACKUP_SIZE=$(du -h "$LOCAL_BACKUP_DIR/$BACKUP_FILE" | cut -f1)
log "  ${GREEN}Created:${NC} $BACKUP_FILE ($BACKUP_SIZE)"

# Step 2: Upload to S3
log "${YELLOW}Step 2: Uploading to S3...${NC}"
S3_PATH="s3://${S3_BUCKET}/${S3_KEY}"
log "  Target: ${S3_PATH}"

if aws s3 cp "$LOCAL_BACKUP_DIR/$BACKUP_FILE" "$S3_PATH" \
    --storage-class STANDARD_IA \
    --region "$AWS_REGION"; then
    log "  ${GREEN}Upload successful!${NC}"
else
    log "${RED}Error: S3 upload failed${NC}"
    exit 1
fi

# Step 3: Verify upload
log "${YELLOW}Step 3: Verifying S3 upload...${NC}"
if aws s3 ls "$S3_PATH" --region "$AWS_REGION" > /dev/null 2>&1; then
    S3_SIZE=$(aws s3 ls "$S3_PATH" --region "$AWS_REGION" | awk '{print $3}')
    log "  ${GREEN}Verified:${NC} $S3_SIZE bytes in S3"
else
    log "${RED}Warning: Could not verify S3 upload${NC}"
fi

# Step 4: Rotate local backups (keep only last N on EC2 to save disk space)
log "${YELLOW}Step 4: Rotating local backups (keeping ${LOCAL_RETENTION})...${NC}"
BACKUP_COUNT=$(ls -1 "$LOCAL_BACKUP_DIR"/mathvidya_backup_*.sql.gz 2>/dev/null | wc -l)

if [ "$BACKUP_COUNT" -gt "$LOCAL_RETENTION" ]; then
    DELETE_COUNT=$((BACKUP_COUNT - LOCAL_RETENTION))
    log "  Removing $DELETE_COUNT old local backup(s)..."
    ls -1t "$LOCAL_BACKUP_DIR"/mathvidya_backup_*.sql.gz | tail -n "$DELETE_COUNT" | xargs rm -f
fi

# Summary
log "${GREEN}========================================${NC}"
log "${GREEN}  Backup Complete!${NC}"
log "${GREEN}========================================${NC}"
log ""
log "Local: ${LOCAL_BACKUP_DIR}/${BACKUP_FILE}"
log "S3:    ${S3_PATH}"
log ""
log "To restore: ./restore-aws.sh ${S3_PATH}"
