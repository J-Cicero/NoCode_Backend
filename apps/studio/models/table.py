from django.db import models
from django.contrib.auth import get_user_model
from apps.foundation.models import Organization
import uuid

User = get_user_model()


class Table(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='schemas')
    table_name = models.SlugField(max_length=63)
    display_name = models.CharField(max_length=255)
    fields_config = models.JSONField(default=dict)
    icon = models.CharField(max_length=10, default='📋')
    description = models.TextField(blank=True)
    auto_generate_pages = models.BooleanField(default=True)
    schema_version = models.IntegerField(default=1)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('project', 'table_name')
        ordering = ['created_at']
        db_table = 'studio_dataschema'

    def __str__(self):
        return f"{self.display_name} ({self.table_name})"
    
    @property
    def structured_fields(self):
        structured = list(self.attributes.all())
        if structured:
            return structured
        return self._convert_json_to_fields()
    
    def _convert_json_to_fields(self):
        fields = []
        for field_name, field_config in self.fields_config.items():
            fields.append({
                'name': field_name,
                'display_name': field_config.get('display_name', field_name.capitalize()),
                'field_type': field_config.get('type', 'TEXT_SHORT'),
                'is_required': field_config.get('required', False),
                'is_unique': field_config.get('unique', False),
                'default_value': field_config.get('default'),
                'choices': field_config.get('choices'),
                'related_schema': field_config.get('related_schema'),
                'order': field_config.get('order', 0)
            })
        return sorted(fields, key=lambda x: x['order'])
    
    def regenerate_pages(self):
        from .signals_auto_generation import regenerate_schema_components
        regenerate_schema_components(self)
    
    def sync_components(self):
        from .services.page_builder import PageBuilder
        page_builder = PageBuilder(self)
        page_builder.sync_components()
    
    def generate_pages(self):
        from .services.page_builder import PageBuilder
        page_builder = PageBuilder(self)
        page_builder.generate_pages()
