from django.db import models
from .project import Project


class Page(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='pages')
    name = models.CharField(max_length=255)
    route = models.CharField(max_length=255)
    config = models.JSONField(default=dict)
    is_home = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('project', 'route')
        ordering = ['created_at']
        db_table = 'studio_page'

    def save(self, *args, **kwargs):
        if self.is_home:
            Page.objects.filter(project=self.project, is_home=True).exclude(pk=self.pk).update(is_home=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.route})"
