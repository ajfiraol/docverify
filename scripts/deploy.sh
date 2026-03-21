#!/bin/bash
# ===================================================================
# deploy.sh - DocVerify Deployment Script
# ===================================================================
# This script automates the deployment process on a VPS.
# It pulls the latest Docker images and restarts services.
#
# Usage:
#   ./scripts/deploy.sh
#
# Prerequisites:
#   - Docker and Docker Compose installed
#   - .env file configured
# ===================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="${IMAGE_NAME:-docverify/docverify:latest}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
APP_DIR="${APP_DIR:-$HOME/docverify}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  DocVerify Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"

# -----------------------------------------------------------------------------
# Check if Docker is running
# -----------------------------------------------------------------------------
echo -e "\n${YELLOW}[1/6] Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi
echo -e "${GREEN}Docker is running${NC}"

# -----------------------------------------------------------------------------
# Check if .env exists
# -----------------------------------------------------------------------------
echo -e "\n${YELLOW}[2/6] Checking configuration...${NC}"
if [ ! -f "$APP_DIR/.env" ]; then
    echo -e "${RED}Error: .env file not found at $APP_DIR/.env${NC}"
    echo -e "${YELLOW}Please create .env file from .env.example${NC}"
    exit 1
fi
echo -e "${GREEN}Configuration found${NC}"

# -----------------------------------------------------------------------------
# Pull latest image
# -----------------------------------------------------------------------------
echo -e "\n${YELLOW}[3/6] Pulling latest image...${NC}"
docker pull "$IMAGE_NAME" || echo -e "${YELLOW}Warning: Could not pull image, using local${NC}"

# -----------------------------------------------------------------------------
# Run database migrations
# -----------------------------------------------------------------------------
echo -e "\n${YELLOW}[4/6] Running database migrations...${NC}"
cd "$APP_DIR"
docker compose run --rm web python manage.py migrate --noinput
echo -e "${GREEN}Migrations completed${NC}"

# -----------------------------------------------------------------------------
# Collect static files
# -----------------------------------------------------------------------------
echo -e "\n${YELLOW}[5/6] Collecting static files...${NC}"
docker compose run --rm web python manage.py collectstatic --noinput --clear
echo -e "${GREEN}Static files collected${NC}"

# -----------------------------------------------------------------------------
# Restart services
# -----------------------------------------------------------------------------
echo -e "\n${YELLOW}[6/6] Restarting services...${NC}"
docker compose down
docker compose up -d --build
echo -e "${GREEN}Services restarted${NC}"

# -----------------------------------------------------------------------------
# Show status
# -----------------------------------------------------------------------------
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
docker compose ps

echo -e "\n${GREEN}Application deployed successfully!${NC}"
echo -e "View logs: ${YELLOW}docker compose logs -f${NC}"
