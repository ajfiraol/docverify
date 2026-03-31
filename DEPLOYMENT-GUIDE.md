# DocVerify Production Deployment Guide

Complete deployment instructions for DocVerify (Django) application on a VPS with Redis, Celery, Nginx, and Cloudflare integration for domain `eventaxiss.com`.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Server Preparation](#server-preparation)
4. [SSH Key & VPS User Setup](#ssh-key--vps-user-setup) - Create deploy user & SSH key
5. [Cloudflare Configuration](#cloudflare-configuration)
6. [GitHub Actions CI/CD Setup](#github-actions-cicd-setup) - Automated deployment
7. [Docker Deployment](#docker-deployment) - Manual fallback
8. [Project Configuration](#project-configuration)
9. [Test Environment](#test-environment)
10. [Service Management](#service-management)
11. [Health Checks](#health-checks)
12. [Cleanup & Disconnection](#cleanup--disconnection) - Complete teardown
13. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLOUDFLARE CDN                                  │
│                    https://eventaxiss.com                               │
│           (SSL Termination, DDoS Protection, Caching)                  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼ HTTPS (443) - Cloudflare Proxied
┌─────────────────────────────────────────────────────────────────────────┐
│                              NGINX                                       │
│                    Reverse Proxy + SSL Termination                       │
│                    Ports: 80, 443                                       │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │   Web    │ │ Celery   │ │ Celery   │
              │ (Django) │ │ Worker  │ │  Beat   │
              │  :8000  │ │         │ │         │
              └──────────┘ └──────────┘ └──────────┘
                    │            │            │
                    └────────────┼────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
              ┌──────────┐              ┌──────────┐
              │  Redis   │   ◄────────►│PostgreSQL│
              │ Cache    │   Broker    │   DB     │
              │ :6379   │              │  :5432  │
              └──────────┘              └──────────┘
```

### Services

| Service | Image | Purpose | Port |
|---------|-------|---------|------|
| web | Custom (Django + Gunicorn) | Django application | 8000 |
| celery_worker | Custom (Celery) | Process async tasks | - |
| celery_beat | Custom (Celery Beat) | Schedule periodic tasks | - |
| redis | redis:7-alpine | Cache + Message broker | 6379 |
| db | postgres:15-alpine | PostgreSQL database | 5432 |
| nginx | nginx:alpine | Reverse proxy + SSL | 80, 443 |

---

## Prerequisites

### Server Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 1 vCPU | 2 vCPU |
| RAM | 1 GB | 2 GB |
| Storage | 20 GB | 40 GB |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |

### Required Accounts

- [ ] **VPS Provider**: Server access (DigitalOcean, Linode, AWS, etc.)
- [ ] **Cloudflare Account**: For DNS management (free tier works)
- [ ] **Optional**: Sentry.io for error tracking (free tier available)

---

## Step 1: Server Preparation (VPS Setup)

### 1.1 Connect to VPS (Initial Setup as Root)

First, connect as root to set up the server:

```bash
ssh root@YOUR_VPS_IP
```

### 1.2 Initial System Setup

```bash
# Update package lists
apt update

# Upgrade all packages
apt upgrade -y

# Install essential packages
apt install -y curl git wget software-properties-common apt-transport-https ca-certificates gnupg lsb-release ufw
```

### 1.3 Install Docker

```bash
# Download and install Docker
curl -fsSL https://get.docker.com | sh

# Add current user to docker group
usermod -aG docker $USER

# Enable Docker to start on boot
systemctl enable docker

# Start Docker
systemctl start docker

# Verify installation
docker --version
docker-compose --version
```

### 1.4 Configure Firewall

```bash
# Set default policies
ufw default allow outgoing
ufw default deny incoming

# Allow SSH (always keep this open)
ufw allow 22/tcp comment 'SSH'

# Allow HTTP
ufw allow 80/tcp comment 'HTTP'

# Allow HTTPS
ufw allow 443/tcp comment 'HTTPS'

# Enable firewall
ufw --force enable

# Check status
ufw status
```

### 1.5 Create Deployment Directory

```bash
# Create deployment directory
mkdir -p /opt/docverify

# Set ownership (replace 'ubuntu' with your username)
chown -R ubuntu:ubuntu /opt/docverify

# Navigate to deployment directory
cd /opt/docverify
```

---

## Step 2: SSH Key & VPS User Setup

### 2.1 Generate SSH Key Pair (On Your Local Machine)

```bash
# Generate SSH key (Ed25519 recommended)
ssh-keygen -t ed25519 -C "your_email@example.com"
```

**Default location**: `~/.ssh/id_ed25519`

### 2.2 Copy Public Key to VPS

**Option A: Using ssh-copy-id**

```bash
# Copy public key to VPS
ssh-copy-id -i ~/.ssh/id_ed25519.pub root@YOUR_VPS_IP
```

**Option B: Manual Copy**

On VPS:
```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "ssh-ed25519 AAAA... your-key" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### 2.3 Create VPS Deployment User

Instead of using root directly, create a separate user:

```bash
# Create deploy user
adduser deploy

# Add to docker group
usermod -aG docker deploy

# Add to sudo group (optional)
usermod -aG sudo deploy
```

### 2.4 Add SSH Key for Deploy User

**Option A: Copy from root**

```bash
mkdir /home/deploy/.ssh
cp /root/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys
```

**Option B: Generate new key**

On local machine:
```bash
ssh-keygen -t ed25519 -C "deploy@eventaxiss.com" -f ~/.ssh/id_ed25519_deploy
ssh-copy-id -i ~/.ssh/id_ed25519_deploy.pub deploy@VPS_IP
```

### 2.5 Connect as Deploy User

```bash
ssh -i ~/.ssh/id_ed25519_deploy deploy@YOUR_VPS_IP
```

### 2.6 Disable Root Login (After Testing)

```bash
sudo nano /etc/ssh/sshd_config
```

Change:
```
PermitRootLogin no
PasswordAuthentication no
PubKeyAuthentication yes
```

```bash
sudo systemctl restart sshd
```

### 2.7 Remove VPN User (Cleanup)

```bash
userdel -r deploy
rm ~/.ssh/id_ed25519_deploy*
```

---

## Step 3: Cloudflare Configuration

### 2.1 Configure DNS Records

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Select your domain: `eventaxiss.com`
3. Go to **DNS** > **Add record**

| Type | Name | Content | Proxy Status | TTL |
|------|------|---------|--------------|-----|
| A | @ | YOUR_VPS_IP | Proxied | Auto |
| A | www | YOUR_VPS_IP | Proxied | Auto |

**Note**: Replace `YOUR_VPS_IP` with your actual VPS IP address.

### 2.2 Get Origin SSL Certificate

1. Go to **SSL/TLS** > **Origin Server**
2. Click **Create Certificate**
3. Configure:
   - **Hostname**: `eventaxiss.com` and `*.eventaxiss.com`
   - **Validity**: 15 years
4. Click **Create**
5. Copy the **Origin Certificate** and **Private Key**

### 2.3 Save SSL Certificates

On your VPS:

```bash
# Create SSL directory
mkdir -p /opt/docverify/nginx/ssl

# Save certificate (paste when prompted, end with Ctrl+D)
cat > /opt/docverify/nginx/ssl/cert.pem << 'EOF'
-----BEGIN CERTIFICATE-----
your-certificate-here
-----END CERTIFICATE-----
EOF

# Save private key
cat > /opt/docverify/nginx/ssl/key.pem << 'EOF'
-----BEGIN PRIVATE KEY-----
your-private-key-here
-----END PRIVATE KEY-----
EOF

# Set proper permissions
chmod 600 /opt/docverify/nginx/ssl/key.pem
```

### 2.4 Configure SSL Mode

In Cloudflare dashboard:
- Go to **SSL/TLS** > **Overview**
- Set **SSL/TLS Encryption Mode** to `Full` or `Full (Strict)`

### 2.5 Create Cloudflare API Token

1. Go to **Profile** > **API Tokens**
2. Click **Create Custom Token**
3. Configure:
   - **Token name**: `docverify-production`
   - **Permissions**:
     - `Zone:DNS:Edit`
     - `Zone:Zone:Read`
   - **Zone Resources**: Include `eventaxiss.com`
4. Click **Create Token**- cfut_gv8dqd1OTsFGc1nYhoMuK0gE2pQyrgNRnPrUtM9i43b998d9
5. Copy the token (shown only once)

---

## Step 7: Test Environment Setup

### 7.1 Create Test Subdomain (Temporary)

For testing purposes, use a temporary subdomain that can be easily removed:

| Type | Name | Content | Proxy Status |
|------|------|---------|------------|
| A | test | YOUR_VPS_IP | DNS Only (Gray/cloud) |

**Important**: Use "DNS Only" (gray cloud) status - this means traffic goes directly to your VPS without Cloudflare proxy. This makes it easier to disconnect later.

### 7.2 Test App User (For Testing the Deployed Application)

Create a test user account within the Django application to test the deployed system:

```bash
# Enter the web container
docker exec -it docverify_web bash

# Create test user
python manage.py createsuperuser
# Username: testuser
# Email: test@example.com
# Password: TestPass123!
# (or use non-superuser via Django admin)
```

### 7.3 Non-Superuser Test Account

```bash
# Create test user via Django shell
docker exec -it docverify_web python manage.py shell
```

```python
from django.contrib.auth import get_user_model
User = get_user_model()

# Create regular user (not staff/admin)
user = User.objects.create_user(
    username='testuser',
    email='test@example.com',
    password='TestPass123!'
)

# Optional: Make staff for admin access
user.is_staff = True
user.save()

print(f"User created: {user.username}")
exit()
```

### 7.4 Alternative: Test-Only Environment Variable

In `.env` file, add a flag to limit access:

```
# Restrict to specific IP addresses (optional)
ALLOWED_TEST_IPS=your-local-ip-address
```

Or create a test-only settings file:

```python
# docverify/test_settings.py
from .settings import *

DEBUG = True
ALLOWED_HOSTS = ['test.eventaxiss.com', 'localhost', '127.0.0.1']
```

---

## Step 6: Project Configuration

### 3.1 Copy Project Files to VPS

**Option A: Using Git**

```bash
cd /opt/docverify
git clone https://your-repo-url.git .
```

**Option B: Using SCP**

```bash
# From your local machine
scp -r ./docverify/* root@YOUR_VPS_IP:/opt/docverify/
```

### 3.2 Update Dockerfile

Ensure the Dockerfile includes the production requirements:

```dockerfile
# In Dockerfile, ensure this line exists:
COPY requirements-production.txt requirements.txt
```

### 3.3 Create .env File

```bash
cd /opt/docverify
cp .env.example .env
nano .env
```

Edit the `.env` file with your values:

```bash
# ===================================================================
# .env - Production Environment Variables
# ===================================================================

# -----------------------------------------------------------------------------
# Django Settings
# -----------------------------------------------------------------------------
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(50))"
DJANGO_SECRET_KEY=your-super-secret-key-min-50-chars-change-in-production

# IMPORTANT: Set to False in production
DJANGO_DEBUG=False

# Your domain
DJANGO_ALLOWED_HOSTS=eventaxiss.com,www.eventaxiss.com

# -----------------------------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------------------------
POSTGRES_DB=docverify
POSTGRES_USER=docverify
POSTGRES_PASSWORD=change-this-to-strong-password

# -----------------------------------------------------------------------------
# Redis & Celery Configuration
# -----------------------------------------------------------------------------
# Redis password (generate with: openssl rand -hex 32)
REDIS_PASSWORD=change-this-to-strong-redis-password

# Celery broker and result backend
CELERY_BROKER_URL=redis://:change-this-to-strong-redis-password@redis:6379/0
CELERY_RESULT_BACKEND=redis://:change-this-to-strong-redis-password@redis:6379/1

# -----------------------------------------------------------------------------
# Nginx Configuration
# -----------------------------------------------------------------------------
NGINX_PORT=80
NGINX_SSL_PORT=443

# -----------------------------------------------------------------------------
# Cloudflare Configuration
# -----------------------------------------------------------------------------
CLOUDFLARE_API_TOKEN=your-cloudflare-api-token
CLOUDFLARE_ZONE_ID=your-zone-id

# -----------------------------------------------------------------------------
# Monitoring (Optional)
# -----------------------------------------------------------------------------
# Get free DSN at https://sentry.io
SENTRY_DSN=
```

### 3.4 Generate Secret Keys

```bash
# Generate Django secret key
python -c "import secrets; print(secrets.token_urlsafe(50))"

# Generate Redis password
openssl rand -hex 32
```

---

## Step 4: GitHub Actions CI/CD Setup

Your project already has CI/CD workflows configured:
- **ci.yml** - Runs tests and linting on PR/push
- **cd.yml** - Builds and deploys to VPS on main branch push

### 4.1 Workflow Overview

```
Push to main → CI (Test & Build) → CD (Deploy to VPS)
```

**CI Workflow (ci.yml):**
- Runs on every push/PR to `main`
- Tests with PostgreSQL
- Lints with flake8
- Checks code with Black
- Builds Docker image

**CD Workflow (cd.yml):**
- Runs after CI passes (push to `main`)
- Builds Docker image to GHCR + Docker Hub
- Deploys to VPS via SSH

### 4.2 Generate SSH Key for GitHub Actions

On your **local machine**:

```bash
# Generate SSH key for GitHub Actions
ssh-keygen -t ed25519 -C "github-actions@eventaxiss.com" -f ~/.ssh/id_ed25519_github

# Display private key (copy this for GitHub secret)
cat ~/.ssh/id_ed25519_github
```

### 4.3 Add SSH Key to VPS

On **VPS** (as root):

```bash
# Add public key to authorized_keys
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "ssh-ed25519 AAAA... your-key" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

Or from local machine:

```bash
ssh-copy-id -i ~/.ssh/id_ed25519_github deploy@VPS_IP
```

### 4.4 Configure GitHub Secrets

Go to **GitHub Repo > Settings > Secrets and variables > Actions**

Add these secrets:

| Secret Name | Value | Required |
|------------|-------|----------|
| `VPS_HOST` | Your VPS IP address | Yes |
| `VPS_USER` | `deploy` (or root) | Yes |
| `VPS_SSH_KEY` | Private SSH key content | Yes |
| `DOCKER_USERNAME` | Docker Hub username | Optional |
| `DOCKER_PASSWORD` | Docker Hub password | Optional |

### 4.5 Configure VPS for Deployment

On **VPS**, prepare the deployment directory:

```bash
# As root, create deploy user
adduser deploy
usermod -aG docker deploy

# Create deployment directory
mkdir -p /opt/docverify
chown -R deploy:deploy /opt/docverify

# Switch to deploy user
su - deploy
cd /opt/docverify
```

### 4.6 Trigger Deployment

**Automatic (on push to main):**

```bash
git add .
git commit -m "Deploy update"
git push origin main
```

**Manual:**
1. Go to GitHub > **Actions** > **CD - Deploy to VPS**
2. Click **Run workflow**

### 4.7 Monitor Deployment

1. Go to GitHub > **Actions** tab
2. Click on the running workflow
3. View real-time logs

---

## Step 5: Docker Deployment (Manual Fallback)

*(Only if GitHub Actions is not available)*

### 4.1 Build Docker Images

```bash
cd /opt/docverify

# Build all services
docker-compose -f docker-compose.prod.yml build
```

### 4.2 Start Services

```bash
# Start all services in detached mode
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

Expected output:

```
NAME                IMAGE               STATUS          PORTS
docverify_celery_beat    docverify_celery_beat    Up
docverify_celery_worker  docverify_celery_worker  Up
docverify_db            postgres:15-alpine   Up (healthy)   5432:5432
docverify_nginx          nginx:alpine         Up             0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
docverify_redis         redis:7-alpine      Up (healthy)   6379:6379
docverify_web           docverify_web        Up (healthy)   8000:8000
```

### 4.3 Run Database Migrations

```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### 4.4 Collect Static Files

```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### 4.5 Create Superuser

```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

Follow the prompts to create an admin user.

### 4.6 Verify Static Files

```bash
# Check static files were collected
docker-compose -f docker-compose.prod.yml exec web ls -la /app/staticfiles/
```

---

## Step 8: Service Management

### 5.1 View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f web
docker-compose -f docker-compose.prod.yml logs -f celery_worker
docker-compose -f docker-compose.prod.yml logs -f nginx

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100
```

### 5.2 Restart Services

```bash
# Restart all services
docker-compose -f docker-compose.prod.yml restart

# Restart specific service
docker-compose -f docker-compose.prod.yml restart web
```

### 5.3 Stop Services

```bash
# Stop all services
docker-compose -f docker-compose.prod.yml down

# Stop and remove volumes (WARNING: deletes database data)
docker-compose -f docker-compose.prod.yml down -v
```

### 5.4 Scale Services

```bash
# Scale Celery workers
docker-compose -f docker-compose.prod.yml up -d --scale celery_worker=2

# Scale Celery workers (Note: may cause issues with task scheduling)
```

### 5.5 Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build --force-recreate

# Run migrations if needed
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

---

## Step 9: Health Checks

### 6.1 Check Container Status

```bash
docker ps
```

All containers should show status "Up" or "Up (healthy)".

### 6.2 Test Application Endpoints

```bash
# Test via localhost
curl http://localhost:8000/admin/
curl http://localhost:8000/health/

# Test via domain (after DNS propagates)
curl https://eventaxiss.com/health/
```

### 6.3 Test Database Connection

```bash
docker exec docverify_db psql -U docverify -c "SELECT version();"
```

### 6.4 Test Redis Connection

```bash
docker exec docverify_redis redis-cli -a your-redis-password ping
```

Expected: `PONG`

### 6.5 Test Celery

```bash
# Check active tasks
docker exec docverify_celery_worker celery -A docverify inspect active

# Check registered tasks
docker exec docverify_celery_worker celery -A docverify inspect registered

# Check stats
docker exec docverify_celery_worker celery -A docverify inspect stats
```

### 6.6 Test Nginx

```bash
# Test nginx configuration
docker exec docverify_nginx nginx -t

# Check nginx logs
docker logs docverify_nginx
```

---

## Step 10: Cleanup & Disconnection

### 8.1 Stop All Docker Services

```bash
cd /opt/docverify

# Stop all containers
docker-compose -f docker-compose.prod.yml down

# Stop and remove all volumes (database, redis data)
docker-compose -f docker-compose.prod.yml down -v

# Remove all images
docker-compose -f docker-compose.prod.yml down --rmi all

# Remove all containers, volumes, images
docker-compose -f docker-compose.prod.yml down -v --rmi all
```

### 8.2 Delete Test User

```bash
# Delete test user from database
docker exec -it docverify_web python manage.py shell
```

```python
from django.contrib.auth import get_user_model
User = get_user_model()

# Delete test user
user = User.objects.get(username='testuser')
user.delete()

print("Test user deleted")
exit()
```

### 8.3 Remove from Cloudflare DNS

1. Go to Cloudflare Dashboard > DNS
2. Find the A record for your test subdomain (e.g., `test.eventaxiss.com`)
3. Click the delete icon to remove

Or using Cloudflare API:

```bash
# Delete DNS record via API
curl -X DELETE "https://api.cloudflare.com/client/v4/zones/YOUR_ZONE_ID/dns_records/YOUR_RECORD_ID" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json"
```

### 8.4 Disable Domain in Cloudflare

If you want to completely disconnect from Cloudflare temporarily:

1. Go to Cloudflare Dashboard > DNS
2. Click on the A record proxy status (turns it gray - "DNS Only")
3. Or delete all DNS records

### 8.5 Full Server Cleanup

```bash
# On VPS, remove all deployment files
rm -rf /opt/docverify

# Remove Docker
apt remove docker.io docker-ce docker-ce-cli containerd.io

# Remove Docker Compose
rm /usr/local/bin/docker-compose

# Disable firewall rules
ufw disable

# Remove SSH key (optional, if you added it)
rm ~/.ssh/authorized_keys
```

### 8.6 Complete Teardown Checklist

- [ ] Stop Docker containers: `docker-compose down`
- [ ] Remove volumes: `docker-compose down -v`
- [ ] Delete test user from database
- [ ] Remove DNS records from Cloudflare
- [ ] Turn off proxy (gray out DNS)
- [ ] Delete SSL certificates (optional)
- [ ] Remove deployment directory: `rm -rf /opt/docverify`
- [ ] Remove SSH key from server (if added specifically for this project)
- [ ] Re-enable password auth (if disabled): `/etc/ssh/sshd_config`
- [ ] Consider destroying VPS instance entirely if not needed

### 8.7 Emergency Disconnection Script

Create a script for quick disconnection:

```bash
#!/bin/bash
# /opt/docverify/emergency_teardown.sh

echo "Starting emergency teardown..."

# 1. Stop and remove all containers
echo "[1/5] Stopping containers..."
cd /opt/docverify
docker-compose -f docker-compose.prod.yml down -v

# 2. Delete test user
echo "[2/5] Deleting test user..."
docker exec docverify_web python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
try:
    user = User.objects.get(username='testuser')
    user.delete()
    print("Test user deleted")
except:
    pass
EOF

# 3. Note: DNS cleanup requires manual action or API token
echo "[3/5] To remove DNS records:"
echo "   1. Go to https://dash.cloudflare.com"
echo "   2. Select eventaxiss.com"
echo "   3. Go to DNS and delete records"

# 4. Cleanup files
echo "[4/5] Cleaning up files..."
rm -rf /opt/docverify

# 5. Display final instructions
echo "[5/5] Teardown complete!"
echo ""
echo "Next steps:"
echo "1. Manually delete DNS records in Cloudflare"
echo "2. Delete VPS if no longer needed"
echo "3. Remove SSH key if added"

chmod +x /opt/docverify/emergency_teardown.sh
```

---

## Step 11: Troubleshooting

### 7.1 Container Won't Start

```bash
# Check logs for errors
docker-compose -f docker-compose.prod.yml logs

# Common fixes:
# - Check .env file exists
# - Check port 80/443 not in use
# - Check SSL certificates exist
```

### 7.2 Database Connection Error

```bash
# Check database is running
docker ps | grep docverify_db

# Check database logs
docker logs docverify_db

# Test connection from web container
docker exec -it docverify_web python -c "import psycopg2; print('OK')"
```

### 7.3 Redis Connection Error

```bash
# Check Redis is running
docker ps | grep docverify_redis

# Check Redis logs
docker logs docverify_redis

# Test Redis connection
docker exec docverify_redis redis-cli -a your-password ping
```

### 7.4 Celery Tasks Not Running

```bash
# Check Celery worker logs
docker logs docverify_celery_worker

# Check Redis is accessible from worker
docker exec docverify_celery_worker python -c "import redis; r = redis.from_url('redis://:password@redis:6379/0'); print(r.ping())"
```

### 7.5 SSL Certificate Issues

```bash
# Verify certificates exist
ls -la /opt/docverify/nginx/ssl/

# Test nginx configuration
docker exec docverify_nginx nginx -t

# Check nginx error logs
docker logs docverify_nginx --tail=50
```

### 7.6 Permission Issues

```bash
# Fix docker group permissions
sudo usermod -aG docker $USER
newgrp docker

# Fix file permissions
sudo chown -R $USER:$USER /opt/docverify
```

### 7.7 Port Already in Use

```bash
# Find what's using the port
sudo lsof -i :80
sudo lsof -i :443

# Stop the conflicting service
sudo systemctl stop apache2  # or nginx
```

---

## Step 12: Security Hardening

### 8.1 Update Docker Daemon

```bash
sudo nano /etc/docker/daemon.json
```

Add:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "live-restore": true
}
```

Restart Docker:

```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
```

### 8.2 Enable Automatic Security Updates

```bash
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 8.3 Fail2ban Installation (Optional)

```bash
sudo apt install fail2ban

# Configure for SSH
sudo nano /etc/fail2ban/jail.local
```

Add:

```ini
[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
```

```bash
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## Step 13: Monitoring & Maintenance

### 9.1 Log Rotation

Create `/etc/logrotate.d/docker-compose`:

```
/opt/docverify/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

### 9.2 Backup Database

Create backup script:

```bash
#!/bin/bash
# /opt/docverify/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
docker exec docverify_db pg_dump -U docverify docverify > /opt/docverify/backups/db_$DATE.sql

# Keep only last 7 backups
find /opt/docverify/backups -type f -mtime +7 -delete
```

Make executable and add to crontab:

```bash
chmod +x /opt/docverify/backup.sh
crontab -e
```

Add line:

```
0 2 * * * /opt/docverify/backup.sh >> /var/log/backup.log 2>&1
```

### 9.3 Health Monitoring Script

```bash
#!/bin/bash
# /opt/docverify/healthcheck.sh

# Check all services
docker-compose -f /opt/docverify/docker-compose.prod.yml ps

# Send notification on failure
if [ $? -ne 0 ]; then
    echo "Service down!" | send-email -to "admin@eventaxiss.com"
fi
```

---

## Quick Reference

### Essential Commands

```bash
# Start deployment
cd /opt/docverify
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop deployment
docker-compose -f docker-compose.prod.yml down

# Restart after update
git pull
docker-compose -f docker-compose.prod.yml up -d --build --force-recreate
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### URLs

| Service | URL |
|---------|-----|
| Application | https://eventaxiss.com |
| Admin | https://eventaxiss.com/admin |
| Health Check | https://eventaxiss.com/health |

### Ports

| Port | Service |
|------|---------|
| 22 | SSH |
| 80 | HTTP |
| 443 | HTTPS |

---

## Support

For issues or questions:
1. Check logs: `docker-compose -f docker-compose.prod.yml logs`
2. Check container status: `docker ps`
3. Verify .env configuration
4. Consult this guide's troubleshooting section