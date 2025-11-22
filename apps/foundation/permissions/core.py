"""
Permissions centralisées et simplifiées pour toute la plateforme.
Basé sur OrganizationMember pour la gestion des rôles.
"""
from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()


class IsAuthenticated(permissions.IsAuthenticated):
    """Permission de base : utilisateur authentifié."""
    pass


class IsStaffUser(permissions.BasePermission):
    """Utilisateur staff/superuser (admin système)."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or request.user.is_superuser
        )


class IsResourceOwner(permissions.BasePermission):
    """Propriétaire de la ressource (created_by)."""
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        return False


class IsOrgMember(permissions.BasePermission):
    """
    Utilisateur est membre actif de l'organisation liée à la ressource.
    Fonctionne pour les ressources avec:
    - obj.organization (direct)
    - obj.project.organization (via projet)
    - obj.workflow.organization (via workflow)
    - obj.app.project.organization (via app)
    """
    
    def has_permission(self, request, view):
        """Vérifie que l'utilisateur est authentifié."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Staff peut tout voir
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Récupérer l'organisation de l'objet
        organization = self._get_organization(obj)
        
        if not organization:
            # Ressource personnelle (pas d'organisation)
            # Vérifier si l'utilisateur en est le propriétaire
            if hasattr(obj, 'created_by'):
                return obj.created_by == request.user
            if hasattr(obj, 'user'):
                return obj.user == request.user
            return False
        
        # Vérifier membership
        from apps.foundation.models import OrganizationMember
        return OrganizationMember.objects.filter(
            organization=organization,
            user=request.user,
            status='ACTIVE'
        ).exists()
    
    def _get_organization(self, obj):
        """Récupère l'organisation liée à l'objet."""
        if hasattr(obj, 'organization'):
            return obj.organization
        if hasattr(obj, 'project') and hasattr(obj.project, 'organization'):
            return obj.project.organization
        if hasattr(obj, 'workflow') and hasattr(obj.workflow, 'organization'):
            return obj.workflow.organization
        if hasattr(obj, 'app') and hasattr(obj.app, 'project'):
            return obj.app.project.organization
        return None


class IsOrgAdmin(permissions.BasePermission):
    """
    Utilisateur est ADMIN ou OWNER de l'organisation.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Staff peut tout faire
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Récupérer l'organisation
        organization = self._get_organization(obj)
        
        if not organization:
            # Ressource personnelle
            if hasattr(obj, 'created_by'):
                return obj.created_by == request.user
            if hasattr(obj, 'user'):
                return obj.user == request.user
            return False
        
        # Vérifier rôle ADMIN ou OWNER
        from apps.foundation.models import OrganizationMember
        return OrganizationMember.objects.filter(
            organization=organization,
            user=request.user,
            role__in=['ADMIN', 'OWNER'],
            status='ACTIVE'
        ).exists()
    
    def _get_organization(self, obj):
        """Récupère l'organisation liée à l'objet."""
        if hasattr(obj, 'organization'):
            return obj.organization
        if hasattr(obj, 'project') and hasattr(obj.project, 'organization'):
            return obj.project.organization
        if hasattr(obj, 'workflow') and hasattr(obj.workflow, 'organization'):
            return obj.workflow.organization
        if hasattr(obj, 'app') and hasattr(obj.app, 'project'):
            return obj.app.project.organization
        return None


class IsOrgOwner(permissions.BasePermission):
    """
    Utilisateur est OWNER de l'organisation uniquement.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Staff peut tout faire
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Récupérer l'organisation
        organization = self._get_organization(obj)
        
        if not organization:
            # Ressource personnelle
            if hasattr(obj, 'created_by'):
                return obj.created_by == request.user
            if hasattr(obj, 'user'):
                return obj.user == request.user
            return False
        
        # Vérifier rôle OWNER uniquement
        from apps.foundation.models import OrganizationMember
        return OrganizationMember.objects.filter(
            organization=organization,
            user=request.user,
            role='OWNER',
            status='ACTIVE'
        ).exists()
    
    def _get_organization(self, obj):
        """Récupère l'organisation liée à l'objet."""
        if hasattr(obj, 'organization'):
            return obj.organization
        if hasattr(obj, 'project') and hasattr(obj.project, 'organization'):
            return obj.project.organization
        if hasattr(obj, 'workflow') and hasattr(obj.workflow, 'organization'):
            return obj.workflow.organization
        if hasattr(obj, 'app') and hasattr(obj.app, 'project'):
            return obj.app.project.organization
        return None


class HasActiveSubscription(permissions.BasePermission):
    """
    L'organisation de l'utilisateur a un abonnement actif.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Staff bypass
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Récupérer les organisations de l'utilisateur
        from apps.foundation.models import OrganizationMember, Subscription
        
        org_ids = OrganizationMember.objects.filter(
            user=request.user,
            status='ACTIVE'
        ).values_list('organization_id', flat=True)
        
        # Vérifier qu'au moins une organisation a un abonnement actif
        return Subscription.objects.filter(
            organization_id__in=org_ids,
            status='ACTIVE'
        ).exists()


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Le propriétaire peut modifier, les autres peuvent seulement lire.
    """
    
    def has_object_permission(self, request, view, obj):
        # Lecture autorisée pour tout le monde
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Écriture uniquement pour le propriétaire
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        return False


# Helpers pour vérifier les rôles dans les vues
def get_user_organizations(user):
    """Retourne les IDs des organisations dont l'utilisateur est membre actif."""
    from apps.foundation.models import OrganizationMember
    
    return OrganizationMember.objects.filter(
        user=user,
        status='ACTIVE'
    ).values_list('organization_id', flat=True)


def is_org_member(user, organization):
    """Vérifie si l'utilisateur est membre actif de l'organisation."""
    from apps.foundation.models import OrganizationMember
    
    if not user or not user.is_authenticated:
        return False
    
    if user.is_staff or user.is_superuser:
        return True
    
    return OrganizationMember.objects.filter(
        organization=organization,
        user=user,
        status='ACTIVE'
    ).exists()


def is_org_admin(user, organization):
    """Vérifie si l'utilisateur est ADMIN ou OWNER de l'organisation."""
    from apps.foundation.models import OrganizationMember
    
    if not user or not user.is_authenticated:
        return False
    
    if user.is_staff or user.is_superuser:
        return True
    
    return OrganizationMember.objects.filter(
        organization=organization,
        user=user,
        role__in=['ADMIN', 'OWNER'],
        status='ACTIVE'
    ).exists()


def is_org_owner(user, organization):
    """Vérifie si l'utilisateur est OWNER de l'organisation."""
    from apps.foundation.models import OrganizationMember
    
    if not user or not user.is_authenticated:
        return False
    
    if user.is_staff or user.is_superuser:
        return True
    
    return OrganizationMember.objects.filter(
        organization=organization,
        user=user,
        role='OWNER',
        status='ACTIVE'
    ).exists()
