"""
Configuration de l'administration Django pour le module Insights.
"""
from django.contrib import admin
from .models import (
    UserActivity, SystemMetric, ApplicationMetric, 
    UserMetric, PerformanceMetric
)


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """Administration pour les activités utilisateur."""
    list_display = ['id']
    readonly_fields = ['id']


@admin.register(SystemMetric)
class SystemMetricAdmin(admin.ModelAdmin):
    """Administration pour les métriques système."""
    list_display = ['id']
    readonly_fields = ['id']


@admin.register(ApplicationMetric)
class ApplicationMetricAdmin(admin.ModelAdmin):
    """Administration pour les métriques applicatives."""
    list_display = ['id']
    readonly_fields = ['id']


@admin.register(UserMetric)
class UserMetricAdmin(admin.ModelAdmin):
    """Administration pour les métriques utilisateur."""
    list_display = ['id']
    readonly_fields = ['id']


@admin.register(PerformanceMetric)
class PerformanceMetricAdmin(admin.ModelAdmin):
    """Administration pour les métriques de performance."""
    list_display = ['id']
    readonly_fields = ['id']
