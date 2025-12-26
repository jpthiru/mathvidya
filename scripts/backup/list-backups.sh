#!/bin/bash
#
# Mathvidya - List Available Backups
#
# Lists all available backups from local storage and S3.
#
# Usage (on EC2):
#   ./list-backups.sh

# Load environment variables
if [ -f /opt/mathvidya/.env ]; then
    export $(grep -v '^#' /opt/mathvidya/.env | xargs)
fi

# Configuration
LOCAL_BACKUP_DIR="/opt/mathvidya/backups"
S3_BUCKET="${S3_BACKUP_BUCKET:-mathvidya-backups}"
AWS_REGION="${AWS_REGION:-ap-south-1}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Mathvidya Available Backups${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Local backups
echo -e "${YELLOW}Local Backups (${LOCAL_BACKUP_DIR}):${NC}"
if ls "$LOCAL_BACKUP_DIR"/mathvidya_backup_*.sql.gz 1>/dev/null 2>&1; then
    ls -lh "$LOCAL_BACKUP_DIR"/mathvidya_backup_*.sql.gz | awk '{print "  " $9 " (" $5 ", " $6 " " $7 ")"}'
else
    echo "  No local backups found"
fi

echo ""

# S3 backups
echo -e "${YELLOW}S3 Backups (s3://${S3_BUCKET}/db-backups/):${NC}"
if aws s3 ls "s3://${S3_BUCKET}/db-backups/" --recursive --region "$AWS_REGION" 2>/dev/null | grep -v "pre-restore" | tail -20; then
    :
else
    echo "  No S3 backups found or could not connect to S3"
fi

echo ""
echo -e "${GREEN}To restore from backup:${NC}"
echo "  ./restore-aws.sh <backup_file_or_s3_path>"
echo ""
echo -e "${GREEN}Examples:${NC}"
echo "  ./restore-aws.sh /opt/mathvidya/backups/mathvidya_backup_20241226_120000.sql.gz"
echo "  ./restore-aws.sh s3://${S3_BUCKET}/db-backups/2024/12/mathvidya_backup_20241226_120000.sql.gz"
