from django.db import models
from django.contrib.auth import get_user_model
from apps.foundation.models import Organization
import uuid

User = get_user_model()


class Project(models.Model):
    tracking_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=255)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='projects', null=True, blank=True)
    schema_name = models.CharField(max_length=63, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        db_table = 'studio_project'

    def __str__(self):
        return f"{self.name} ({self.schema_name})"
