
from rest_framework import permissions
from django.contrib.auth import get_user_model
from ..models import Organization, OrganizationMember

User = get_user_model()

class IsOwnerOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return obj.owner == request.user if hasattr(obj, 'owner') else obj.user == request.user


class IsOrganizationMember(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False
        
        try:
            organization = Organization.objects.get(id=org_id)
            return OrganizationMember.objects.filter(
                organization=organization,
                user=request.user,
                status='ACTIVE'
            ).exists()
        except Organization.DoesNotExist:
            return False


class IsOrganizationOwner(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False
        
        try:
            organization = Organization.objects.get(id=org_id)
            return organization.owner == request.user
        except Organization.DoesNotExist:
            return False


class IsOrganizationAdmin(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False
        
        try:
            organization = Organization.objects.get(id=org_id)
            
            # Vérifier si c'est le propriétaire
            if organization.owner == request.user:
                return True
            
            # Vérifier si c'est un admin
            try:
                member = OrganizationMember.objects.get(
                    organization=organization,
                    user=request.user,
                    status='ACTIVE'
                )
                return member.role in ['OWNER', 'ADMIN']
            except OrganizationMember.DoesNotExist:
                return False
                
        except Organization.DoesNotExist:
            return False


class CanManageBilling(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False
        
        try:
            organization = Organization.objects.get(id=org_id)
            
            if organization.owner == request.user:
                return True
            
            try:
                member = OrganizationMember.objects.get(
                    organization=organization,
                    user=request.user,
                    status='ACTIVE'
                )
                return member.role in ['OWNER', 'ADMIN']
            except OrganizationMember.DoesNotExist:
                return False
                
        except Organization.DoesNotExist:
            return False


class IsEntrepriseOwner(permissions.BasePermission):

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        org_id = view.kwargs.get('org_id') or view.kwargs.get('entreprise_id')
        if not org_id:
            return False
        
        try:
            organization = Organization.objects.get(id=org_id)
            return organization.owner == request.user
        except Organization.DoesNotExist:
            return False
    
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Organization):
            return obj.owner == request.user
        return False


class IsStaffOrOwner(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        
        # Vérifier si c'est le propriétaire
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        return False


class IsVerifiedEntreprise(permissions.BasePermission):
    """Vérifie si l'utilisateur a une organisation vérifiée."""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Récupérer les organisations vérifiées de l'utilisateur
        user_organizations = Organization.objects.filter(
            members__user=request.user,
            members__status='ACTIVE',
            is_verified=True
        )
        
        return user_organizations.exists()


class HasActiveSubscription(permissions.BasePermission):

    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False
        
        try:
            organization = Organization.objects.get(id=org_id)
            
            # Vérifier qu'il y a un abonnement actif
            from ..models import Abonnement
            return Abonnement.objects.filter(
                organization=organization,
                status='ACTIF'
            ).exists()
            
        except Organization.DoesNotExist:
            return False


class CanInviteMembers(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False
        
        try:
            organization = Organization.objects.get(id=org_id)
            
            # Vérifier les paramètres de l'organisation
            try:
                settings = organization.settings
                if not settings.allow_member_invites:
                    # Seuls les propriétaires et admins peuvent inviter si désactivé
                    if organization.owner == request.user:
                        return True
                    
                    try:
                        member = OrganizationMember.objects.get(
                            organization=organization,
                            user=request.user,
                            status='ACTIVE'
                        )
                        return member.role in ['OWNER', 'ADMIN']
                    except OrganizationMember.DoesNotExist:
                        return False
                else:
                    # Tous les membres peuvent inviter si activé
                    return OrganizationMember.objects.filter(
                        organization=organization,
                        user=request.user,
                        status='ACTIVE'
                    ).exists()
                    
            except:
                # Si pas de paramètres, utiliser la logique par défaut
                return OrganizationMember.objects.filter(
                    organization=organization,
                    user=request.user,
                    status='ACTIVE'
                ).exists()
                
        except Organization.DoesNotExist:
            return False


class IsOwnerOrStaff(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'client') and hasattr(obj.client, 'user'):
            return obj.client.user == request.user
        
        return False


class CanAccessUserData(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        user_id = view.kwargs.get('user_id')
        if not user_id:
            return True  # Accès à ses propres données
        
        if request.user.is_staff:
            return True
        
        return str(request.user.id) == str(user_id)


class HasSubscriptionLimit(permissions.BasePermission):

    
    def __init__(self, limit_type, usage_field=None):
        self.limit_type = limit_type
        self.usage_field = usage_field
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False
        
        try:
            organization = Organization.objects.get(id=org_id)
            
            # Récupérer l'abonnement actif
            from ..models import Abonnement
            subscription = Abonnement.objects.filter(
                organization=organization,
                status='ACTIF'
            ).first()
            
            if not subscription:
                return False
            
            # Vérifier la limite (implémentation simplifiée)
            # Dans une vraie implémentation, on calculerait l'usage actuel
            current_usage = 0  # À remplacer par le vrai calcul
            
            return subscription.check_limit(self.limit_type, current_usage)
            
        except Organization.DoesNotExist:
            return False


class DynamicPermission(permissions.BasePermission):
    
    def __init__(self, required_permission):
        self.required_permission = required_permission
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False
        
        try:
            organization = Organization.objects.get(id=org_id)
            
            # Propriétaire a toutes les permissions
            if organization.owner == request.user:
                return True
            
            # Vérifier les permissions du membre
            try:
                member = OrganizationMember.objects.get(
                    organization=organization,
                    user=request.user,
                    status='ACTIVE'
                )
                
                # Vérifier si la permission est dans la liste des permissions du membre
                member_permissions = member.permissions or []
                return self.required_permission in member_permissions
                
            except OrganizationMember.DoesNotExist:
                return False
                
        except Organization.DoesNotExist:
            return False
