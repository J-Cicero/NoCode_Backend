"""
Permissions personnalisées pour le module Studio.
"""
from rest_framework import permissions
from .models import Project, OrganizationMember


class HasProjectAccess(permissions.BasePermission):
    """
    Vérifie que l'utilisateur a accès au projet.
    L'utilisateur doit être membre de l'organisation du projet.
    """
    
    def has_permission(self, request, view):
        # Vérifie que l'utilisateur est authentifié
        if not request.user.is_authenticated:
            return False
            
        # Pour les méthodes non sécurisées (GET, HEAD, OPTIONS),
        # on vérifie que l'utilisateur est membre de l'organisation
        if request.method in permissions.SAFE_METHODS:
            project_id = view.kwargs.get('pk') or view.kwargs.get('project_id')
            if not project_id:
                # Si on ne peut pas déterminer le projet, on refuse par sécurité
                return False
                
            try:
                project = Project.objects.get(id=project_id)
                return project.organization.members.filter(id=request.user.id).exists()
            except Project.DoesNotExist:
                return False
                
        # Pour les méthodes modifiantes (POST, PUT, PATCH, DELETE),
        # on vérifie que l'utilisateur est admin de l'organisation
        # ou propriétaire du projet
        project_id = view.kwargs.get('pk') or view.kwargs.get('project_id')
        if not project_id:
            return False
            
        try:
            project = Project.objects.get(id=project_id)
            # Vérifie si l'utilisateur est propriétaire du projet
            if project.created_by == request.user:
                return True
                
            # Vérifie si l'utilisateur est admin de l'organisation
            return OrganizationMember.objects.filter(
                organization=project.organization,
                user=request.user,
                role__in=['OWNER', 'ADMIN']
            ).exists()
            
        except Project.DoesNotExist:
            return False
    
    def has_object_permission(self, request, view, obj):
        # Pour les méthodes non sécurisées, on vérifie que l'utilisateur est membre de l'org
        if request.method in permissions.SAFE_METHODS:
            return obj.organization.members.filter(id=request.user.id).exists()
            
        # Pour les méthodes modifiantes, on vérifie que l'utilisateur est admin ou propriétaire
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
            
        # Vérifie si l'utilisateur est admin de l'organisation
        return OrganizationMember.objects.filter(
            organization=obj.organization,
            user=request.user,
            role__in=['OWNER', 'ADMIN']
        ).exists()
