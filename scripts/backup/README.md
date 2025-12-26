# Mathvidya Database Backup & Restore

This directory contains scripts to backup and restore the PostgreSQL database running in Docker.

## Quick Start

### Create a Local Backup

**Linux/Mac (Git Bash on Windows):**
```bash
cd scripts/backup
./backup-local.sh
```

**Windows CMD:**
```cmd
cd scripts\backup
backup-local.bat
```

### Restore from Backup

**Linux/Mac:**
```bash
./restore.sh ./backups/mathvidya_backup_20241226_120000.sql.gz
```

**Windows:**
```cmd
restore.bat .\backups\mathvidya_backup_20241226_120000.sql
```

---

## Scripts Overview

| Script | Description |
|--------|-------------|
| `backup-local.sh` / `.bat` | Creates local backup with rotation |
| `backup-s3.sh` | Uploads backup to AWS S3 |
| `restore.sh` / `.bat` | Restores database from backup file |

---

## Detailed Usage

### 1. Local Backup (`backup-local.sh`)

Creates a compressed SQL dump and stores it locally. Automatically rotates old backups.

```bash
# Default: saves to ./backups, keeps last 7 backups
./backup-local.sh

# Custom backup directory
./backup-local.sh /path/to/backups

# Custom directory and retention count (keep 14 backups)
./backup-local.sh /path/to/backups 14
```

**Output:**
```
./backups/mathvidya_backup_20241226_120000.sql.gz
```

### 2. S3 Backup (`backup-s3.sh`)

Creates a local backup and uploads it to AWS S3. Useful for offsite disaster recovery.

**Prerequisites:**
- AWS CLI installed (`pip install awscli`)
- AWS credentials configured (`aws configure`)
- S3 bucket exists with write permissions

```bash
# Uses S3_BUCKET from .env file
./backup-s3.sh

# Specify bucket explicitly
./backup-s3.sh mathvidya-production

# Custom bucket and prefix
./backup-s3.sh mathvidya-production db-backups
```

**S3 Path Structure:**
```
s3://mathvidya-production/db-backups/2024/12/mathvidya_backup_20241226_120000.sql.gz
```

### 3. Restore (`restore.sh`)

Restores the database from a backup file. **Warning: This replaces all existing data!**

```bash
# Restore from local backup
./restore.sh ./backups/mathvidya_backup_20241226_120000.sql.gz

# Restore from S3 (download first)
aws s3 cp s3://mathvidya-production/db-backups/2024/12/mathvidya_backup_20241226_120000.sql.gz ./
./restore.sh mathvidya_backup_20241226_120000.sql.gz
```

**Safety Features:**
- Creates a pre-restore backup before making any changes
- Requires explicit "yes" confirmation
- Verifies table counts after restore

---

## Automated Backups

### Option 1: Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task → "Mathvidya Daily Backup"
3. Trigger: Daily at 2:00 AM
4. Action: Start a program
   - Program: `C:\path\to\mathvidya\scripts\backup\backup-local.bat`
   - Start in: `C:\path\to\mathvidya\scripts\backup`

### Option 2: Linux Cron Job

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /path/to/mathvidya/scripts/backup && ./backup-local.sh >> /var/log/mathvidya-backup.log 2>&1

# Add weekly S3 backup on Sundays at 3 AM
0 3 * * 0 cd /path/to/mathvidya/scripts/backup && ./backup-s3.sh >> /var/log/mathvidya-s3-backup.log 2>&1
```

### Option 3: Docker Cron Container

Add to `docker-compose.yml`:

```yaml
backup-cron:
  image: postgres:14-alpine
  volumes:
    - ./scripts/backup:/backup
    - ./backups:/backups
  environment:
    - PGHOST=postgres
    - PGUSER=mathvidya_user
    - PGPASSWORD=mathvidya_password
    - PGDATABASE=mathvidya
  command: >
    sh -c "echo '0 2 * * * pg_dump -U $$PGUSER $$PGDATABASE | gzip > /backups/mathvidya_backup_$$(date +%Y%m%d_%H%M%S).sql.gz' | crontab - && crond -f"
  depends_on:
    - postgres
```

---

## S3 Lifecycle Policy (Recommended)

Set up automatic cleanup in S3 to manage storage costs:

```json
{
  "Rules": [
    {
      "ID": "Delete old backups",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "db-backups/"
      },
      "Expiration": {
        "Days": 90
      },
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "GLACIER"
        }
      ]
    }
  ]
}
```

Apply via AWS Console or CLI:
```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket mathvidya-production \
  --lifecycle-configuration file://lifecycle.json
```

---

## Troubleshooting

### "Container not running" Error

```bash
# Start the database container
docker-compose up -d postgres

# Verify it's running
docker ps | grep mathvidya-postgres
```

### "Permission denied" on restore

The restore script terminates existing connections. If issues persist:

```bash
# Restart backend to release connections
docker-compose restart backend

# Then retry restore
./restore.sh backup_file.sql.gz
```

### AWS Credentials Error

```bash
# Configure AWS CLI
aws configure

# Test credentials
aws sts get-caller-identity

# Test S3 access
aws s3 ls s3://mathvidya-production/
```

### Backup File is Empty

Check if the database has data:
```bash
docker exec mathvidya-postgres psql -U mathvidya_user -d mathvidya -c "SELECT COUNT(*) FROM questions;"
```

---

## Best Practices

1. **Test restores regularly** - A backup is only useful if you can restore it
2. **Keep at least one offsite backup** - Use S3 or another cloud storage
3. **Automate backups** - Set up cron or Task Scheduler
4. **Monitor backup sizes** - Sudden changes may indicate issues
5. **Document restore procedures** - Know what to do in an emergency
6. **Backup before major changes** - Always backup before migrations or updates

---

## File Locations

| Location | Purpose |
|----------|---------|
| `./backups/` | Local backup storage |
| `s3://bucket/db-backups/` | S3 backup storage |
| `./backups/pre_restore_*.sql` | Safety backups before restore |
