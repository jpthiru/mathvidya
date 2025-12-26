#!/bin/bash
#
# Mathvidya Database Backup Script (Local)
#
# Creates a compressed backup of the PostgreSQL database and stores it locally.
# Maintains rotation: keeps last N backups (default: 7)
#
# Usage: ./backup-local.sh [backup_dir] [retention_count]
#
# Examples:
#   ./backup-local.sh                          # Uses default ./backups dir, keeps 7 backups
#   ./backup-local.sh /path/to/backups         # Custom backup directory
#   ./backup-local.sh /path/to/backups 14      # Keep 14 backups

set -e

# Configuration
CONTAINER_NAME="mathvidya-postgres"
DB_NAME="mathvidya"
DB_USER="mathvidya_user"
BACKUP_DIR="${1:-./backups}"
RETENTION_COUNT="${2:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="mathvidya_backup_${TIMESTAMP}.sql.gz"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Mathvidya Database Backup (Local)${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Check if container exists and is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}Error: Container '${CONTAINER_NAME}' is not running${NC}"
    echo "Please ensure the database container is up:"
    echo "  docker-compose up -d postgres"
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"
echo -e "${YELLOW}Backup directory:${NC} $BACKUP_DIR"

# Create the backup
echo -e "${YELLOW}Creating backup...${NC}"
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/$BACKUP_FILE"

# Verify backup was created and has content
if [ -s "$BACKUP_DIR/$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}Backup created successfully!${NC}"
    echo -e "  File: ${BACKUP_FILE}"
    echo -e "  Size: ${BACKUP_SIZE}"
else
    echo -e "${RED}Error: Backup file is empty or was not created${NC}"
    rm -f "$BACKUP_DIR/$BACKUP_FILE"
    exit 1
fi

# Rotate old backups (keep only the last N)
echo ""
echo -e "${YELLOW}Rotating backups (keeping last ${RETENTION_COUNT})...${NC}"
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/mathvidya_backup_*.sql.gz 2>/dev/null | wc -l)

if [ "$BACKUP_COUNT" -gt "$RETENTION_COUNT" ]; then
    DELETE_COUNT=$((BACKUP_COUNT - RETENTION_COUNT))
    echo "  Removing $DELETE_COUNT old backup(s)..."
    ls -1t "$BACKUP_DIR"/mathvidya_backup_*.sql.gz | tail -n "$DELETE_COUNT" | xargs rm -f
fi

# List current backups
echo ""
echo -e "${GREEN}Current backups:${NC}"
ls -lh "$BACKUP_DIR"/mathvidya_backup_*.sql.gz 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'

echo ""
echo -e "${GREEN}Backup completed successfully!${NC}"
echo -e "To restore, use: ./restore.sh $BACKUP_DIR/$BACKUP_FILE"
