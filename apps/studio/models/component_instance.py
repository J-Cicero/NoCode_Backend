from django.db import models
from .page import Page
from .component import Component
from .attribute import Attribute


class ComponentInstance(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='component_instances')
    component = models.ForeignKey(Component, on_delete=models.CASCADE, related_name='instances')
    order = models.PositiveIntegerField(default=0)
    config = models.JSONField(default=dict)
    linked_field_schema = models.ForeignKey(Attribute, on_delete=models.SET_NULL, null=True, blank=True, related_name='component_instances')
    is_auto_generated = models.BooleanField(default=False)
    needs_sync = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'created_at']
        db_table = 'studio_componentinstance'

    def __str__(self):
        return f"{self.component.display_name} sur {self.page.name}"
