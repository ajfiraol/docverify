# Monitoring & Observability Guide

This document explains the monitoring tools and endpoints available in DocVerify.

## Table of Contents
1. [Health Check Endpoints](#health-check-endpoints)
2. [Logging](#logging)
3. [Error Tracking](#error-tracking)
4. [Prometheus Metrics](#prometheus-metrics)

---

## Health Check Endpoints

DocVerify provides several health check endpoints for monitoring:

### 1. Basic Health Check
```
GET /health/
```
Returns basic service status.

**Response:**
```json
{
    "status": "ok",
    "service": "docverify",
    "version": "1.0.0"
}
```

### 2. Detailed Health Check
```
GET /health/detailed/
```
Returns detailed status including database, cache, and storage.

**Response:**
```json
{
    "status": "ok",
    "service": "docverify",
    "version": "1.0.0",
    "checks": {
        "database": "ok",
        "cache": "ok",
        "storage": "ok"
    }
}
```

### 3. Readiness Check (Kubernetes)
```
GET /ready/
```
Returns readiness status for Kubernetes probes.

---

## Docker Health Check

The Dockerfile includes a built-in health check:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')" || exit 1
```

---

## Logging

### Log Files

Logs are stored in the `logs/` directory:

| File | Description |
|------|-------------|
| `logs/docverify.log` | General application logs |
| `logs/error.log` | Error and warning logs |

### Log Levels

| Level | Usage |
|-------|-------|
| DEBUG | Detailed debugging info |
| INFO | General information |
| WARNING | Warnings |
| ERROR | Errors |
| CRITICAL | Critical issues |

### Log Format

```
INFO 2024-01-15 10:30:45 views User logged in successfully
ERROR 2024-01-15 10:31:12 models Failed to save document
```

### Viewing Logs in Docker

```bash
# View application logs
docker-compose logs -f web

# View error logs
docker-compose logs -f web | grep ERROR
```

---

## Error Tracking

### Django Error Pages

In DEBUG mode, Django shows detailed error pages. In production:

1. **500 Error Emails**: Configure `ADMINS` in settings
2. **Error Logging**: All errors are logged to `logs/error.log`

### Custom Error Pages

To add custom error pages, create templates:
- `templates/404.html` - Page not found
- `templates/500.html` - Server error
- `templates/403.html` - Forbidden
- `templates/400.html` - Bad request

---

## Prometheus Metrics (Optional)

To add Prometheus metrics:

1. Install prometheus client:
```bash
pip install django-prometheus
```

2. Add to INSTALLED_APPS:
```python
'prometheus_client',
'django_prometheus',
```

3. Update URLs:
```python
path('', include('django_prometheus.urls')),
```

4. Access metrics at:
```
GET /metrics/
```

---

## Monitoring Tools Integration

### Docker Stats

```bash
# Monitor container resources
docker stats docverify_web

# Monitor with logs
docker-compose logs -f --tail=100
```

### Kubernetes Probes

```yaml
livenessProbe:
  httpGet:
    path: /health/
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready/
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Load Balancer Health Checks

Configure your load balancer to check:
- `/health/` - Basic health
- `/health/detailed/` - Detailed health

---

## Recommended Monitoring Stack

For production, consider adding:

| Tool | Purpose |
|------|---------|
| **Prometheus** | Metrics collection |
| **Grafana** | Metrics visualization |
| **Sentry** | Error tracking |
| **ELK Stack** | Log aggregation |
| **Uptime Robot** | External monitoring |

---

## Security Considerations

1. **Don't expose `/metrics/` in production** without authentication
2. **Rate limit** health check endpoints if needed
3. **Rotate logs** regularly to prevent disk space issues
4. **Use HTTPS** for all monitoring endpoints

---

## Troubleshooting

### Check Application Health

```bash
# Local health check
curl http://localhost:8000/health/

# Detailed health
curl http://localhost:8000/health/detailed/
```

### View Recent Errors

```bash
# Tail error log
tail -f logs/error.log

# Search for errors
grep ERROR logs/error.log
```

### Check Container Health

```bash
# Docker health status
docker inspect --format='{{.State.Health.Status}}' docverify_web

# Restart unhealthy container
docker-compose restart web
```
