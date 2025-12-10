from django.db import models


class Component(models.Model):
    COMPONENT_CATEGORIES = [
        ('layout', 'Layout'),
        ('forms', 'Formulaires'),
        ('content', 'Contenu'),
        ('navigation', 'Navigation'),
        ('data', 'Données'),
        ('media', 'Médias'),
        ('feedback', 'Feedback'),
        ('overlay', 'Overlay'),
    ]

    name = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=COMPONENT_CATEGORIES, default='content')
    icon = models.CharField(max_length=100, blank=True)
    properties = models.JSONField(default=dict)
    validation_rules = models.JSONField(default=dict)
    default_config = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    version = models.CharField(max_length=20, default='1.0.0')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']
        db_table = 'studio_component'

    def __str__(self):
        return f"{self.display_name} ({self.category})"
