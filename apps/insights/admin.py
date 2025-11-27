"""
Configuration de l'administration Django pour le module Insights.
"""
from django.contrib import admin
from .models import (
    UserActivity, SystemMetric, ApplicationMetric, 
    UserMetric, PerformanceMetric
)


# Only show Insights admin to superusers/staff
def has_admin_permission(request):
    """Check if user has admin permissions for Insights module"""
    return request.user.is_superuser or request.user.is_staff


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """Administration pour les activités utilisateur."""
    list_display = ['id']
    readonly_fields = ['id']
    
    def has_module_permission(self, request):
        return has_admin_permission(request)
    
    def has_view_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_change_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_add_permission(self, request):
        return has_admin_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        return has_admin_permission(request)


@admin.register(SystemMetric)
class SystemMetricAdmin(admin.ModelAdmin):
    """Administration pour les métriques système."""
    list_display = ['id']
    readonly_fields = ['id']
    
    def has_module_permission(self, request):
        return has_admin_permission(request)
    
    def has_view_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_change_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_add_permission(self, request):
        return has_admin_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        return has_admin_permission(request)


@admin.register(ApplicationMetric)
class ApplicationMetricAdmin(admin.ModelAdmin):
    """Administration pour les métriques applicatives."""
    list_display = ['id']
    readonly_fields = ['id']
    
    def has_module_permission(self, request):
        return has_admin_permission(request)
    
    def has_view_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_change_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_add_permission(self, request):
        return has_admin_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        return has_admin_permission(request)


@admin.register(UserMetric)
class UserMetricAdmin(admin.ModelAdmin):
    """Administration pour les métriques utilisateur."""
    list_display = ['id']
    readonly_fields = ['id']
    
    def has_module_permission(self, request):
        return has_admin_permission(request)
    
    def has_view_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_change_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_add_permission(self, request):
        return has_admin_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        return has_admin_permission(request)


@admin.register(PerformanceMetric)
class PerformanceMetricAdmin(admin.ModelAdmin):
    """Administration pour les métriques de performance."""
    list_display = ['id']
    readonly_fields = ['id']
    
    def has_module_permission(self, request):
        return has_admin_permission(request)
    
    def has_view_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_change_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_add_permission(self, request):
        return has_admin_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        return has_admin_permission(request)
