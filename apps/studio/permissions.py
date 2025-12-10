
from rest_framework import permissions
from .models import Project
from apps.foundation.models import OrganizationMember

class HasProjectAccess(permissions.BasePermission):

    
    def has_permission(self, request, view):
        # Vérifie que l'utilisateur est authentifié
        if not request.user.is_authenticated:
            return False
            
        # Pour les méthodes non sécurisées (GET, HEAD, OPTIONS),
        # on vérifie que l'utilisateur est membre de l'organisation OU propriétaire du projet
        if request.method in permissions.SAFE_METHODS:
            project_id = view.kwargs.get('pk') or view.kwargs.get('project_id')
            if not project_id:
                # Si on ne peut pas déterminer le projet, on refuse par sécurité
                return False
                
            try:
                project = Project.objects.get(id=project_id)
                # Permet l'accès si l'utilisateur est le créateur du projet
                if project.created_by == request.user:
                    return True
                # Vérifie si l'utilisateur est membre de l'organisation
                if project.organization and project.organization.members.filter(id=request.user.id).exists():
                    return True
                return False
            except Project.DoesNotExist:
                return False
                
        # Pour les méthodes modifiantes (POST, PUT, PATCH, DELETE),
        # on vérifie que l'utilisateur est admin de l'organisation
        # OU propriétaire du projet (projets personnels autorisés)
        project_id = view.kwargs.get('pk') or view.kwargs.get('project_id')
        
        # Pour la création de projet (POST sans project_id), on autorise tout utilisateur authentifié
        if request.method == 'POST' and not project_id:
            return True
            
        if not project_id:
            return False
            
        try:
            project = Project.objects.get(id=project_id)
            # Vérifie si l'utilisateur est propriétaire du projet
            if project.created_by == request.user:
                return True
                
            # Vérifie si l'utilisateur est admin de l'organisation
            if project.organization:
                return OrganizationMember.objects.filter(
                    organization=project.organization,
                    user=request.user,
                    role__in=['OWNER', 'ADMIN']
                ).exists()
            
        except Project.DoesNotExist:
            return False
    
    def has_object_permission(self, request, view, obj):
        # Pour les méthodes non sécurisées, on vérifie que l'utilisateur est membre de l'org OU propriétaire
        if request.method in permissions.SAFE_METHODS:
            # Permet l'accès si l'utilisateur est le créateur du projet
            if hasattr(obj, 'created_by') and obj.created_by == request.user:
                return True
            # Vérifie si l'utilisateur est membre de l'organisation
            if hasattr(obj, 'organization') and obj.organization and obj.organization.members.filter(id=request.user.id).exists():
                return True
            return False
            
        # Pour les méthodes modifiantes, on vérifie que l'utilisateur est admin ou propriétaire
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
            
        # Vérifie si l'utilisateur est admin de l'organisation
        if hasattr(obj, 'organization') and obj.organization:
            return OrganizationMember.objects.filter(
                organization=obj.organization,
                user=request.user,
                role__in=['OWNER', 'ADMIN']
            ).exists()
        
        return False
