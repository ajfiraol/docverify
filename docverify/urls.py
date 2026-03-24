"""
URL configuration for docverify project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from . import monitoring

urlpatterns = [
    # Health check endpoints
    path('health/', monitoring.health_check, name='health_check'),
    path('health/detailed/', monitoring.detailed_health_check, name='detailed_health_check'),
    path('ready/', monitoring.readiness_check, name='readiness_check'),

    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('documents/', include('documents.urls')),
    path('verification/', include('verification.urls')),
    path('institutions/', include('institutions.urls')),
    path('', RedirectView.as_view(url='documents/', permanent=False), name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
