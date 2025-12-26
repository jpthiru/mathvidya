# Mathvidya Database Backup & Restore (AWS)

Database backup and restore scripts for the Mathvidya PostgreSQL database running on AWS EC2.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  AWS EC2 Instance                                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Docker                                              │   │
│  │  ┌─────────────────┐  ┌───────────────────────────┐ │   │
│  │  │ mathvidya-      │  │ mathvidya-backend         │ │   │
│  │  │ postgres        │  │ celery-worker             │ │   │
│  │  │ (PostgreSQL 14) │  │ celery-beat               │ │   │
│  │  └─────────────────┘  └───────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                                │
│  /opt/mathvidya/backups/   │  (local backup storage)       │
└────────────────────────────┼────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────────┐
                    │  AWS S3            │
                    │  mathvidya-backups │
                    │  /db-backups/      │
                    │    /2024/12/       │
                    └────────────────────┘
```

## Quick Start

### 1. Deploy Scripts to EC2

From your local machine:
```bash
# SSH into EC2
ssh -i ~/.ssh/mathvidya-key ec2-user@<EC2_IP>

# Create scripts directory
mkdir -p /opt/mathvidya/scripts/backup
cd /opt/mathvidya/scripts/backup

# Copy scripts (or clone from git)
# The scripts are in: scripts/backup/
```

### 2. Create a Backup

On the EC2 instance:
```bash
cd /opt/mathvidya/scripts/backup
./backup-aws.sh
```

### 3. List Available Backups

```bash
./list-backups.sh
```

### 4. Restore from Backup

```bash
# From local file
./restore-aws.sh /opt/mathvidya/backups/mathvidya_backup_20241226_120000.sql.gz

# From S3
./restore-aws.sh s3://mathvidya-backups/db-backups/2024/12/mathvidya_backup_20241226_120000.sql.gz
```

---

## Scripts Overview

| Script | Description |
|--------|-------------|
| `backup-aws.sh` | Creates backup and uploads to S3 |
| `restore-aws.sh` | Restores from local file or S3 |
| `list-backups.sh` | Lists all available backups |

### Local-only Scripts (for development)

| Script | Description |
|--------|-------------|
| `backup-local.sh` | Creates local backup only (Windows/Linux) |
| `restore.sh` | Restores locally (Windows/Linux) |

---

## Detailed Usage

### backup-aws.sh

Creates a compressed SQL dump and uploads to S3.

```bash
# Uses environment variables from /opt/mathvidya/.env
./backup-aws.sh

# Or specify bucket explicitly
./backup-aws.sh mathvidya-backups
```

**What it does:**
1. Dumps PostgreSQL database to compressed `.sql.gz` file
2. Uploads to S3 with date-based folder structure: `s3://bucket/db-backups/2024/12/file.sql.gz`
3. Uses STANDARD_IA storage class (cost-effective for backups)
4. Keeps last 3 local backups on EC2 (saves disk space)

**Environment variables:**
```bash
S3_BACKUP_BUCKET=mathvidya-backups
POSTGRES_USER=mathvidya_user
POSTGRES_DB=mathvidya
AWS_REGION=ap-south-1
```

### restore-aws.sh

Restores database from a backup file or S3 path.

```bash
# From local backup
./restore-aws.sh /opt/mathvidya/backups/mathvidya_backup_20241226_120000.sql.gz

# From S3 (downloads automatically)
./restore-aws.sh s3://mathvidya-backups/db-backups/2024/12/mathvidya_backup_20241226_120000.sql.gz
```

**What it does:**
1. Downloads from S3 if needed
2. Creates a pre-restore backup (safety)
3. Stops backend services
4. Drops and recreates database
5. Restores data
6. Restarts backend services
7. Verifies table counts

---

## Automated Backups (Cron)

### Set up daily backups at 2 AM IST

SSH into EC2 and run:
```bash
# Edit crontab
crontab -e

# Add this line (2 AM IST = 8:30 PM UTC previous day)
30 20 * * * /opt/mathvidya/scripts/backup/backup-aws.sh >> /var/log/mathvidya-backup.log 2>&1
```

### Verify cron is working

```bash
# Check cron logs
tail -f /var/log/mathvidya-backup.log

# List cron jobs
crontab -l
```

---

## S3 Lifecycle Policy

Configure S3 to automatically manage old backups and reduce storage costs.

### Via AWS Console:

1. Go to S3 → mathvidya-backups → Management → Lifecycle rules
2. Create rule:
   - Name: `backup-lifecycle`
   - Prefix: `db-backups/`
   - Transitions:
     - Move to Glacier after 30 days
   - Expiration:
     - Delete after 90 days

### Via AWS CLI:

```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket mathvidya-backups \
  --lifecycle-configuration '{
    "Rules": [
      {
        "ID": "backup-lifecycle",
        "Status": "Enabled",
        "Filter": { "Prefix": "db-backups/" },
        "Transitions": [
          { "Days": 30, "StorageClass": "GLACIER" }
        ],
        "Expiration": { "Days": 90 }
      }
    ]
  }'
```

---

## Remote Backup (from local machine)

If you want to trigger backups from your local machine:

```bash
# Run backup on EC2 remotely
ssh -i ~/.ssh/mathvidya-key ec2-user@<EC2_IP> "/opt/mathvidya/scripts/backup/backup-aws.sh"

# Download latest backup to local machine
ssh -i ~/.ssh/mathvidya-key ec2-user@<EC2_IP> "cat /opt/mathvidya/backups/\$(ls -t /opt/mathvidya/backups/mathvidya_backup_*.sql.gz | head -1)" > local_backup.sql.gz
```

---

## Troubleshooting

### "Container not running" Error

```bash
cd /opt/mathvidya
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml up -d postgres
```

### "Permission denied" Error

```bash
chmod +x /opt/mathvidya/scripts/backup/*.sh
```

### AWS Credentials Error

EC2 should use IAM Instance Role for S3 access. If not configured:
```bash
# Check IAM role
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/

# Or configure AWS CLI
aws configure
```

### Backup File is Empty

Check database has data:
```bash
docker exec mathvidya-postgres psql -U mathvidya_user -d mathvidya -c "SELECT COUNT(*) FROM questions;"
```

### Disk Space Issues on EC2

The scripts keep only 3 local backups. To free more space:
```bash
# Remove old backups (keep only latest)
ls -t /opt/mathvidya/backups/mathvidya_backup_*.sql.gz | tail -n +2 | xargs rm -f

# Check disk usage
df -h
```

---

## Best Practices

1. **Automated backups** - Set up cron for daily backups
2. **Test restores regularly** - At least monthly
3. **Monitor backup sizes** - Sudden changes may indicate issues
4. **Keep S3 lifecycle rules** - Manage costs with Glacier transition
5. **Backup before migrations** - Always backup before schema changes
6. **Document EC2 credentials** - Keep SSH key secure

---

## File Locations

| Location | Purpose |
|----------|---------|
| `/opt/mathvidya/scripts/backup/` | Backup scripts on EC2 |
| `/opt/mathvidya/backups/` | Local backups on EC2 |
| `s3://mathvidya-backups/db-backups/` | S3 backup storage |
| `/var/log/mathvidya-backup.log` | Backup cron logs |

---

## Recovery Scenarios

### Scenario 1: Application Error (recent data loss)

```bash
# List recent backups
./list-backups.sh

# Restore from today's backup
./restore-aws.sh /opt/mathvidya/backups/mathvidya_backup_20241226_020000.sql.gz
```

### Scenario 2: EC2 Instance Lost

1. Launch new EC2 instance
2. Set up Docker and deploy application
3. Download latest backup from S3:
   ```bash
   aws s3 cp s3://mathvidya-backups/db-backups/2024/12/mathvidya_backup_20241226_020000.sql.gz .
   ```
4. Restore database

### Scenario 3: Need to Rollback Migration

```bash
# Pre-migration backup is created automatically
# Find it in S3
aws s3 ls s3://mathvidya-backups/db-backups/pre-restore/

# Restore pre-migration state
./restore-aws.sh s3://mathvidya-backups/db-backups/pre-restore/pre_restore_20241226_120000.sql.gz
```
