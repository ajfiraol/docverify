from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'uploaded_by', 'status', 'verification_status', 'created_at']
    list_filter = ['document_type', 'status', 'verification_status', 'created_at']
    search_fields = ['title', 'uploaded_by__username']
    readonly_fields = ['created_at', 'updated_at']
