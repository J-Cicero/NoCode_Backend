
from rest_framework import permissions
from django.contrib.auth import get_user_model
from ..models import Organization, OrganizationMember

User = get_user_model()

class OrganizationPermission(permissions.BasePermission):

    # Mapping des actions vers les rôles requis
    ROLE_PERMISSIONS = {
        'create': [],
        'list': [],
        'retrieve': ['MEMBER', 'ADMIN', 'OWNER'],
        'update': ['ADMIN', 'OWNER'],
        'partial_update': ['ADMIN', 'OWNER'],
        'destroy': ['OWNER'],
        'transfer_ownership': ['OWNER'],
        'leave': ['MEMBER', 'ADMIN'],
    }
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        action = getattr(view, 'action', None)
        
        if action in ['create', 'list']:
            return True
        
        return True
    
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Organization):
            return False
        
        action = getattr(view, 'action', None)
        required_roles = self.ROLE_PERMISSIONS.get(action, ['OWNER'])
        
        if obj.owner == request.user:
            return True
        
        try:
            member = OrganizationMember.objects.get(
                organization=obj,
                user=request.user,
                status='ACTIVE'
            )

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
        
        if organization.owner == request.user:
            return True
        
        try:
            current_member = OrganizationMember.objects.get(
                organization=organization,
                user=request.user,
                status='ACTIVE'
            )
            
            if action in ['retrieve', 'list']:
                return True  # Tous les membres peuvent voir les autres membres
            
            elif action in ['update', 'partial_update', 'destroy']:
                if current_member.role not in ['ADMIN', 'OWNER']:
                    return False
                
                if current_member.role == 'ADMIN' and obj.role in ['OWNER', 'ADMIN']:
                    return False

                if action == 'destroy' and obj.user == request.user:
                    return False
                
                return True
            
            return False
            
        except OrganizationMember.DoesNotExist:
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
