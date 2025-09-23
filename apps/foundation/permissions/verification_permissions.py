"""
Permissions spécialisées pour la vérification des entreprises.
Gère les permissions liées au processus KYB et à l'upload de documents.
"""
from rest_framework import permissions
from django.contrib.auth import get_user_model
from ..models import Entreprise, DocumentVerification, DocumentUpload


User = get_user_model()


class CanStartVerification(permissions.BasePermission):
    """
    Permission pour démarrer un processus de vérification.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        entreprise_id = view.kwargs.get('entreprise_id')
        if not entreprise_id:
            return False
        
        try:
            entreprise = Entreprise.objects.get(id=entreprise_id)
            
            # Seul le propriétaire de l'entreprise peut démarrer la vérification
            return entreprise.user == request.user
            
        except Entreprise.DoesNotExist:
            return False


class CanViewVerificationStatus(permissions.BasePermission):
    """
    Permission pour consulter le statut de vérification.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        entreprise_id = view.kwargs.get('entreprise_id')
        if not entreprise_id:
            return False
        
        try:
            entreprise = Entreprise.objects.get(id=entreprise_id)
            
            # Le propriétaire peut voir le statut, les staff aussi
            return entreprise.user == request.user or request.user.is_staff
            
        except Entreprise.DoesNotExist:
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
            
            # Seul le propriétaire de l'entreprise peut uploader des documents
            return verification.entreprise.user == request.user
            
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


class IsVerifiedEntreprise(permissions.BasePermission):
    """
    Permission pour vérifier qu'une entreprise est vérifiée.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.user_type != 'ENTREPRISE':
            return False
        
        try:
            entreprise = request.user.entreprise
            return entreprise.is_verified
        except Entreprise.DoesNotExist:
            return False


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
            # Le propriétaire de l'entreprise ou les staff peuvent accéder
            return (obj.entreprise.user == request.user or 
                   request.user.is_staff)
        
        elif isinstance(obj, DocumentUpload):
            # Le propriétaire de l'entreprise ou les staff peuvent accéder
            return (obj.verification.entreprise.user == request.user or 
                   request.user.is_staff)
        
        return False


class VerificationStatusPermission(permissions.BasePermission):
    """
    Permission basée sur le statut de vérification de l'entreprise.
    """
    
    def __init__(self, required_status='VERIFIED'):
        self.required_status = required_status
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.user_type != 'ENTREPRISE':
            return False
        
        try:
            entreprise = request.user.entreprise
            return entreprise.verification_status == self.required_status
        except Entreprise.DoesNotExist:
            return False
