#!/bin/bash
#
# Mathvidya Database Backup Script (S3)
#
# Creates a compressed backup of the PostgreSQL database and uploads it to AWS S3.
# Also maintains a local copy and rotates old backups.
#
# Prerequisites:
#   - AWS CLI installed and configured (aws configure)
#   - S3 bucket exists with appropriate permissions
#
# Usage: ./backup-s3.sh [s3_bucket] [s3_prefix]
#
# Examples:
#   ./backup-s3.sh                                    # Uses default bucket from .env
#   ./backup-s3.sh mathvidya-production               # Custom bucket
#   ./backup-s3.sh mathvidya-production db-backups    # Custom bucket and prefix

set -e

# Load environment variables if .env exists
if [ -f "../../backend/.env" ]; then
    export $(grep -v '^#' ../../backend/.env | xargs)
fi

# Configuration
CONTAINER_NAME="mathvidya-postgres"
DB_NAME="mathvidya"
DB_USER="mathvidya_user"
LOCAL_BACKUP_DIR="./backups"
S3_BUCKET="${1:-${S3_BUCKET:-mathvidya-production}}"
S3_PREFIX="${2:-db-backups}"
LOCAL_RETENTION=3  # Keep 3 local backups
S3_RETENTION=30    # Keep 30 days in S3 (via lifecycle policy)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_FOLDER=$(date +%Y/%m)
BACKUP_FILE="mathvidya_backup_${TIMESTAMP}.sql.gz"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Mathvidya Database Backup (S3)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    echo "Install it with: pip install awscli"
    echo "Then configure with: aws configure"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}Error: AWS credentials not configured or invalid${NC}"
    echo "Run: aws configure"
    exit 1
fi

# Check if container exists and is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}Error: Container '${CONTAINER_NAME}' is not running${NC}"
    exit 1
fi

# Create local backup directory
mkdir -p "$LOCAL_BACKUP_DIR"

# Step 1: Create local backup
echo -e "${YELLOW}Step 1: Creating database backup...${NC}"
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$LOCAL_BACKUP_DIR/$BACKUP_FILE"

# Verify backup
if [ ! -s "$LOCAL_BACKUP_DIR/$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file is empty${NC}"
    exit 1
fi

BACKUP_SIZE=$(du -h "$LOCAL_BACKUP_DIR/$BACKUP_FILE" | cut -f1)
echo -e "  ${GREEN}Created:${NC} $BACKUP_FILE ($BACKUP_SIZE)"

# Step 2: Upload to S3
echo ""
echo -e "${YELLOW}Step 2: Uploading to S3...${NC}"
S3_PATH="s3://${S3_BUCKET}/${S3_PREFIX}/${DATE_FOLDER}/${BACKUP_FILE}"
echo -e "  Target: ${S3_PATH}"

if aws s3 cp "$LOCAL_BACKUP_DIR/$BACKUP_FILE" "$S3_PATH" --storage-class STANDARD_IA; then
    echo -e "  ${GREEN}Upload successful!${NC}"
else
    echo -e "${RED}Error: S3 upload failed${NC}"
    exit 1
fi

# Step 3: Verify upload
echo ""
echo -e "${YELLOW}Step 3: Verifying S3 upload...${NC}"
if aws s3 ls "$S3_PATH" > /dev/null 2>&1; then
    S3_SIZE=$(aws s3 ls "$S3_PATH" | awk '{print $3}')
    echo -e "  ${GREEN}Verified:${NC} $S3_SIZE bytes in S3"
else
    echo -e "${RED}Warning: Could not verify S3 upload${NC}"
fi

# Step 4: Rotate local backups
echo ""
echo -e "${YELLOW}Step 4: Rotating local backups (keeping ${LOCAL_RETENTION})...${NC}"
BACKUP_COUNT=$(ls -1 "$LOCAL_BACKUP_DIR"/mathvidya_backup_*.sql.gz 2>/dev/null | wc -l)

if [ "$BACKUP_COUNT" -gt "$LOCAL_RETENTION" ]; then
    DELETE_COUNT=$((BACKUP_COUNT - LOCAL_RETENTION))
    echo "  Removing $DELETE_COUNT old local backup(s)..."
    ls -1t "$LOCAL_BACKUP_DIR"/mathvidya_backup_*.sql.gz | tail -n "$DELETE_COUNT" | xargs rm -f
fi

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Backup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Local backup: ${LOCAL_BACKUP_DIR}/${BACKUP_FILE}"
echo -e "S3 location:  ${S3_PATH}"
echo ""
echo -e "${YELLOW}To restore from S3:${NC}"
echo "  aws s3 cp $S3_PATH ./backup.sql.gz"
echo "  ./restore.sh ./backup.sql.gz"
