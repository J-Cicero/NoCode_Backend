"""
Configuration de l'administration Django pour le module Runtime.
"""
from django.contrib import admin
from .models import (
    GeneratedApp, DeploymentLog
)


# Only show Runtime admin to superusers/staff
def has_admin_permission(request):
    """Check if user has admin permissions for Runtime module"""
    return request.user.is_superuser or request.user.is_staff


@admin.register(GeneratedApp)
class GeneratedAppAdmin(admin.ModelAdmin):
    """Administration pour les applications générées."""
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


@admin.register(DeploymentLog)
class DeploymentLogAdmin(admin.ModelAdmin):
    """Administration pour les logs de déploiement."""
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
