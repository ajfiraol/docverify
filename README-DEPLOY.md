# CI/CD Deployment Guide

This document explains the GitHub Actions workflow for continuous integration and deployment.

## Table of Contents
1. [Overview](#overview)
2. [Workflow Files](#workflow-files)
3. [CI Pipeline](#ci-pipeline)
4. [CD Pipeline](#cd-pipeline)
5. [Setup Instructions](#setup-instructions)
6. [VPS Configuration](#vps-configuration)

---

## Overview

The project uses GitHub Actions for automated:
- **CI (Continuous Integration)**: Testing code on every PR
- **CD (Continuous Deployment)**: Deploying to VPS on push to main

```
GitHub Repository
      │
      ▼
┌─────────────────┐
│  CI Pipeline    │ ◄── Pull Request / Push
│  (ci.yml)       │
│                 │
│  - Lint         │
│  - Test         │
│  - Build Docker │
└─────────────────┘
      │
      ▼ (if main branch)
┌─────────────────┐
│  CD Pipeline    │ ◄── Push to main
│  (cd.yml)       │
│                 │
│  - Build Image  │
│  - Push to GHCR │
│  - Deploy to VPS│
└─────────────────┘
```

---

## Workflow Files

### 1. `.github/workflows/ci.yml`

**Purpose**: Runs tests and quality checks on every PR

**Triggers**:
- Pull requests to main/master
- Push to any branch

**What it does**:
1. **Checkout**: Downloads code
2. **Setup Python**: Configures Python 3.11
3. **Install dependencies**: pip install -r requirements.txt
4. **Linting**: Checks code quality with flake8
5. **Formatting**: Verifies code style with black
6. **Django Check**: Runs `python manage.py check`
7. **Migrations**: Applies database migrations
8. **Tests**: Runs pytest (if any)
9. **Docker Build**: Verifies Docker image builds

**Why this matters**:
- Catches bugs before merging
- Enforces code style
- Ensures Docker image works

### 2. `.github/workflows/cd.yml`

**Purpose**: Deploys to VPS when code is pushed to main

**Triggers**:
- Push to main/master branch
- Manual trigger (workflow_dispatch)

**What it does**:

#### Build & Push Stage:
1. Checkout code
2. Setup Docker Buildx
3. Extract metadata (tags, labels)
4. Login to GHCR (GitHub Container Registry)
5. Build and push Docker image

#### Deploy Stage:
1. SSH into VPS
2. Pull latest docker-compose.yml
3. Pull new Docker image
4. Run migrations
5. Restart services

**Why this matters**:
- Automated deployments
- No manual server access needed
- Consistent deployment process

---

## CI Pipeline

### Step-by-Step Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    CI Pipeline                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. TRIGGER                                                 │
│     └─> Pull Request / Push                                 │
│                                                             │
│  2. CHECKOUT                                                │
│     └─> Download code from GitHub                           │
│                                                             │
│  3. SETUP PYTHON                                            │
│     └─> Python 3.11 with pip cache                          │
│                                                             │
│  4. INSTALL DEPS                                            │
│     └─> pip install requirements.txt                        │
│                                                             │
│  5. LINT                                                    │
│     └─> flake8: Check for errors                            │
│                                                             │
│  6. FORMAT                                                  │
│     └─> black: Check code style                             │
│                                                             │
│  7. DJANGO CHECK                                            │
│     └─> manage.py check: Validate config                    │
│                                                             │
│  8. MIGRATE                                                 │
│     └─> manage.py migrate: Test DB schema                  │
│                                                             │
│  9. BUILD DOCKER                                            │
│     └─> Build image to verify it works                     │
│                                                             │
│  10. COMPLETE                                               │
│      └─> Pass/Fail status on PR                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## CD Pipeline

### Step-by-Step Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    CD Pipeline                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. TRIGGER                                                 │
│     └─> Push to main branch                                 │
│                                                             │
│  2. BUILD & PUSH STAGE                                      │
│                                                             │
│     a) Checkout                                             │
│        └─> Download code                                    │
│                                                             │
│     b) Build Docker                                         │
│        └─> Build image with tags                           │
│           - latest                                          │
│           - sha-{commit}                                    │
│           - branch-{name}                                   │
│                                                             │
│     c) Push to Registry                                     │
│        └─> GitHub Container Registry (GHCR)                │
│                                                             │
│  3. DEPLOY STAGE (on main branch)                          │
│                                                             │
│     a) SSH to VPS                                           │
│        └─> Connect using secrets                           │
│                                                             │
│     b) Pull config                                          │
│        └─> Get latest docker-compose.yml                   │
│                                                             │
│     c) Pull image                                           │
│        └─> docker pull new-image                            │
│                                                             │
│     d) Migrate                                              │
│        └─> Run manage.py migrate                           │
│                                                             │
│     e) Restart                                              │
│        └─> docker-compose up -d                            │
│                                                             │
│  4. COMPLETE                                                │
│     └─> Application deployed!                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Setup Instructions

### 1. Create GitHub Repository

```bash
# Initialize git
git init
git add .
git commit -m "Initial commit"

# Create repository on GitHub, then:
git remote add origin https://github.com/yourusername/docverify.git
git branch -M main
git push -u origin main
```

### 2. Configure GitHub Secrets

Go to: **Repository → Settings → Secrets and variables → Actions**

Add these secrets:

| Secret | Description | Example |
|--------|-------------|---------|
| `VPS_HOST` | Your VPS IP address | `192.168.1.100` |
| `VPS_USER` | SSH username | `root` or `deploy` |
| `VPS_SSH_KEY` | Private SSH key | `-----BEGIN RSA...` |
| `DOCKER_USERNAME` | Docker Hub (optional) | `yourname` |
| `DOCKER_PASSWORD` | Docker Hub password | `yourpassword` |

### 3. Generate SSH Key for VPS

```bash
# On your local machine
ssh-keygen -t rsa -b 4096 -C "github-actions" -f deploy_key

# Copy public key to VPS
ssh-copy-id -i deploy_key.pub user@vps-ip

# Copy private key content to GitHub secret
cat deploy_key
```

---

## VPS Configuration

### 1. Prepare VPS

```bash
# SSH into your VPS
ssh user@vps-ip

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose
apt-get install docker-compose

# Add user to docker group
usermod -aG docker $USER

# Create deployment directory
mkdir -p ~/docverify
cd ~/docverify

# Copy these files:
# - docker-compose.yml
# - .env
# - nginx.conf
```

### 2. Create .env on VPS

```bash
# Copy example
cp .env.example .env

# Edit with your values
nano .env
```

Required variables:
```
DJANGO_SECRET_KEY=your-generated-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com
POSTGRES_DB=docverify
POSTGRES_USER=docverify
POSTGRES_PASSWORD=secure-password-here
```

### 3. Test Docker

```bash
# Test the setup
docker-compose config

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

---

## How the Deployment Works

### GitHub Actions Flow

1. **Developer pushes code**:
   ```bash
   git add .
   git commit -m "Fix bug"
   git push origin main
   ```

2. **CI pipeline runs**:
   - Runs linting, tests, builds Docker
   - If fails: Shows errors on PR
   - If passes: Ready to merge

3. **Merge to main**:
   - CD pipeline triggers automatically
   - Builds Docker image
   - Tags with commit SHA
   - Pushes to GHCR

4. **Deploy to VPS**:
   - GitHub Actions SSHs into VPS
   - Pulls new image
   - Runs migrations
   - Restarts services
   - Application is updated!

---

## Manual Deployment

If GitHub Actions fails, you can deploy manually:

```bash
# SSH into VPS
ssh user@vps-ip

# Navigate to app directory
cd ~/docverify

# Pull latest
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Check status
docker-compose ps
```

---

## Troubleshooting

### CI Fails

1. **Flake8 errors**: Fix linting issues
2. **Black format**: Run `black .` to auto-format
3. **Django check fails**: Fix settings or migrations
4. **Docker build fails**: Check Dockerfile syntax

### CD Fails

1. **SSH connection failed**:
   - Verify VPS secrets are correct
   - Check SSH key has proper permissions

2. **Image pull failed**:
   - Verify GitHub login worked
   - Check image tag is correct

3. **Deployment errors**:
   - Check logs: `docker-compose logs -f`
   - Verify .env file exists

---

## Security Best Practices

1. **Use separate deploy user** (not root)
2. **Rotate secrets regularly**
3. **Enable 2FA on GitHub**
4. **Use private container registry**
5. **Firewall only necessary ports**

---

## Monitoring

After deployment, monitor with:

```bash
# Docker stats
docker stats

# View logs
docker-compose logs -f web

# Check application health
curl http://localhost/health/
```

---

## Next Steps

1. Set up domain and SSL (Let's Encrypt)
2. Configure backups
3. Set up monitoring (Prometheus/Grafana)
4. Configure log rotation
