#!/bin/bash
# ===================================================================
# deploy.sh - DocVerify Production Deployment Script
# ===================================================================
# Run on VPS: bash deploy.sh
# ===================================================================

set -e  # Exit on error

echo "=============================================="
echo "DocVerify Production Deployment"
echo "=============================================="

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}[+]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# ===================================================================
# Check if running as root
# ===================================================================
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root - this script should be run as a regular user with sudo access"
fi

# ===================================================================
# Step 1: Update System
# ===================================================================
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# ===================================================================
# Step 2: Install Docker (if not installed)
# ===================================================================
if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
fi

# ===================================================================
# Step 3: Install Docker Compose (if not installed)
# ===================================================================
if ! command -v docker-compose &> /dev/null; then
    print_status "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# ===================================================================
# Step 4: Configure Firewall
# ===================================================================
print_status "Configuring firewall..."
sudo ufw default allow outgoing
sudo ufw default deny incoming
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw --force enable

# ===================================================================
# Step 5: Create Deployment Directory
# ===================================================================
DEPLOY_DIR="/opt/docverify"
print_status "Creating deployment directory at $DEPLOY_DIR..."

if [ ! -d "$DEPLOY_DIR" ]; then
    sudo mkdir -p $DEPLOY_DIR
fi

# ===================================================================
# Step 6: Copy Configuration Files
# ===================================================================
print_status "Copying configuration files..."

# Copy SSL certificates (you need to provide these)
# sudo cp -r nginx/ssl $DEPLOY_DIR/

# Make scripts executable
chmod +x deploy.sh

print_status "Deployment preparation complete!"
echo ""
echo "Next steps:"
echo "1. Copy your project files to $DEPLOY_DIR"
echo "2. Create .env file from .env.example"
echo "3. Run: docker-compose -f docker-compose.prod.yml up -d"
echo "4. Run migrations: docker-compose -f docker-compose.prod.yml exec web python manage.py migrate"
echo "5. Collect static: docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput"