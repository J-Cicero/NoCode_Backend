from django.db import models
from django.contrib.auth import get_user_model
from .project import Project

User = get_user_model()


class EditLock(models.Model):
    ELEMENT_TYPE_CHOICES = [
        ('page', 'Page'),
        ('component', 'Composant'),
        ('schema', 'Schéma de données'),
        ('project', 'Projet'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='edit_locks')
    element_type = models.CharField(max_length=20, choices=ELEMENT_TYPE_CHOICES)
    element_id = models.CharField(max_length=255)
    locked_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='edit_locks')
    locked_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'studio_edit_lock'
        ordering = ['-locked_at']
        indexes = [
            models.Index(fields=['project', 'element_type', 'element_id']),
            models.Index(fields=['locked_by']),
            models.Index(fields=['locked_at']),
        ]
        unique_together = ('project', 'element_type', 'element_id')
    
    def __str__(self):
        return f"{self.element_type} {self.element_id} - {self.locked_by.email}"
    
    @property
    def is_expired(self):
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False
    
    def extend_lock(self, minutes=5):
        from django.utils import timezone
        from datetime import timedelta
        self.expires_at = timezone.now() + timedelta(minutes=minutes)
        self.save(update_fields=['expires_at'])


class CollaborationSession(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='collaboration_sessions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collaboration_sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    channel_name = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'studio_collaboration_session'
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['project', 'is_active']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['last_activity']),
        ]
    
    def __str__(self):
        return f"{self.user.email} sur {self.project.name}"
    
    @property
    def is_stale(self):
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() - self.last_activity > timedelta(minutes=5)
    
    def mark_inactive(self):
        self.is_active = False
        self.save(update_fields=['is_active'])
