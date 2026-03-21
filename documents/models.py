import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Document(models.Model):
    """Document model for user uploads."""

    DOCUMENT_TYPES = [
        ('passport', 'Passport'),
        ('driving_license', 'Driving License'),
        ('marriage_certificate', 'Marriage Certificate'),
        ('educational_certificate', 'Educational Certificate'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    VERIFICATION_CHOICES = [
        ('unverified', 'Unverified'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('pending', 'Pending'),
    ]

    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_CHOICES,
        default='unverified'
    )
    description = models.TextField(blank=True)
    verification_id = models.CharField(max_length=12, unique=True, null=True, blank=True)
    verification_id_expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'documents'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_document_type_display()})"

    def generate_verification_id(self):
        """Generate a new verification ID that changes every 5 minutes."""
        self.verification_id = uuid.uuid4().hex[:12].upper()
        self.verification_id_expires_at = timezone.now() + timedelta(minutes=5)
        self.save()
        return self.verification_id

    def get_current_verification_id(self):
        """Get current verification ID, generating new one if expired."""
        if not self.verification_id or not self.verification_id_expires_at:
            return self.generate_verification_id()

        if timezone.now() >= self.verification_id_expires_at:
            return self.generate_verification_id()

        return self.verification_id

    def is_verification_id_valid(self, entered_id):
        """Check if the entered verification ID is valid."""
        if not self.verification_id or not entered_id:
            return False
        return self.verification_id == entered_id.upper() and timezone.now() < self.verification_id_expires_at
