"""
Configuration de l'administration Django pour le module Runtime.
"""
from django.contrib import admin
from .models import (
    GeneratedApp, DeploymentLog
)


@admin.register(GeneratedApp)
class GeneratedAppAdmin(admin.ModelAdmin):
    """Administration pour les applications générées."""
    list_display = ['id']
    readonly_fields = ['id']


@admin.register(DeploymentLog)
class DeploymentLogAdmin(admin.ModelAdmin):
    """Administration pour les logs de déploiement."""
    list_display = ['id']
    readonly_fields = ['id']
