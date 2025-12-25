# Mathvidya Infrastructure

This directory contains the Terraform configuration for deploying Mathvidya to AWS.

## Architecture

```
                     ┌──────────────┐
                     │  CloudFlare  │  (DNS + CDN + DDoS Protection)
                     │    or        │
                     │  Route 53    │
                     └──────┬───────┘
                            │
                     ┌──────▼───────┐
                     │   Elastic IP │
                     └──────┬───────┘
                            │
┌───────────────────────────▼───────────────────────────┐
│                    VPC (10.0.0.0/16)                  │
│  ┌─────────────────────────────────────────────────┐  │
│  │              Public Subnet (10.0.1.0/24)        │  │
│  │  ┌───────────────────────────────────────────┐  │  │
│  │  │            EC2 t3.small                   │  │  │
│  │  │  ┌─────────────────────────────────────┐  │  │  │
│  │  │  │           Nginx (SSL)               │  │  │  │
│  │  │  └─────────────────────────────────────┘  │  │  │
│  │  │  ┌─────────────────────────────────────┐  │  │  │
│  │  │  │        Docker Compose               │  │  │  │
│  │  │  │  ┌─────────┐ ┌─────────┐ ┌───────┐  │  │  │  │
│  │  │  │  │ FastAPI │ │ Celery  │ │ Redis │  │  │  │  │
│  │  │  │  └─────────┘ └─────────┘ └───────┘  │  │  │  │
│  │  │  │  ┌─────────────────────────────────┐│  │  │  │
│  │  │  │  │         PostgreSQL              ││  │  │  │
│  │  │  │  └─────────────────────────────────┘│  │  │  │
│  │  │  └─────────────────────────────────────┘  │  │  │
│  │  └───────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────┘  │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │         Private Subnet (10.0.10.0/24)           │  │
│  │         (Reserved for future RDS)               │  │
│  └─────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────┘
                            │
                     ┌──────▼───────┐
                     │      S3      │
                     │  (Media +    │
                     │   Backups)   │
                     └──────────────┘
```

## Cost Breakdown

| Resource | Monthly Cost |
|----------|--------------|
| EC2 t3.small | ~$15 |
| EBS 30GB gp3 | ~$2.50 |
| Elastic IP | $0 (when attached) |
| S3 (50GB) | ~$1-2 |
| Data Transfer | ~$2-5 |
| **Total** | **~$20-25/month** |

## Prerequisites

1. **AWS Account** with CLI configured
2. **Terraform** >= 1.0 installed
3. **SSH Key Pair** generated locally
4. **Domain** (mathvidya.com) registered

## Quick Start

### 1. Install Terraform

```bash
# macOS
brew install terraform

# Windows (with Chocolatey)
choco install terraform

# Linux
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

### 2. Configure AWS CLI

```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Default region: ap-south-1
# Default output format: json
```

### 3. Generate SSH Key

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/mathvidya-key -N ""
```

### 4. Create Variables File

```bash
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
project_name = "mathvidya"
environment  = "prod"
aws_region   = "ap-south-1"
domain_name  = "mathvidya.com"

# Paste your public key
ssh_public_key = "ssh-rsa AAAA... (contents of ~/.ssh/mathvidya-key.pub)"

# Your IP for SSH access (find with: curl ifconfig.me)
ssh_allowed_cidrs = ["YOUR_IP/32"]

# Strong passwords (generate with: openssl rand -base64 32)
db_password = "your-strong-password-here"
secret_key  = "your-secret-key-here"

alarm_email = "your-email@example.com"
```

### 5. Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Apply changes
terraform apply
```

### 6. Note the Outputs

After successful deployment, note these values:
- `ec2_public_ip` - IP address for DNS
- `ssh_command` - SSH command to connect
- `s3_media_bucket` - Bucket name for media files

## Post-Deployment Setup

### 1. Configure DNS

Add these DNS records (in CloudFlare or your DNS provider):

| Type | Name | Value |
|------|------|-------|
| A | @ | [ec2_public_ip] |
| A | www | [ec2_public_ip] |

### 2. SSH into Server

```bash
ssh -i ~/.ssh/mathvidya-key ec2-user@[ec2_public_ip]
```

### 3. Clone Repository

```bash
cd /opt/mathvidya
git clone https://github.com/your-org/mathvidya.git .
```

### 4. Build and Start Application

```bash
# Build frontend
cd frontend-react
npm install
npm run build
cd ..

# Start Docker containers
docker-compose -f docker-compose.prod.yml up -d

# Run database migrations
docker exec mathvidya-backend alembic upgrade head
```

### 5. Get SSL Certificate

```bash
# After DNS propagation (5-30 minutes)
sudo certbot --nginx -d mathvidya.com -d www.mathvidya.com
```

## Maintenance

### View Logs

```bash
# All containers
docker-compose -f docker-compose.prod.yml logs -f

# Specific container
docker logs -f mathvidya-backend
docker logs -f mathvidya-postgres

# Nginx
sudo tail -f /var/log/nginx/error.log
```

### Deploy Updates

```bash
cd /opt/mathvidya
./deploy.sh
```

### Backup Database

```bash
./backup.sh
```

### Restore Database

```bash
# Download from S3
aws s3 cp s3://mathvidya-backups-prod/database/mathvidya_db_TIMESTAMP.sql.gz .

# Restore
gunzip mathvidya_db_TIMESTAMP.sql.gz
docker exec -i mathvidya-postgres psql -U mathvidya_user -d mathvidya < mathvidya_db_TIMESTAMP.sql
```

## Security Checklist

- [x] VPC with public/private subnets
- [x] Security groups with minimal access
- [x] SSH restricted to specific IPs
- [x] SSL/TLS encryption (Certbot)
- [x] Database in private network (Docker)
- [x] S3 buckets with encryption
- [x] IAM roles with least privilege
- [x] CloudWatch monitoring and alerts
- [x] Automated backups to S3
- [x] Rate limiting on API endpoints

## Scaling Up

When you need more capacity:

### Option 1: Vertical Scaling
```hcl
# In terraform.tfvars
instance_type = "t3.medium"  # or t3.large
```

### Option 2: Add RDS (Managed Database)
Add to main.tf:
```hcl
resource "aws_db_instance" "main" {
  identifier        = "mathvidya-db"
  engine            = "postgres"
  engine_version    = "14"
  instance_class    = "db.t3.micro"
  allocated_storage = 20
  # ... more configuration
}
```

### Option 3: Migrate to ECS
See `infrastructure/terraform-ecs/` (future)

## Troubleshooting

### Can't SSH into instance
```bash
# Check security group allows your IP
terraform state show aws_security_group.app

# Check instance is running
aws ec2 describe-instance-status --instance-ids [instance-id]
```

### Docker containers not starting
```bash
ssh into instance
cd /opt/mathvidya
docker-compose -f docker-compose.prod.yml logs
```

### SSL certificate issues
```bash
# Check certificate status
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal
```

### Database connection issues
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check logs
docker logs mathvidya-postgres
```

## Files Structure

```
infrastructure/
├── terraform/
│   ├── main.tf              # Main infrastructure
│   ├── variables.tf         # Variable definitions
│   ├── outputs.tf           # Output values
│   ├── terraform.tfvars.example  # Example variables
│   ├── .gitignore           # Ignore sensitive files
│   └── scripts/
│       └── user_data.sh     # EC2 bootstrap script
└── README.md                # This file
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review AWS CloudWatch logs
3. Open an issue in the repository
