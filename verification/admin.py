from django.contrib import admin
from .models import VerificationRequest, DocumentVerification


@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = ['document', 'requested_by', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['document__title', 'requested_by__username']


@admin.register(DocumentVerification)
class DocumentVerificationAdmin(admin.ModelAdmin):
    list_display = ['document', 'verified_by', 'verification_type', 'status', 'verified_at']
    list_filter = ['verification_type', 'status', 'verified_at']
    search_fields = ['document__title', 'verified_by__username']
