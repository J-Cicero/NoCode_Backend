
from rest_framework import permissions
from .models import Project
from apps.foundation.models import OrganizationMember

class HasProjectAccess(permissions.BasePermission):
    """
    Permission personnalisée pour les projets NoCode.
    
    Règles:
    - Client individuel: contrôle total sur ses propres projets
    - OWNER/ADMIN d'organisation: contrôle total sur les projets de l'org
    - MEMBER d'organisation: lecture seule sur les projets de l'org
    """
    
    def has_permission(self, request, view):
        # Vérifie que l'utilisateur est authentifié
        if not request.user.is_authenticated:
            return False
        
        # Pour la création de projet (POST sans project_id), on autorise tout utilisateur authentifié
        project_id = view.kwargs.get('pk') or view.kwargs.get('project_id')
        if request.method == 'POST' and not project_id:
            return True
            
        # Si pas de project_id, on laisse passer (le queryset filtrera)
        if not project_id:
            return True
                
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return False
        
        # Vérifie si l'utilisateur est le créateur du projet (client individuel)
        if project.created_by == request.user:
            return True
        
        # Vérifie les permissions au niveau de l'organisation
        if project.organization:
            membership = OrganizationMember.objects.filter(
                organization=project.organization,
                user=request.user,
                status='ACTIVE'
            ).first()
            
            if not membership:
                return False
            
            # SAFE_METHODS (GET, HEAD, OPTIONS): tous les membres peuvent lire
            if request.method in permissions.SAFE_METHODS:
                return True
            
            # Méthodes modifiantes: uniquement OWNER et ADMIN
            return membership.role in ['OWNER', 'ADMIN']
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """
        Permission au niveau objet.
        Gère Project et les objets liés (Table, Page, Component, etc.)
        """
        # Récupérer le projet associé à l'objet
        if isinstance(obj, Project):
            project = obj
        elif hasattr(obj, 'project'):
            project = obj.project
        elif hasattr(obj, 'page') and hasattr(obj.page, 'project'):
            project = obj.page.project
        elif hasattr(obj, 'schema') and hasattr(obj.schema, 'project'):
            project = obj.schema.project
        else:
            # Si on ne peut pas déterminer le projet, on refuse
            return False
        
        # Vérifie si l'utilisateur est le créateur du projet
        if project.created_by == request.user:
            return True
        
        # Vérifie les permissions au niveau de l'organisation
        if project.organization:
            membership = OrganizationMember.objects.filter(
                organization=project.organization,
                user=request.user,
                status='ACTIVE'
            ).first()
            
            if not membership:
                return False
            
            # SAFE_METHODS: tous les membres peuvent lire
            if request.method in permissions.SAFE_METHODS:
                return True
            
            # Méthodes modifiantes: uniquement OWNER et ADMIN
            return membership.role in ['OWNER', 'ADMIN']
        
        return False
