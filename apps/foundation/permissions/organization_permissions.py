"""
Permissions spécialisées pour les organisations.
Gère les permissions complexes liées aux organisations et leurs membres.
"""
from rest_framework import permissions
from django.contrib.auth import get_user_model
from ..models import Organization, OrganizationMember, OrganizationInvitation


User = get_user_model()


class OrganizationPermission(permissions.BasePermission):

    # Mapping des actions vers les rôles requis
    ROLE_PERMISSIONS = {
        'create': [],  # Tout utilisateur authentifié peut créer une organisation
        'list': [],    # Tout utilisateur authentifié peut lister ses organisations
        'retrieve': ['MEMBER', 'ADMIN', 'OWNER'],
        'update': ['ADMIN', 'OWNER'],
        'partial_update': ['ADMIN', 'OWNER'],
        'destroy': ['OWNER'],
        'transfer_ownership': ['OWNER'],
        'leave': ['MEMBER', 'ADMIN'],  # OWNER ne peut pas quitter sans transférer
    }
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        action = getattr(view, 'action', None)
        
        # Actions qui ne nécessitent pas d'organisation spécifique
        if action in ['create', 'list']:
            return True
        
        return True  # Vérification détaillée dans has_object_permission
    
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Organization):
            return False
        
        action = getattr(view, 'action', None)
        required_roles = self.ROLE_PERMISSIONS.get(action, ['OWNER'])
        
        # Le propriétaire a tous les droits
        if obj.owner == request.user:
            return True
        
        # Vérifier le rôle du membre
        try:
            member = OrganizationMember.objects.get(
                organization=obj,
                user=request.user,
                status='ACTIVE'
            )
            
            # Cas spécial pour leave - OWNER ne peut pas quitter sans transférer
            if action == 'leave' and member.role == 'OWNER':
                return False
            
            return member.role in required_roles or 'MEMBER' in required_roles
            
        except OrganizationMember.DoesNotExist:
            return False


class OrganizationMemberPermission(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False
        
        try:
            organization = Organization.objects.get(id=org_id)
            
            # Vérifier que l'utilisateur est membre de l'organisation
            return OrganizationMember.objects.filter(
                organization=organization,
                user=request.user,
                status='ACTIVE'
            ).exists()
            
        except Organization.DoesNotExist:
            return False
    
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, OrganizationMember):
            return False
        
        organization = obj.organization
        action = getattr(view, 'action', None)
        
        # Le propriétaire peut tout faire
        if organization.owner == request.user:
            return True
        
        try:
            current_member = OrganizationMember.objects.get(
                organization=organization,
                user=request.user,
                status='ACTIVE'
            )
            
            # Actions selon le rôle
            if action in ['retrieve', 'list']:
                return True  # Tous les membres peuvent voir les autres membres
            
            elif action in ['update', 'partial_update', 'destroy']:
                # Seuls ADMIN et OWNER peuvent modifier/supprimer des membres
                if current_member.role not in ['ADMIN', 'OWNER']:
                    return False
                
                # Un ADMIN ne peut pas modifier un OWNER ou un autre ADMIN
                if current_member.role == 'ADMIN' and obj.role in ['OWNER', 'ADMIN']:
                    return False
                
                # On ne peut pas se supprimer soi-même (utiliser leave à la place)
                if action == 'destroy' and obj.user == request.user:
                    return False
                
                return True
            
            return False
            
        except OrganizationMember.DoesNotExist:
            return False


class OrganizationInvitationPermission(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False
        
        try:
            organization = Organization.objects.get(id=org_id)
            
            # Vérifier les permissions d'invitation
            if organization.owner == request.user:
                return True
            
            try:
                member = OrganizationMember.objects.get(
                    organization=organization,
                    user=request.user,
                    status='ACTIVE'
                )
                
                # Vérifier les paramètres d'organisation
                try:
                    settings = organization.settings
                    if settings.allow_member_invites:
                        return True  # Tous les membres peuvent inviter
                    else:
                        return member.role in ['ADMIN', 'OWNER']  # Seuls admin/owner
                except:
                    # Paramètres par défaut : seuls admin/owner peuvent inviter
                    return member.role in ['ADMIN', 'OWNER']
                    
            except OrganizationMember.DoesNotExist:
                return False
                
        except Organization.DoesNotExist:
            return False
    
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, OrganizationInvitation):
            return False
        
        organization = obj.organization
        action = getattr(view, 'action', None)
        
        # Le propriétaire peut tout faire
        if organization.owner == request.user:
            return True
        
        # L'inviteur peut gérer ses propres invitations
        if obj.invited_by == request.user:
            return action in ['retrieve', 'update', 'destroy', 'resend']
        
        try:
            member = OrganizationMember.objects.get(
                organization=organization,
                user=request.user,
                status='ACTIVE'
            )
            
            # Les admins peuvent gérer toutes les invitations
            if member.role in ['ADMIN', 'OWNER']:
                return True
            
            # Les membres peuvent seulement voir les invitations
            return action in ['retrieve', 'list']
            
        except OrganizationMember.DoesNotExist:
            return False


class CanManageOrganizationSettings(permissions.BasePermission):

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False
        
        try:
            organization = Organization.objects.get(id=org_id)
            
            # Seuls le propriétaire et les admins peuvent gérer les paramètres
            if organization.owner == request.user:
                return True
            
            try:
                member = OrganizationMember.objects.get(
                    organization=organization,
                    user=request.user,
                    status='ACTIVE'
                )
                return member.role in ['ADMIN', 'OWNER']
                
            except OrganizationMember.DoesNotExist:
                return False
                
        except Organization.DoesNotExist:
            return False


class CanViewOrganizationStats(permissions.BasePermission):

    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False
        
        try:
            organization = Organization.objects.get(id=org_id)
            
            # Propriétaire et admins peuvent voir les stats
            if organization.owner == request.user:
                return True
            
            try:
                member = OrganizationMember.objects.get(
                    organization=organization,
                    user=request.user,
                    status='ACTIVE'
                )
                return member.role in ['ADMIN', 'OWNER']
                
            except OrganizationMember.DoesNotExist:
                return False
                
        except Organization.DoesNotExist:
            return False


class OrganizationContextPermission(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False
        
        try:
            organization = Organization.objects.get(id=org_id)
            
            # Vérifier que l'utilisateur est membre
            is_member = OrganizationMember.objects.filter(
                organization=organization,
                user=request.user,
                status='ACTIVE'
            ).exists()
            
            if is_member or organization.owner == request.user:
                # Injecter l'organisation dans la requête pour utilisation ultérieure
                request.current_organization = organization
                return True
            
            return False
            
        except Organization.DoesNotExist:
            return False
