"""
Permissions basées sur les rôles pour le module Foundation.
Gère les accès selon : ADMIN_APP > OWNER > MEMBER > CLIENT
"""

from rest_framework.permissions import BasePermission
from django.contrib.auth import get_user_model

User = get_user_model()


class IsAdminApp(BasePermission):
    """Uniquement les administrateurs de l'application."""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            (request.user.is_admin or request.user.is_superuser)
        )


class IsOwnerOrAdmin(BasePermission):
    """Propriétaire de la ressource OU admin de l'app."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Vérifier si l'utilisateur est propriétaire
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'id'):
            return obj.id == request.user.id
            
        return False


class IsOrganizationOwnerOrAdmin(BasePermission):
    """Propriétaire de l'organisation OU admin app."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Vérifier si l'utilisateur est owner de l'organisation
        if hasattr(obj, 'organization'):
            return obj.organization.owner == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
            
        return False


class IsOrganizationMemberOrAdmin(BasePermission):
    """Membre de l'organisation OU admin app."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Vérifier si l'utilisateur est membre de l'organisation
        if hasattr(obj, 'organization'):
            return obj.organization.members.filter(
                user=request.user, 
                status='ACTIVE'
            ).exists()
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
            
        return False


class CanAccessOwnDataOrAdmin(BasePermission):
    """Accéder à ses propres données OU admin app (pas les données perso des autres)."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app peut voir mais pas modifier les données perso
        if request.user.is_admin or request.user.is_superuser:
            return request.method in ['GET', 'HEAD', 'OPTIONS']
            
        # Utilisateur ne peut accéder qu'à ses propres données
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'id'):
            return obj.id == request.user.id
            
        return False


class IsOwnerOrReadOnly(BasePermission):
    """Propriétaire peut modifier, autres peuvent seulement lire."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Lecture autorisée pour tout utilisateur authentifié
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
            
        # Écriture uniquement pour le propriétaire ou admin
        if hasattr(obj, 'owner'):
            return obj.owner == request.user or request.user.is_admin
        elif hasattr(obj, 'user'):
            return obj.user == request.user or request.user.is_admin
            
        return False


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


def can_user_access_organization(user, organization, required_role='MEMBER'):
    """Vérifie si un utilisateur peut accéder à une organisation."""
    user_role = get_user_role_in_organization(user, organization)
    
    if not user_role:
        return False
        
    # Hiérarchie des rôles
    role_hierarchy = {
        'ADMIN_APP': 4,
        'OWNER': 3,
        'ADMIN': 2,
        'MEMBER': 1,
        'CLIENT': 0
    }
    
    return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)
