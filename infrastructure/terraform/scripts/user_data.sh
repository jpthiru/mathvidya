#!/bin/bash
# Mathvidya EC2 Bootstrap Script (Minimal)
set -e

# Variables from Terraform
PROJECT_NAME="${project_name}"
DOMAIN_NAME="${domain_name}"
DB_PASSWORD="${db_password}"
SECRET_KEY="${secret_key}"
S3_MEDIA_BUCKET="${s3_media_bucket}"
S3_BACKUP_BUCKET="${s3_backup_bucket}"
AWS_REGION="${aws_region}"

exec > >(tee /var/log/user-data.log) 2>&1
echo "Starting bootstrap at $(date)"

# Install packages
dnf update -y
dnf install -y docker nginx certbot python3-certbot-nginx git htop vim jq

# Docker setup
systemctl start docker && systemctl enable docker
usermod -aG docker ec2-user

# Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# Create app directory
mkdir -p /opt/mathvidya
chown ec2-user:ec2-user /opt/mathvidya

# Create .env file
cat > /opt/mathvidya/.env << EOF
DATABASE_URL=postgresql+asyncpg://mathvidya_user:$${DB_PASSWORD}@postgres:5432/mathvidya
POSTGRES_DB=mathvidya
POSTGRES_USER=mathvidya_user
POSTGRES_PASSWORD=$${DB_PASSWORD}
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
SECRET_KEY=$${SECRET_KEY}
DEBUG=False
AWS_REGION=$${AWS_REGION}
S3_MEDIA_BUCKET=$${S3_MEDIA_BUCKET}
S3_BACKUP_BUCKET=$${S3_BACKUP_BUCKET}
EOF
chmod 600 /opt/mathvidya/.env
chown ec2-user:ec2-user /opt/mathvidya/.env

# Nginx config
mv /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup 2>/dev/null || true
cat > /etc/nginx/nginx.conf << 'NGINXCONF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;
events { worker_connections 1024; }
http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    sendfile on;
    keepalive_timeout 65;
    gzip on;
    include /etc/nginx/conf.d/*.conf;
}
NGINXCONF

cat > /etc/nginx/conf.d/mathvidya.conf << SITECONF
server {
    listen 80;
    server_name $${DOMAIN_NAME} www.$${DOMAIN_NAME};
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 301 https://\\\$host\\\$request_uri; }
}
server {
    listen 443 ssl;
    server_name $${DOMAIN_NAME} www.$${DOMAIN_NAME};
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    location / {
        root /opt/mathvidya/frontend-react/dist;
        try_files \\\$uri \\\$uri/ /index.html;
    }
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
    }
}
SITECONF

mkdir -p /etc/nginx/ssl /var/www/certbot
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/privkey.pem \
    -out /etc/nginx/ssl/fullchain.pem \
    -subj "/CN=$${DOMAIN_NAME}"

systemctl start nginx && systemctl enable nginx

echo "Bootstrap completed at $(date)"
echo "Next: Clone repo to /opt/mathvidya, run docker-compose -f docker-compose.yml up -d"
