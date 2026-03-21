# DocVerify - Legal Document Verification System

A Django-based system for uploading, managing, and verifying legal documents with role-based access control.

## Features

- **Multi-role Authentication**: Regular Users, Institutions, Companies
- **Document Management**: Upload, view, track documents
- **Verification System**: Institution verification with auto-generated verification IDs
- **Time-based Verification IDs**: 12-character IDs that refresh every 5 minutes
- **Public Verification**: Anyone can verify document authenticity via ID

## Tech Stack

- **Backend**: Django 4.x / Python 3.11
- **Database**: PostgreSQL (production) / SQLite (development)
- **Frontend**: Bootstrap 5
- **Containerization**: Docker & Docker Compose
- **CI/CD**: GitHub Actions

---

## Quick Start

### Local Development

```bash
# Clone the repository
git clone <repository-url>
cd docverify

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start server
python manage.py runserver
```

Access at: http://localhost:8000

### With Docker

```bash
# Development
docker-compose -f docker-compose.dev.yml up --build

# Production
docker-compose up -d
```

---

## User Roles

| Role | Description | Features |
|------|-------------|----------|
| **Regular User** | Document owners | Upload documents, view verification IDs |
| **Institution** | Government/Regulatory | Verify documents, view pending requests |
| **Company** | Third parties (employers, agencies) | Verify document authenticity via ID |

---

## Verification ID System

### How It Works

1. User uploads a document
2. Institution verifies the document (approves/rejects)
3. On approval, a 12-character verification ID is generated (e.g., `A1B2C3D4E5F6`)
4. User can share this ID with companies
5. Companies enter the ID at `/verification/verify-by-id/`
6. The system confirms document authenticity

### Features
- **Auto-refresh**: ID changes every 5 minutes
- **Manual refresh**: Users can request new ID anytime
- **Public access**: Verification doesn't require login

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/accounts/register/` | User registration |
| `/accounts/login/` | User login |
| `/documents/` | User's documents |
| `/documents/upload/` | Upload document |
| `/verification/verify-by-id/` | Public verification |
| `/verification/pending/` | Institution pending verifications |

---

## Docker Setup

See [README-DOCKER.md](./README-DOCKER.md) for detailed Docker configuration.

### Production Deployment

```bash
# Build and start
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

---

## CI/CD Pipeline

See [README-DEPLOY.md](./README-DEPLOY.md) for GitHub Actions setup.

### Workflows

1. **CI (ci.yml)**: Runs on every PR
   - Linting (flake8)
   - Code formatting (black)
   - Django checks
   - Docker build

2. **CD (cd.yml)**: Runs on push to main
   - Builds Docker image
   - Pushes to container registry
   - Deploys to VPS

---

## Project Structure

```
docverify/
├── docverify/           # Django project settings
├── accounts/            # User authentication
├── documents/           # Document management
├── verification/        # Verification workflow
├── templates/           # HTML templates
├── static/              # Static files
├── scripts/             # Deployment scripts
├── Dockerfile           # Production Docker image
├── Dockerfile.dev       # Development Docker image
├── docker-compose.yml   # Production compose
├── docker-compose.dev.yml
├── nginx.conf           # Nginx configuration
├── requirements.txt     # Python dependencies
└── .env.example         # Environment template
```

---

## Environment Variables

Create `.env` from `.env.example`:

```
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,example.com
POSTGRES_DB=docverify
POSTGRES_USER=docverify
POSTGRES_PASSWORD=secure-password
```

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

---

## License

MIT License

---

## Support

For issues and questions, please open a GitHub issue.
