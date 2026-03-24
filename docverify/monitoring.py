# ===================================================================
# Health Check Views
# ===================================================================
# Provides health check endpoints for monitoring.
# Used by load balancers and orchestration systems (K8s, Docker Swarm)
# ===================================================================

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import connection
from django.core.cache import cache
import os


def health_check(request):
    """
    Basic health check endpoint.
    Returns 200 if application is running.
    """
    return JsonResponse({
        'status': 'ok',
        'service': 'docverify',
        'version': '1.0.0'
    })


def detailed_health_check(request):
    """
    Detailed health check with dependency status.
    """
    health_status = {
        'status': 'ok',
        'service': 'docverify',
        'version': '1.0.0',
        'checks': {}
    }

    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['checks']['database'] = f'error: {str(e)}'
        health_status['status'] = 'degraded'

    # Check cache
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health_status['checks']['cache'] = 'ok'
        else:
            health_status['checks'] = 'degraded'
    except Exception as e:
        health_status['checks']['cache'] = f'error: {str(e)}'

    # Check disk space (media directory)
    try:
        media_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'media')
        if os.path.exists(media_path):
            health_status['checks']['storage'] = 'ok'
        else:
            health_status['checks']['storage'] = 'not_configured'
    except Exception as e:
        health_status['checks']['storage'] = f'error: {str(e)}'

    status_code = 200 if health_status['status'] == 'ok' else 503
    return JsonResponse(health_status, status=status_code)


def readiness_check(request):
    """
    Kubernetes readiness probe endpoint.
    """
    return JsonResponse({'ready': True})
