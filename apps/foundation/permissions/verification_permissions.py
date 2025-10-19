"""
Permissions spécialisées pour la vérification des organisations.
Gère les permissions liées au processus KYB et à l'upload de documents.
"""
from rest_framework import permissions
from django.contrib.auth import get_user_model
from ..models import DocumentVerification, DocumentUpload, Organization, OrganizationMember


User = get_user_model()


class CanStartVerification(permissions.BasePermission):
    """
    Permission pour démarrer un processus de vérification.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        organization_id = view.kwargs.get('organization_id')
        if not organization_id:
            return False
        
        try:
            organization = Organization.objects.get(id=organization_id)
            
            # Seul le propriétaire ou admin de l'organisation peut démarrer la vérification
            return organization.members.filter(user=request.user, role__in=['OWNER', 'ADMIN']).exists()
            
        except Organization.DoesNotExist:
            return False


class CanViewVerificationStatus(permissions.BasePermission):
    """
    Permission pour consulter le statut de vérification.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        organization_id = view.kwargs.get('organization_id')
        if not organization_id:
            return False
        
        try:
            organization = Organization.objects.get(id=organization_id)
            
            # Le propriétaire ou admin peut voir le statut, les staff aussi
            return (organization.members.filter(user=request.user, role__in=['OWNER', 'ADMIN']).exists() or 
                   request.user.is_staff)
            
        except Organization.DoesNotExist:
            return False


class CanUploadDocuments(permissions.BasePermission):
    """
    Permission pour uploader des documents de vérification.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        verification_id = view.kwargs.get('verification_id')
        if not verification_id:
            return False
        
        try:
            verification = DocumentVerification.objects.get(id=verification_id)
            
            # Seul les membres de l'organisation peuvent uploader des documents
            return verification.organization.members.filter(user=request.user).exists()
            
        except DocumentVerification.DoesNotExist:
            return False


class CanReviewDocuments(permissions.BasePermission):
    """
    Permission pour réviser des documents (admin seulement).
    """
    
    def has_permission(self, request, view):
        # Seuls les staff peuvent réviser les documents
        return request.user.is_authenticated and request.user.is_staff
    
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, DocumentUpload):
            # Les staff peuvent réviser tous les documents
            return request.user.is_staff
        
        return False


class CanCompleteVerification(permissions.BasePermission):
    """
    Permission pour finaliser une vérification (admin seulement).
    """
    
    def has_permission(self, request, view):
        # Seuls les staff peuvent finaliser les vérifications
        return request.user.is_authenticated and request.user.is_staff
    
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, DocumentVerification):
            # Les staff peuvent finaliser toutes les vérifications
            return request.user.is_staff
        
        return False


class CanViewPendingVerifications(permissions.BasePermission):
    """
    Permission pour voir les vérifications en attente (admin seulement).
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff


class CanViewVerificationStats(permissions.BasePermission):
    """
    Permission pour consulter les statistiques de vérification (admin seulement).
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff


class IsVerifiedOrganization(permissions.BasePermission):
    """
    Permission pour vérifier qu'une organisation est vérifiée.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.user_type not in ['BUSINESS', 'ENTREPRISE']:
            return False
        
        # Récupérer les organisations de l'utilisateur
        user_organizations = Organization.objects.filter(
            members__user=request.user,
            members__status='ACTIVE',
            is_verified=True
        )
        
        return user_organizations.exists()


class CanAccessVerificationData(permissions.BasePermission):
    """
    Permission pour accéder aux données de vérification.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        return True  # Vérification détaillée dans has_object_permission
    
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, DocumentVerification):
            # Les membres de l'organisation ou les staff peuvent accéder
            return (obj.organization.members.filter(user=request.user).exists() or 
                   request.user.is_staff)
        
        elif isinstance(obj, DocumentUpload):
            # Les membres de l'organisation ou les staff peuvent accéder
            return (obj.verification.organization.members.filter(user=request.user).exists() or 
                   request.user.is_staff)
        
        return False


class VerificationStatusPermission(permissions.BasePermission):
    """
    Permission basée sur le statut de vérification de l'organisation.
    """
    
    def __init__(self, required_status='VERIFIED'):
        self.required_status = required_status
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.user_type not in ['BUSINESS', 'ENTREPRISE']:
            return False
        
        # Récupérer les organisations de l'utilisateur
        user_organizations = Organization.objects.filter(
            members__user=request.user,
            members__status='ACTIVE'
        )
        
        # Vérifier si au moins une organisation a le statut requis
        for org in user_organizations:
            if org.is_verified == (self.required_status == 'VERIFIED'):
                return True
        
        return False
