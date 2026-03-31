"""
Celery configuration for DocVerify.
This file configures Celery with Redis as the message broker.
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docverify.settings')

# Create the Celery application
app = Celery('docverify')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()

# Configure Celery Beat for scheduled tasks
app.conf.beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler'

# Celery result configuration
app.conf.result_expires = 60 * 60 * 24  # 24 hours
app.conf.task_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.result_serializer = 'json'
app.conf.timezone = 'UTC'
app.conf.enable_utc = True

# Task routing (customize as needed)
app.conf.task_routes = {
    'documents.tasks.*': {'queue': 'default'},
    'verification.tasks.*': {'queue': 'default'},
}

# Periodic tasks configuration
app.conf.beat_schedule = {
    # Example: Clean up old verification tokens daily
    'cleanup-expired-tokens': {
        'task': 'accounts.tasks.cleanup_expired_tokens',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    # Example: Send email notifications hourly
    'check-pending-verifications': {
        'task': 'verification.tasks.check_pending_notifications',
        'schedule': crontab(minute=0),  # Hourly
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f'Request: {self.request!r}')
    return 'Task executed successfully'


# Configure Celery to use Redis as broker
app.conf.broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
app.conf.result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')