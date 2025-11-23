"""
Configuration de l'administration Django pour le module Studio.
"""
from django.contrib import admin
from .models import (
    Project, DataSchema, Page, Component, 
    CollaborationSession, ComponentInstance, EditLock
)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Administration pour les projets Studio."""
    list_display = ['id']


@admin.register(DataSchema)
class DataSchemaAdmin(admin.ModelAdmin):
    """Administration pour les schémas de données Studio."""
    list_display = ['id']


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    """Administration pour les pages Studio."""
    list_display = ['id']


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    """Administration pour les composants Studio."""
    list_display = ['id']


@admin.register(EditLock)
class EditLockAdmin(admin.ModelAdmin):
    """Administration pour les verrous d'édition."""
    list_display = ['id']


@admin.register(CollaborationSession)
class CollaborationSessionAdmin(admin.ModelAdmin):
    """Administration pour les sessions de collaboration."""
    list_display = ['id']


@admin.register(ComponentInstance)
class ComponentInstanceAdmin(admin.ModelAdmin):
    """Administration pour les instances de composants."""
    list_display = ['id']


