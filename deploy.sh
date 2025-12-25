#!/bin/bash
# Mathvidya Deployment Script
set -e

echo "=========================================="
echo "Mathvidya Deployment Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as ec2-user
if [ "$USER" != "ec2-user" ]; then
    echo -e "${RED}Please run as ec2-user${NC}"
    exit 1
fi

APP_DIR="/opt/mathvidya"
cd $APP_DIR

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}.env file not found! Please create it first.${NC}"
    echo "Expected location: $APP_DIR/.env"
    exit 1
fi

echo -e "${GREEN}Step 1: Pulling latest code...${NC}"
git pull origin main || git pull origin master || echo "First deployment - no pull needed"

echo -e "${GREEN}Step 2: Building frontend...${NC}"
cd frontend-react
if [ -f package.json ]; then
    npm install
    npm run build
    echo -e "${GREEN}Frontend built successfully!${NC}"
else
    echo -e "${YELLOW}No package.json found in frontend-react, skipping frontend build${NC}"
fi
cd ..

echo -e "${GREEN}Step 3: Building Docker images...${NC}"
docker-compose -f docker-compose.prod.yml build

echo -e "${GREEN}Step 4: Starting containers...${NC}"
docker-compose -f docker-compose.prod.yml up -d

echo -e "${GREEN}Step 5: Waiting for database to be ready...${NC}"
sleep 10

echo -e "${GREEN}Step 6: Running database migrations...${NC}"
docker exec mathvidya-backend alembic upgrade head || echo -e "${YELLOW}Migration failed or no migrations to run${NC}"

echo -e "${GREEN}Step 7: Restarting Nginx...${NC}"
sudo systemctl restart nginx

echo "=========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "Useful commands:"
echo "  View logs:     docker-compose -f docker-compose.prod.yml logs -f"
echo "  Backend logs:  docker logs -f mathvidya-backend"
echo "  Restart:       docker-compose -f docker-compose.prod.yml restart"
echo "  Status:        docker-compose -f docker-compose.prod.yml ps"
echo ""
