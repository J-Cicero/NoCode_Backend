"""
Permissions spécialisées pour la facturation et les abonnements.
Gère les permissions liées aux paiements, factures et abonnements.
"""
from rest_framework import permissions
from django.contrib.auth import get_user_model
from ..models import Organization, OrganizationMember, Abonnement


User = get_user_model()


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


class CanViewBillingInfo(permissions.BasePermission):

    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False
        
        try:
            organization = Organization.objects.get(id=org_id)
            
            # Propriétaire et admins peuvent voir les infos de facturation
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


class CanManageSubscriptions(permissions.BasePermission):

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False
        
        try:
            organization = Organization.objects.get(id=org_id)
            
            # Seuls propriétaire et admins peuvent gérer les abonnements
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
    
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Abonnement):
            # Vérifier que l'abonnement appartient à une organisation de l'utilisateur
            organization = obj.organization
            
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
        
        return False


class CanManagePaymentMethods(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if isinstance(obj):
            # Un utilisateur peut seulement gérer ses propres moyens de paiement
            return obj.user == request.user
        
        return False


class CanViewInvoices(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False
        
        try:
            organization = Organization.objects.get(id=org_id)
            
            # Propriétaire et admins peuvent voir les factures
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
    
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Facture):
            organization = obj.organization
            
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
        
        return False


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
            return Abonnement.objects.filter(
                organization=organization,
                status='ACTIF'
            ).exists()
            
        except Organization.DoesNotExist:
            return False


class CanCreatePaymentIntent(permissions.BasePermission):

    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Vérifier l'organisation dans les données de la requête
        organization_id = request.data.get('organization_id')
        if not organization_id:
            return False
        
        try:
            organization = Organization.objects.get(id=organization_id)
            
            # Seuls propriétaire et admins peuvent créer des paiements
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


class CanGenerateInvoices(permissions.BasePermission):

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False
        
        try:
            organization = Organization.objects.get(id=org_id)
            
            # Seuls propriétaire et admins peuvent générer des factures
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


class CanViewBillingStats(permissions.BasePermission):

    def has_permission(self, request, view):
        # Seuls les staff peuvent voir les stats globales de facturation
        return request.user.is_authenticated and request.user.is_staff


class SubscriptionLimitPermission(permissions.BasePermission):

    
    def __init__(self, limit_type, current_usage_calculator=None):
        self.limit_type = limit_type
        self.current_usage_calculator = current_usage_calculator
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False
        
        try:
            organization = Organization.objects.get(id=org_id)
            
            # Récupérer l'abonnement actif
            subscription = Abonnement.objects.filter(
                organization=organization,
                status='ACTIF'
            ).first()
            
            if not subscription:
                return False
            
            # Calculer l'usage actuel
            current_usage = 0
            if self.current_usage_calculator:
                current_usage = self.current_usage_calculator(organization)
            
            # Vérifier la limite
            return subscription.check_limit(self.limit_type, current_usage)
            
        except Organization.DoesNotExist:
            return False
