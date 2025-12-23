
from rest_framework import permissions
from django.contrib.auth import get_user_model
from ..models import Organization, OrganizationMember

User = get_user_model()


class UserRole:
    USER_SIMPLE = 'USER_SIMPLE'
    ORGANIZATION_CREATOR = 'ORGANIZATION_CREATOR'
    ORGANIZATION_MEMBER = 'ORGANIZATION_MEMBER'
    ORGANIZATION_OWNER = 'ORGANIZATION_OWNER'


def get_user_role(user):
    if not user or not user.is_authenticated:
        return None
    
    has_created_org = Organization.objects.filter(owner=user).exists()
    
    if has_created_org:
        return UserRole.ORGANIZATION_CREATOR
    
    is_member = OrganizationMember.objects.filter(
        user=user,
        status='ACTIVE'
    ).exists()
    
    if is_member:
        return UserRole.ORGANIZATION_MEMBER
    
    return UserRole.USER_SIMPLE


def get_user_role_in_organization(user, organization):
    if not user or not user.is_authenticated or not organization:
        return None
    
    if organization.owner == user:
        return UserRole.ORGANIZATION_OWNER
    
    try:
        member = OrganizationMember.objects.get(
            organization=organization,
            user=user,
            status='ACTIVE'
        )
        
        if member.role == 'OWNER':
            return UserRole.ORGANIZATION_OWNER
        else:
            return UserRole.ORGANIZATION_MEMBER
        
    except OrganizationMember.DoesNotExist:
        pass
    
    return None


class IsUserSimple(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        role = get_user_role(request.user)
        return role == UserRole.USER_SIMPLE
    
    def has_object_permission(self, request, view, obj):
        """L'utilisateur simple ne peut accéder qu'à ses propres ressources."""
        if not request.user.is_authenticated:
            return False
        
        # Vérifier si c'est une ressource personnelle
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        return False


class IsOrganizationCreator(permissions.BasePermission):
    """
    Permission pour les créateurs d'organisation.
    Peuvent créer des organisations et gérer leurs propres organisations.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        role = get_user_role(request.user)
        return role == UserRole.ORGANIZATION_CREATOR
    
    def has_object_permission(self, request, view, obj):
        """Le créateur peut gérer ses propres organisations."""
        if not request.user.is_authenticated:
            return False
        
        # Si c'est une organisation, vérifier si c'est le propriétaire
        if isinstance(obj, Organization):
            return obj.owner == request.user
        
        # Pour les autres ressources, vérifier via l'organisation
        organization = _get_organization_from_obj(obj)
        if organization:
            return organization.owner == request.user
        
        # Sinon, vérifier si c'est une ressource personnelle
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False


class IsOrganizationMember(permissions.BasePermission):
    """
    Permission pour les membres d'organisation.
    Accès limité aux ressources de leur organisation.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        role = get_user_role(request.user)
        return role in [UserRole.ORGANIZATION_MEMBER, UserRole.ORGANIZATION_CREATOR]
    
    def has_object_permission(self, request, view, obj):
        """Le membre peut accéder aux ressources de son organisation."""
        if not request.user.is_authenticated:
            return False
        
        organization = _get_organization_from_obj(obj)
        
        if not organization:
            # Ressource personnelle
            if hasattr(obj, 'created_by'):
                return obj.created_by == request.user
            return False
        
        # Vérifier si l'utilisateur est membre de l'organisation
        return OrganizationMember.objects.filter(
            organization=organization,
            user=request.user,
            status='ACTIVE'
        ).exists()




class IsOrganizationOwner(permissions.BasePermission):
    """
    Permission pour les OWNER d'une organisation.
    Peuvent tout faire dans leur organisation.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Vérifier si l'utilisateur est OWNER d'au moins une organisation
        return Organization.objects.filter(owner=request.user).exists()
    
    def has_object_permission(self, request, view, obj):
        """L'owner peut tout faire dans son organisation."""
        if not request.user.is_authenticated:
            return False
        
        # Si c'est une organisation, vérifier si c'est le propriétaire
        if isinstance(obj, Organization):
            return obj.owner == request.user
        
        organization = _get_organization_from_obj(obj)
        
        if not organization:
            return False
        
        # Vérifier si l'utilisateur est le propriétaire de l'organisation
        return organization.owner == request.user


class CanCreateOrganization(permissions.BasePermission):
    """
    Permission pour créer une organisation.
    Tous les utilisateurs authentifiés peuvent créer une organisation.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class CanInviteMembers(permissions.BasePermission):
    """
    Permission pour inviter des membres dans une organisation.
    Seuls les OWNER peuvent inviter.
    """
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        if isinstance(obj, Organization):
            organization = obj
        else:
            organization = _get_organization_from_obj(obj)
        
        if not organization:
            return False
        
        # Seul le propriétaire (OWNER) peut inviter des membres
        return organization.owner == request.user


class CanRemoveMembers(permissions.BasePermission):
    """
    Permission pour supprimer des membres d'une organisation.
    Seuls les OWNER peuvent supprimer des membres.
    """
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        if isinstance(obj, Organization):
            organization = obj
        else:
            organization = _get_organization_from_obj(obj)
        
        if not organization:
            return False
        
        # Seul le propriétaire peut supprimer des membres
        return organization.owner == request.user


# ============================================================================
# PERMISSIONS COMPOSÉES
# ============================================================================

class IsOwnerOrOrgMember(permissions.BasePermission):
    """
    Permission composée: propriétaire de la ressource OU membre de l'organisation.
    """
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Vérifier si c'est le propriétaire
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        if hasattr(obj, 'owner') and obj.owner == request.user:
            return True
        
        # Vérifier si c'est un membre de l'organisation
        organization = _get_organization_from_obj(obj)
        if organization:
            return OrganizationMember.objects.filter(
                organization=organization,
                user=request.user,
                status='ACTIVE'
            ).exists()
        
        return False


class IsOwnerOrOrgOwner(permissions.BasePermission):
    """
    Permission composée: propriétaire de la ressource OU OWNER de l'organisation.
    """
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Vérifier si c'est le propriétaire de la ressource
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        if hasattr(obj, 'owner') and obj.owner == request.user:
            return True
        
        # Vérifier si c'est le OWNER de l'organisation
        organization = _get_organization_from_obj(obj)
        if organization:
            return organization.owner == request.user
        
        return False


# ============================================================================
# HELPERS PRIVÉS
# ============================================================================

def _get_organization_from_obj(obj):
    """Récupère l'organisation liée à un objet."""
    if isinstance(obj, Organization):
        return obj
    
    if hasattr(obj, 'organization'):
        return obj.organization
    
    if hasattr(obj, 'project') and hasattr(obj.project, 'organization'):
        return obj.project.organization
    
    if hasattr(obj, 'workflow') and hasattr(obj.workflow, 'organization'):
        return obj.workflow.organization
    
    if hasattr(obj, 'app') and hasattr(obj.app, 'project'):
        return obj.app.project.organization
    
    return None

