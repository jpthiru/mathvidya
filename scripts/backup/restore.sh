#!/bin/bash
#
# Mathvidya Database Restore Script
#
# Restores the PostgreSQL database from a backup file.
# CAUTION: This will REPLACE all data in the current database!
#
# Usage: ./restore.sh <backup_file>
#
# Examples:
#   ./restore.sh ./backups/mathvidya_backup_20241226_120000.sql.gz
#   ./restore.sh mathvidya_backup_20241226_120000.sql.gz

set -e

# Configuration
CONTAINER_NAME="mathvidya-postgres"
DB_NAME="mathvidya"
DB_USER="mathvidya_user"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  Mathvidya Database Restore${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Check arguments
if [ -z "$1" ]; then
    echo -e "${RED}Error: No backup file specified${NC}"
    echo ""
    echo "Usage: ./restore.sh <backup_file>"
    echo ""
    echo "Available backups:"
    ls -lh ./backups/mathvidya_backup_*.sql.gz 2>/dev/null || echo "  No backups found in ./backups/"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found: ${BACKUP_FILE}${NC}"
    exit 1
fi

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

# Display backup info
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
BACKUP_DATE=$(echo "$BACKUP_FILE" | grep -oP '\d{8}_\d{6}' | head -1 || echo "unknown")
echo -e "Backup file: ${BACKUP_FILE}"
echo -e "File size:   ${BACKUP_SIZE}"
echo -e "Backup date: ${BACKUP_DATE}"
echo ""

# Warning and confirmation
echo -e "${RED}WARNING: This will REPLACE ALL DATA in the database!${NC}"
echo -e "${RED}All current data will be lost!${NC}"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo ""
    echo "Restore cancelled."
    exit 0
fi

echo ""
echo -e "${YELLOW}Starting restore process...${NC}"

# Step 1: Create a pre-restore backup (safety)
echo ""
echo -e "${YELLOW}Step 1: Creating pre-restore backup (safety)...${NC}"
PRE_RESTORE_FILE="./backups/pre_restore_$(date +%Y%m%d_%H%M%S).sql.gz"
mkdir -p ./backups
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$PRE_RESTORE_FILE"
echo -e "  ${GREEN}Created:${NC} $PRE_RESTORE_FILE"

# Step 2: Drop and recreate database
echo ""
echo -e "${YELLOW}Step 2: Preparing database...${NC}"

# Terminate existing connections
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -c "
    SELECT pg_terminate_backend(pg_stat_activity.pid)
    FROM pg_stat_activity
    WHERE pg_stat_activity.datname = '${DB_NAME}'
    AND pid <> pg_backend_pid();" > /dev/null 2>&1 || true

# Drop and recreate
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};"
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"
echo -e "  ${GREEN}Database recreated${NC}"

# Step 3: Restore from backup
echo ""
echo -e "${YELLOW}Step 3: Restoring from backup...${NC}"

# Check if file is gzipped
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME"
else
    cat "$BACKUP_FILE" | docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME"
fi

echo -e "  ${GREEN}Restore completed${NC}"

# Step 4: Verify restore
echo ""
echo -e "${YELLOW}Step 4: Verifying restore...${NC}"
TABLE_COUNT=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
echo -e "  Tables restored: ${TABLE_COUNT}"

# Get row counts for key tables
echo -e "  Row counts:"
for table in users questions exam_templates subscriptions; do
    count=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM ${table};" 2>/dev/null || echo "0")
    echo -e "    - ${table}: ${count}"
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Restore Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Pre-restore backup saved at: ${PRE_RESTORE_FILE}"
echo ""
echo -e "${YELLOW}Note:${NC} You may need to restart the backend service:"
echo "  docker-compose restart backend"
