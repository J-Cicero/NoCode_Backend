"""
Permissions spécifiques au module Runtime pour le NoCode Platform.
Gère l'accès aux projets, tables et données générées dynamiquement.
"""

from rest_framework.permissions import BasePermission
from django.contrib.auth import get_user_model
from apps.foundation.models import OrganizationMember
from apps.foundation.permissions import get_user_organizations

User = get_user_model()


def get_user_role_in_organization(user, organization):
    """Retourne le rôle d'un utilisateur dans une organisation."""
    if not user.is_authenticated:
        return None
        
    # Admin app a le rôle le plus élevé
    if user.is_admin or user.is_superuser:
        return 'ADMIN_APP'
        
    # Propriétaire de l'org
    if organization.owner == user:
        return 'OWNER'
        
    # Membre actif
    membership = organization.members.filter(
        user=user, 
        status='ACTIVE'
    ).first()
    
    if membership:
        return membership.role
        
    return None


class IsProjectOwnerOrAdmin(BasePermission):
    """Propriétaire du projet OU admin de l'organisation."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Vérifier si l'utilisateur est owner de l'organisation du projet
        if hasattr(obj, 'project'):
            return obj.project.organization.owner == request.user
        elif hasattr(obj, 'organization'):
            return obj.organization.owner == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
            
        return False


class IsProjectMemberOrAdmin(BasePermission):
    """Membre de l'organisation du projet OU admin app."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Vérifier si l'utilisateur est membre de l'organisation du projet
        if hasattr(obj, 'project'):
            return obj.project.organization.members.filter(
                user=request.user, 
                status='ACTIVE'
            ).exists()
        elif hasattr(obj, 'organization'):
            return obj.organization.members.filter(
                user=request.user, 
                status='ACTIVE'
            ).exists()
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
            
        return False


class CanAccessProjectData(BasePermission):
    """Accès aux données du projet selon le rôle."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Récupérer l'organisation du projet
        if hasattr(obj, 'project'):
            organization = obj.project.organization
        elif hasattr(obj, 'organization'):
            organization = obj.organization
        else:
            return False
            
        user_role = get_user_role_in_organization(request.user, organization)
        
        if not user_role:
            return False
            
        # Owner peut tout faire
        if user_role == 'OWNER':
            return True
            
        # Admin peut lire et modifier
        if user_role == 'ADMIN':
            return request.method in ['GET', 'HEAD', 'OPTIONS', 'POST', 'PUT', 'PATCH']
            
        # Member peut seulement lire et créer (limité)
        if user_role == 'MEMBER':
            return request.method in ['GET', 'HEAD', 'OPTIONS', 'POST']
            
        return False


class CanManageProjectSchema(BasePermission):
    """Gestion du schéma du projet (tables, champs)."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Récupérer l'organisation du projet
        if hasattr(obj, 'project'):
            organization = obj.project.organization
        elif hasattr(obj, 'organization'):
            organization = obj.organization
        else:
            return False
            
        user_role = get_user_role_in_organization(request.user, organization)
        
        # Seul OWNER et ADMIN peuvent gérer le schéma
        return user_role in ['OWNER', 'ADMIN']


class CanDeployProject(BasePermission):
    """Déploiement du projet."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Récupérer l'organisation du projet
        if hasattr(obj, 'project'):
            organization = obj.project.organization
        elif hasattr(obj, 'organization'):
            organization = obj.organization
        else:
            return False
            
        user_role = get_user_role_in_organization(request.user, organization)
        
        # Seul OWNER peut déployer (ou ADMIN si autorisé par l'organisation)
        if user_role == 'OWNER':
            return True
        elif user_role == 'ADMIN':
            # Vérifier si les admins peuvent déployer (config organisation)
            return organization.allow_admin_deploy if hasattr(organization, 'allow_admin_deploy') else False
            
        return False


def has_project_access(user, project, required_permission='read'):
    """Vérifie l'accès à un projet selon le rôle."""
    if not user.is_authenticated:
        return False
        
    if user.is_admin or user.is_superuser:
        return True
        
    user_role = get_user_role_in_organization(user, project.organization)
    
    if not user_role:
        return False
        
    permissions = {
        'OWNER': {
            'read': True,
            'write': True,
            'delete': True,
            'schema': True,
            'deploy': True,
            'manage_users': True,
            'billing': True,
        },
        'ADMIN': {
            'read': True,
            'write': True,
            'delete': True,
            'schema': True,
            'deploy': False,  # Configurable par organisation
            'manage_users': True,
            'billing': False,
        },
        'MEMBER': {
            'read': True,
            'write': True,
            'delete': False,
            'schema': False,
            'deploy': False,
            'manage_users': False,
            'billing': False,
        }
    }
    
    return permissions.get(user_role, {}).get(required_permission, False)


class IsTableAccessible(BasePermission):
    """Vérifie l'accès à une table spécifique."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Vérifier l'accès au projet parent
        if hasattr(obj, 'project'):
            return has_project_access(request.user, obj.project, 'read')
            
        return False


class CanModifyTableData(BasePermission):
    """Modification des données dans une table."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Vérifier l'accès en écriture au projet
        if hasattr(obj, 'project'):
            return has_project_access(request.user, obj.project, 'write')
            
        return False


class CanDeleteTableData(BasePermission):
    """Suppression des données dans une table."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Vérifier l'accès en suppression au projet
        if hasattr(obj, 'project'):
            return has_project_access(request.user, obj.project, 'delete')
            
        return False


# Permissions pour les actions spécifiques
class CanExportData(BasePermission):
    """Exportation des données du projet."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Owner et Admin peuvent exporter
        if hasattr(obj, 'project'):
            user_role = get_user_role_in_organization(request.user, obj.project.organization)
            return user_role in ['OWNER', 'ADMIN']
            
        return False


class CanImportData(BasePermission):
    """Importation des données dans le projet."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Seul Owner et Admin peuvent importer
        if hasattr(obj, 'project'):
            user_role = get_user_role_in_organization(request.user, obj.project.organization)
            return user_role in ['OWNER', 'ADMIN']
            
        return False


class CanAccessAPIKeys(BasePermission):
    """Accès aux clés API du projet."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Seul Owner peut gérer les clés API
        if hasattr(obj, 'project'):
            user_role = get_user_role_in_organization(request.user, obj.project.organization)
            return user_role == 'OWNER'
            
        return False


class CanManageWebhooks(BasePermission):
    """Gestion des webhooks du projet."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Owner et Admin peuvent gérer les webhooks
        if hasattr(obj, 'project'):
            user_role = get_user_role_in_organization(request.user, obj.project.organization)
            return user_role in ['OWNER', 'ADMIN']
            
        return False


# Validation des permissions au niveau de l'organisation
def validate_organization_limits(user, organization, action='create_project'):
    """Valide les limites de l'organisation."""
    if not user.is_authenticated:
        return False, "Non authentifié"
        
    if user.is_admin or user.is_superuser:
        return True, "Admin app"
        
    user_role = get_user_role_in_organization(user, organization)
    
    if not user_role:
        return False, "Non membre"
        
    # Vérifier les limites selon l'action
    if action == 'create_project':
        current_projects = organization.projects.count()
        if current_projects >= organization.max_projects:
            return False, f"Limite de projets atteinte ({organization.max_projects})"
            
    elif action == 'add_member':
        current_members = organization.members.count()
        if current_members >= organization.max_members:
            return False, f"Limite de membres atteinte ({organization.max_members})"
            
    return True, "Autorisé"


# Permission composite pour les vues avec objets multiples
class IsProjectResource(BasePermission):
    """Permission de base pour les ressources de projet."""
    
    def has_permission(self, request, view):
        """Vérifie la permission au niveau de la vue."""
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Vérifier si le projet est dans les paramètres de l'URL
        project_id = view.kwargs.get('project_pk') or view.kwargs.get('project_id')
        if project_id:
            try:
                from apps.runtime.models import Project
                project = Project.objects.get(id=project_id)
                return has_project_access(request.user, project, 'read')
            except Project.DoesNotExist:
                return False
                
        return True  # Si pas de projet spécifié, laisser has_object_permission gérer
    
    def has_object_permission(self, request, view, obj):
        """Vérifie la permission sur l'objet."""
        return CanAccessProjectData().has_object_permission(request, view, obj)


# Permissions pour les endpoints spéciaux
class CanAccessAnalytics(BasePermission):
    """Accès aux analytics du projet."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Owner et Admin peuvent voir les analytics
        if hasattr(obj, 'project'):
            user_role = get_user_role_in_organization(request.user, obj.project.organization)
            return user_role in ['OWNER', 'ADMIN']
            
        return False


class CanManageAutomation(BasePermission):
    """Gestion des workflows et automatisations."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Owner et Admin peuvent gérer les automatisations
        if hasattr(obj, 'project'):
            user_role = get_user_role_in_organization(request.user, obj.project.organization)
            return user_role in ['OWNER', 'ADMIN']
            
        return False


# Helper pour déterminer les permissions requises selon l'action
def get_required_permission(action):
    """Retourne la permission requise pour une action."""
    mapping = {
        'list': 'read',
        'retrieve': 'read',
        'create': 'write',
        'update': 'write',
        'partial_update': 'write',
        'destroy': 'delete',
        'schema': 'schema',
        'deploy': 'deploy',
        'export': 'export',
        'import': 'import',
        'analytics': 'read',
        'automation': 'schema',
    }
    return mapping.get(action, 'read')
