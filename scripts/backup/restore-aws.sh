#!/bin/bash
#
# Mathvidya Database Restore Script (AWS EC2)
#
# This script runs ON the EC2 server to restore the PostgreSQL database
# from a local backup file or S3.
#
# Usage (on EC2):
#   ./restore-aws.sh <backup_file_or_s3_path>
#
# Examples:
#   ./restore-aws.sh /opt/mathvidya/backups/mathvidya_backup_20241226_120000.sql.gz
#   ./restore-aws.sh s3://mathvidya-backups/db-backups/2024/12/mathvidya_backup_20241226_120000.sql.gz

set -e

# Load environment variables
if [ -f /opt/mathvidya/.env ]; then
    export $(grep -v '^#' /opt/mathvidya/.env | xargs)
fi

# Configuration
CONTAINER_NAME="mathvidya-postgres"
DB_NAME="${POSTGRES_DB:-mathvidya}"
DB_USER="${POSTGRES_USER:-mathvidya_user}"
AWS_REGION="${AWS_REGION:-ap-south-1}"
LOCAL_BACKUP_DIR="/opt/mathvidya/backups"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "${YELLOW}========================================${NC}"
log "${YELLOW}  Mathvidya Database Restore (AWS)${NC}"
log "${YELLOW}========================================${NC}"

# Check arguments
if [ -z "$1" ]; then
    log "${RED}Error: No backup file specified${NC}"
    echo ""
    echo "Usage: ./restore-aws.sh <backup_file_or_s3_path>"
    echo ""
    echo "Local backups:"
    ls -lh "$LOCAL_BACKUP_DIR"/mathvidya_backup_*.sql.gz 2>/dev/null || echo "  No local backups found"
    echo ""
    echo "S3 backups (recent):"
    aws s3 ls "s3://${S3_BACKUP_BUCKET:-mathvidya-backups}/db-backups/" --recursive --region "$AWS_REGION" 2>/dev/null | tail -10 || echo "  Could not list S3 backups"
    exit 1
fi

BACKUP_SOURCE="$1"
BACKUP_FILE=""

# Check if source is S3 path
if [[ "$BACKUP_SOURCE" == s3://* ]]; then
    log "Downloading from S3: $BACKUP_SOURCE"
    mkdir -p "$LOCAL_BACKUP_DIR"
    BACKUP_FILE="$LOCAL_BACKUP_DIR/restore_$(date +%Y%m%d_%H%M%S).sql.gz"

    if aws s3 cp "$BACKUP_SOURCE" "$BACKUP_FILE" --region "$AWS_REGION"; then
        log "  ${GREEN}Downloaded successfully${NC}"
    else
        log "${RED}Error: Failed to download from S3${NC}"
        exit 1
    fi
else
    BACKUP_FILE="$BACKUP_SOURCE"
fi

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    log "${RED}Error: Backup file not found: ${BACKUP_FILE}${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    log "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    log "${RED}Error: Container '${CONTAINER_NAME}' is not running${NC}"
    exit 1
fi

# Display backup info
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
log "Backup file: $BACKUP_FILE"
log "File size:   $BACKUP_SIZE"
echo ""

# Warning and confirmation
log "${RED}WARNING: This will REPLACE ALL DATA in the database!${NC}"
log "${RED}All current data will be lost!${NC}"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo ""
    log "Restore cancelled."
    exit 0
fi

log ""
log "${YELLOW}Starting restore process...${NC}"

# Step 1: Create pre-restore backup
log "${YELLOW}Step 1: Creating pre-restore backup (safety)...${NC}"
PRE_RESTORE_FILE="$LOCAL_BACKUP_DIR/pre_restore_$(date +%Y%m%d_%H%M%S).sql.gz"
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$PRE_RESTORE_FILE"
log "  ${GREEN}Created:${NC} $PRE_RESTORE_FILE"

# Also upload pre-restore backup to S3
if [ -n "${S3_BACKUP_BUCKET}" ]; then
    S3_PRE_RESTORE="s3://${S3_BACKUP_BUCKET}/db-backups/pre-restore/$(basename $PRE_RESTORE_FILE)"
    aws s3 cp "$PRE_RESTORE_FILE" "$S3_PRE_RESTORE" --region "$AWS_REGION" --quiet
    log "  ${GREEN}Uploaded to S3:${NC} $S3_PRE_RESTORE"
fi

# Step 2: Stop backend services to release connections
log "${YELLOW}Step 2: Stopping application services...${NC}"
cd /opt/mathvidya
docker-compose -f docker-compose.prod.yml stop backend celery_worker celery_beat 2>/dev/null || true
log "  ${GREEN}Services stopped${NC}"

# Step 3: Drop and recreate database
log "${YELLOW}Step 3: Preparing database...${NC}"

# Terminate existing connections
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -c "
    SELECT pg_terminate_backend(pg_stat_activity.pid)
    FROM pg_stat_activity
    WHERE pg_stat_activity.datname = '${DB_NAME}'
    AND pid <> pg_backend_pid();" > /dev/null 2>&1 || true

# Drop and recreate
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};"
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"
log "  ${GREEN}Database recreated${NC}"

# Step 4: Restore from backup
log "${YELLOW}Step 4: Restoring from backup...${NC}"
gunzip -c "$BACKUP_FILE" | docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME"
log "  ${GREEN}Restore completed${NC}"

# Step 5: Restart application services
log "${YELLOW}Step 5: Restarting application services...${NC}"
docker-compose -f docker-compose.prod.yml up -d backend celery_worker celery_beat
log "  ${GREEN}Services started${NC}"

# Step 6: Verify restore
log "${YELLOW}Step 6: Verifying restore...${NC}"
sleep 3  # Wait for services to start

TABLE_COUNT=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
log "  Tables restored: ${TABLE_COUNT}"

log "  Row counts:"
for table in users questions exam_templates subscriptions; do
    count=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
        "SELECT COUNT(*) FROM ${table};" 2>/dev/null || echo "0")
    log "    - ${table}: ${count}"
done

log ""
log "${GREEN}========================================${NC}"
log "${GREEN}  Restore Complete!${NC}"
log "${GREEN}========================================${NC}"
log ""
log "Pre-restore backup: ${PRE_RESTORE_FILE}"
if [ -n "${S3_BACKUP_BUCKET}" ]; then
    log "Pre-restore S3:     ${S3_PRE_RESTORE}"
fi
