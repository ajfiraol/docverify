from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with role-based profiles."""

    ROLE_CHOICES = [
        ('user', 'Regular User'),
        ('institution', 'Institution'),
        ('company', 'Company'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_regular_user(self):
        return self.role == 'user'

    @property
    def is_institution(self):
        return self.role == 'institution'

    @property
    def is_company(self):
        return self.role == 'company'
