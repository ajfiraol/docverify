# Docker Setup for DocVerify

This document explains the Docker configuration for the DocVerify Legal Document Verification System.

## Table of Contents
1. [Overview](#overview)
2. [Docker Architecture](#docker-architecture)
3. [Files Explained](#files-explained)
4. [Quick Start](#quick-start)
5. [Production Deployment](#production-deployment)
6. [Development Setup](#development-setup)

---

## Overview

Docker containers provide a consistent, isolated environment for running the application. This setup includes:

- **Django Application**: The main web application
- **PostgreSQL Database**: Production-grade database
- **Nginx**: Reverse proxy and static file server

---

## Docker Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        VPS Server                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Docker Compose Network                 │   │
│  │                                                      │   │
│  │   ┌─────────────┐    ┌─────────────┐               │   │
│  │   │    Nginx    │───▶│    Django   │               │   │
│  │   │   (Port 80) │    │  (Web App)  │               │   │
│  │   └─────────────┘    └──────┬──────┘               │   │
│  │                              │                       │   │
│  │                       ┌──────▼──────┐               │   │
│  │                       │ PostgreSQL  │               │   │
│  │                       │  (Database) │               │   │
│  │                       └─────────────┘               │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Files Explained

### 1. `Dockerfile`

**Purpose**: Creates the Docker image for the Django application

**How it works**:
- Uses Python 3.11 slim base image (minimal size)
- Multi-stage build:
  1. **Base stage**: Sets up Python environment
  2. **Dependencies stage**: Installs Python packages (cached for faster builds)
  3. **Application stage**: Copies code and runs gunicorn

**Key features**:
- Non-root user for security
- Health check included
- Gunicorn as production WSGI server

### 2. `docker-compose.yml`

**Purpose**: Orchestrates multiple containers for production

**Services**:
- `web`: Django application
- `db`: PostgreSQL database
- `nginx`: Reverse proxy

**Environment variables**:
- `POSTGRES_DB`: Database name
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password
- `DJANGO_SECRET_KEY`: Django secret key

### 3. `nginx.conf`

**Purpose**: Nginx web server configuration

**Features**:
- Gzip compression for faster loading
- Security headers (XSS protection, etc.)
- Static file caching (30 days)
- Media file serving
- Reverse proxy to Django app

### 4. `Dockerfile.dev`

**Purpose**: Development environment with live reloading

**Differences from production**:
- Mounts source code for instant updates
- Uses SQLite (or configured database)
- Runserver for auto-reload on code changes

### 5. `.env.example`

**Purpose**: Template for environment variables

**Why important**:
- Contains sensitive configuration
- Never commit actual values to git
- Each environment needs its own .env file

---

## Quick Start

### Prerequisites
- Docker installed
- Docker Compose installed

### Steps

1. **Clone and setup**:
```bash
git clone <repository-url>
cd docverify
```

2. **Create environment file**:
```bash
cp .env.example .env
# Edit .env with your values
```

3. **Start production**:
```bash
docker-compose up -d
```

4. **Access application**:
- Web: http://localhost
- Admin: http://localhost/admin

---

## Production Deployment

### Using Docker Compose (VPS)

1. **Transfer files to VPS**:
```bash
scp -r . user@vps:/path/to/docverify
```

2. **Configure environment**:
```bash
ssh user@vps
cd /path/to/docverify
cp .env.example .env
nano .env  # Edit values
```

3. **Start services**:
```bash
docker-compose up -d
```

4. **Run migrations**:
```bash
docker-compose exec web python manage.py migrate
```

### Using GitHub Actions (Recommended)

See [README-DEPLOY.md](./README-DEPLOY.md) for automated deployment.

---

## Development Setup

### Running locally with Docker

```bash
# Using development compose
docker-compose -f docker-compose.dev.yml up --build

# With hot reload
docker-compose -f docker-compose.dev.yml up
```

### Without Docker

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver
```

---

## Common Commands

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart a service
docker-compose restart web

# Run commands in container
docker-compose exec web python manage.py createsuperuser

# Rebuild after code changes (production)
docker-compose build --no-cache
docker-compose up -d

# Database backup
docker-compose exec db pg_dump -U docverify docverify > backup.sql
```

---

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs web

# Common issues:
# - Database not ready: Wait or check health
# - Port already in use: Change port in docker-compose.yml
# - Missing .env: Create from .env.example
```

### Database connection errors
```bash
# Check database is running
docker-compose ps db

# Check environment variables
docker-compose exec web env | grep DATABASE
```

### Permission issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER .
```

---

## Security Considerations

1. **Never commit `.env`** - It's in `.gitignore`
2. **Use strong passwords** - Generate with `python -c "import secrets; print(secrets.token_urlsafe(50))"`
3. **Keep images updated** - Regularly pull latest base images
4. **Use HTTPS** - Add SSL/TLS certificate in production
5. **Restrict database access** - Use firewall rules

---

## Next Steps

- [README-DEPLOY.md](./README-DEPLOY.md) - GitHub Actions CI/CD setup
- [README.md](./README.md) - General project documentation
