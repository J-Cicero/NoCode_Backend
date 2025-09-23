"""
Service de vérification des entreprises.
Gère le processus de vérification des documents d'entreprise et la validation KYB.
"""
import logging
from typing import Dict, List, Optional, Any
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings
from .base_service import BaseService, ServiceResult, ValidationException, BusinessLogicException, PermissionException
from .event_bus import EventBus, FoundationEvents
from ..models import (
    Entreprise, DocumentVerification, DocumentUpload, 
    Organization, OrganizationMember
)


logger = logging.getLogger(__name__)
User = get_user_model()


class VerificationService(BaseService):
    """
    Service de vérification des entreprises.
    Gère toute la logique métier liée à la vérification KYB.
    """
    
    def __init__(self, user: User = None, organization: Organization = None):
        super().__init__(user, organization)
    
    def validate_permissions(self, required_permissions: List[str] = None):
        """Valide les permissions pour les opérations de vérification."""
        super().validate_permissions(required_permissions)
        
        if required_permissions:
            if 'manage_verification' in required_permissions:
                if not self.organization or not self.can_manage_verification():
                    raise PermissionException("Permission de gestion de vérification requise")
    
    def can_manage_verification(self) -> bool:
        """Vérifie si l'utilisateur peut gérer la vérification."""
        if not self.user or not self.organization:
            return False
        
        try:
            member = OrganizationMember.objects.get(
                organization=self.organization,
                user=self.user,
                status='ACTIVE'
            )
            return member.role in ['OWNER', 'ADMIN']
        except OrganizationMember.DoesNotExist:
            return False
    
    def start_verification_process(self, entreprise_id: int) -> ServiceResult:
        """
        Démarre le processus de vérification pour une entreprise.
        """
        try:
            # Récupérer l'entreprise
            try:
                entreprise = Entreprise.objects.get(id=entreprise_id)
            except Entreprise.DoesNotExist:
                return ServiceResult.error_result("Entreprise introuvable")
            
            # Vérifier les permissions
            if self.user != entreprise.user:
                raise PermissionException("Vous ne pouvez pas vérifier cette entreprise")
            
            # Vérifier si une vérification est déjà en cours
            existing_verification = DocumentVerification.objects.filter(
                entreprise=entreprise,
                status__in=['EN_ATTENTE', 'EN_COURS']
            ).first()
            
            if existing_verification:
                return ServiceResult.error_result("Une vérification est déjà en cours pour cette entreprise")
            
            # Vérifier si l'entreprise est déjà vérifiée
            if entreprise.verification_status == 'VERIFIED':
                return ServiceResult.error_result("Cette entreprise est déjà vérifiée")
            
            with transaction.atomic():
                # Créer une nouvelle demande de vérification
                verification = DocumentVerification.objects.create(
                    entreprise=entreprise,
                    status='EN_ATTENTE',
                    submitted_by=self.user,
                    metadata={
                        'started_at': timezone.now().isoformat(),
                        'user_id': self.user.id,
                        'entreprise_data': {
                            'nom': entreprise.nom,
                            'siret': entreprise.siret,
                            'forme_juridique': entreprise.forme_juridique,
                            'secteur_activite': entreprise.secteur_activite,
                        }
                    }
                )
                
                # Mettre à jour le statut de l'entreprise
                entreprise.verification_status = 'PENDING'
                entreprise.save(update_fields=['verification_status'])
                
                # Publier l'événement
                EventBus.publish(FoundationEvents.VERIFICATION_STARTED, {
                    'verification_id': verification.id,
                    'entreprise_id': entreprise.id,
                    'user_id': self.user.id,
                    'siret': entreprise.siret,
                })
                
                self.log_activity('verification_started', {
                    'verification_id': verification.id,
                    'entreprise_id': entreprise.id,
                })
                
                return ServiceResult.success_result({
                    'verification': {
                        'id': verification.id,
                        'status': verification.status,
                        'created_at': verification.created_at.isoformat(),
                        'required_documents': self._get_required_documents(entreprise),
                    },
                    'entreprise': {
                        'id': entreprise.id,
                        'verification_status': entreprise.verification_status,
                    }
                })
                
        except PermissionException as e:
            return ServiceResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Erreur lors du démarrage de la vérification: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors du démarrage de la vérification")
    
    def upload_document(self, verification_id: int, document_type: str, 
                       file: UploadedFile, description: str = '') -> ServiceResult:
        """
        Upload un document pour la vérification.
        """
        try:
            # Récupérer la vérification
            try:
                verification = DocumentVerification.objects.get(id=verification_id)
            except DocumentVerification.DoesNotExist:
                return ServiceResult.error_result("Vérification introuvable")
            
            # Vérifier les permissions
            if self.user != verification.entreprise.user:
                raise PermissionException("Vous ne pouvez pas uploader de documents pour cette vérification")
            
            # Vérifier si la vérification accepte encore des documents
            if verification.status not in ['EN_ATTENTE', 'EN_COURS', 'DOCUMENTS_REQUIS']:
                return ServiceResult.error_result("Cette vérification n'accepte plus de documents")
            
            # Valider le type de document
            valid_types = [
                'KBIS', 'STATUTS', 'PIECE_IDENTITE_DIRIGEANT', 
                'JUSTIFICATIF_DOMICILE', 'RIB', 'AUTRE'
            ]
            if document_type not in valid_types:
                return ServiceResult.error_result(f"Type de document invalide. Types acceptés: {', '.join(valid_types)}")
            
            # Valider le fichier
            validation_result = self._validate_uploaded_file(file)
            if not validation_result['valid']:
                return ServiceResult.error_result(validation_result['error'])
            
            with transaction.atomic():
                # Créer l'upload de document
                document_upload = DocumentUpload.objects.create(
                    verification=verification,
                    document_type=document_type,
                    file=file,
                    original_filename=file.name,
                    file_size=file.size,
                    mime_type=validation_result['mime_type'],
                    description=description,
                    uploaded_by=self.user,
                    status='EN_ATTENTE',
                )
                
                # Mettre à jour le statut de la vérification si nécessaire
                if verification.status == 'EN_ATTENTE':
                    verification.status = 'EN_COURS'
                    verification.save(update_fields=['status'])
                
                # Publier l'événement
                EventBus.publish(FoundationEvents.DOCUMENT_UPLOADED, {
                    'verification_id': verification.id,
                    'document_id': document_upload.id,
                    'document_type': document_type,
                    'entreprise_id': verification.entreprise.id,
                    'user_id': self.user.id,
                })
                
                self.log_activity('document_uploaded', {
                    'verification_id': verification.id,
                    'document_id': document_upload.id,
                    'document_type': document_type,
                    'filename': file.name,
                })
                
                return ServiceResult.success_result({
                    'document': {
                        'id': document_upload.id,
                        'type': document_upload.document_type,
                        'filename': document_upload.original_filename,
                        'size': document_upload.file_size,
                        'status': document_upload.status,
                        'uploaded_at': document_upload.created_at.isoformat(),
                    },
                    'verification': {
                        'id': verification.id,
                        'status': verification.status,
                        'documents_count': verification.documents.count(),
                    }
                })
                
        except PermissionException as e:
            return ServiceResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Erreur lors de l'upload de document: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de l'upload du document")
    
    def review_document(self, document_id: int, status: str, 
                       reviewer_comments: str = '') -> ServiceResult:
        """
        Révise un document uploadé (pour les administrateurs).
        """
        try:
            # Récupérer le document
            try:
                document = DocumentUpload.objects.get(id=document_id)
            except DocumentUpload.DoesNotExist:
                return ServiceResult.error_result("Document introuvable")
            
            # Vérifier les permissions (seuls les staff peuvent réviser)
            if not self.user.is_staff:
                raise PermissionException("Seuls les administrateurs peuvent réviser les documents")
            
            # Valider le statut
            valid_statuses = ['APPROUVE', 'REJETE', 'DOCUMENTS_REQUIS']
            if status not in valid_statuses:
                return ServiceResult.error_result(f"Statut invalide. Statuts acceptés: {', '.join(valid_statuses)}")
            
            with transaction.atomic():
                # Mettre à jour le document
                document.status = status
                document.reviewer_comments = reviewer_comments
                document.reviewed_by = self.user
                document.reviewed_at = timezone.now()
                document.save(update_fields=[
                    'status', 'reviewer_comments', 'reviewed_by', 'reviewed_at'
                ])
                
                # Vérifier si tous les documents requis sont approuvés
                verification = document.verification
                self._check_verification_completion(verification)
                
                # Publier l'événement
                EventBus.publish(FoundationEvents.DOCUMENT_REVIEWED, {
                    'verification_id': verification.id,
                    'document_id': document.id,
                    'document_type': document.document_type,
                    'status': status,
                    'reviewer_id': self.user.id,
                    'entreprise_id': verification.entreprise.id,
                })
                
                self.log_activity('document_reviewed', {
                    'verification_id': verification.id,
                    'document_id': document.id,
                    'status': status,
                    'reviewer_comments': reviewer_comments,
                })
                
                return ServiceResult.success_result({
                    'document': {
                        'id': document.id,
                        'status': document.status,
                        'reviewer_comments': document.reviewer_comments,
                        'reviewed_at': document.reviewed_at.isoformat(),
                        'reviewed_by': document.reviewed_by.full_name,
                    },
                    'verification': {
                        'id': verification.id,
                        'status': verification.status,
                    }
                })
                
        except PermissionException as e:
            return ServiceResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Erreur lors de la révision de document: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la révision du document")
    
    def complete_verification(self, verification_id: int, final_status: str, 
                            admin_comments: str = '') -> ServiceResult:
        """
        Finalise une vérification (pour les administrateurs).
        """
        try:
            # Récupérer la vérification
            try:
                verification = DocumentVerification.objects.get(id=verification_id)
            except DocumentVerification.DoesNotExist:
                return ServiceResult.error_result("Vérification introuvable")
            
            # Vérifier les permissions
            if not self.user.is_staff:
                raise PermissionException("Seuls les administrateurs peuvent finaliser les vérifications")
            
            # Valider le statut final
            valid_statuses = ['APPROUVE', 'REJETE']
            if final_status not in valid_statuses:
                return ServiceResult.error_result(f"Statut final invalide. Statuts acceptés: {', '.join(valid_statuses)}")
            
            with transaction.atomic():
                # Mettre à jour la vérification
                verification.status = final_status
                verification.admin_comments = admin_comments
                verification.reviewed_by = self.user
                verification.reviewed_at = timezone.now()
                
                if final_status == 'APPROUVE':
                    verification.approved_at = timezone.now()
                
                verification.save(update_fields=[
                    'status', 'admin_comments', 'reviewed_by', 'reviewed_at', 'approved_at'
                ])
                
                # Mettre à jour le statut de l'entreprise
                entreprise = verification.entreprise
                if final_status == 'APPROUVE':
                    entreprise.verification_status = 'VERIFIED'
                    entreprise.verified_at = timezone.now()
                else:
                    entreprise.verification_status = 'REJECTED'
                
                entreprise.save(update_fields=['verification_status', 'verified_at'])
                
                # Publier l'événement approprié
                if final_status == 'APPROUVE':
                    EventBus.publish(FoundationEvents.VERIFICATION_APPROVED, {
                        'verification_id': verification.id,
                        'entreprise_id': entreprise.id,
                        'user_id': entreprise.user.id,
                        'reviewer_id': self.user.id,
                        'approved_at': verification.approved_at.isoformat(),
                    })
                else:
                    EventBus.publish(FoundationEvents.VERIFICATION_REJECTED, {
                        'verification_id': verification.id,
                        'entreprise_id': entreprise.id,
                        'user_id': entreprise.user.id,
                        'reviewer_id': self.user.id,
                        'reason': admin_comments,
                    })
                
                self.log_activity('verification_completed', {
                    'verification_id': verification.id,
                    'final_status': final_status,
                    'entreprise_id': entreprise.id,
                })
                
                return ServiceResult.success_result({
                    'verification': {
                        'id': verification.id,
                        'status': verification.status,
                        'reviewed_at': verification.reviewed_at.isoformat(),
                        'admin_comments': verification.admin_comments,
                    },
                    'entreprise': {
                        'id': entreprise.id,
                        'verification_status': entreprise.verification_status,
                        'verified_at': entreprise.verified_at.isoformat() if entreprise.verified_at else None,
                    }
                })
                
        except PermissionException as e:
            return ServiceResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Erreur lors de la finalisation de vérification: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la finalisation de la vérification")
    
    def get_verification_status(self, entreprise_id: int) -> ServiceResult:
        """
        Récupère le statut de vérification d'une entreprise.
        """
        try:
            # Récupérer l'entreprise
            try:
                entreprise = Entreprise.objects.get(id=entreprise_id)
            except Entreprise.DoesNotExist:
                return ServiceResult.error_result("Entreprise introuvable")
            
            # Vérifier les permissions
            if self.user != entreprise.user and not self.user.is_staff:
                raise PermissionException("Vous ne pouvez pas consulter cette vérification")
            
            # Récupérer la vérification en cours ou la plus récente
            verification = DocumentVerification.objects.filter(
                entreprise=entreprise
            ).order_by('-created_at').first()
            
            verification_data = None
            if verification:
                # Récupérer les documents
                documents = verification.documents.all().order_by('-created_at')
                documents_data = []
                
                for doc in documents:
                    documents_data.append({
                        'id': doc.id,
                        'type': doc.document_type,
                        'filename': doc.original_filename,
                        'status': doc.status,
                        'uploaded_at': doc.created_at.isoformat(),
                        'reviewed_at': doc.reviewed_at.isoformat() if doc.reviewed_at else None,
                        'reviewer_comments': doc.reviewer_comments,
                    })
                
                verification_data = {
                    'id': verification.id,
                    'status': verification.status,
                    'created_at': verification.created_at.isoformat(),
                    'reviewed_at': verification.reviewed_at.isoformat() if verification.reviewed_at else None,
                    'approved_at': verification.approved_at.isoformat() if verification.approved_at else None,
                    'admin_comments': verification.admin_comments,
                    'documents': documents_data,
                    'required_documents': self._get_required_documents(entreprise),
                    'completion_percentage': self._calculate_completion_percentage(verification),
                }
            
            return ServiceResult.success_result({
                'entreprise': {
                    'id': entreprise.id,
                    'nom': entreprise.nom,
                    'siret': entreprise.siret,
                    'verification_status': entreprise.verification_status,
                    'verified_at': entreprise.verified_at.isoformat() if entreprise.verified_at else None,
                },
                'verification': verification_data,
                'can_start_verification': (
                    not verification or verification.status in ['REJETE', 'EXPIRE']
                ) and entreprise.verification_status != 'VERIFIED',
            })
            
        except PermissionException as e:
            return ServiceResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la récupération du statut de vérification")
    
    def _get_required_documents(self, entreprise: Entreprise) -> List[Dict]:
        """Retourne la liste des documents requis selon le type d'entreprise."""
        required_docs = [
            {
                'type': 'KBIS',
                'name': 'Extrait Kbis',
                'description': 'Extrait Kbis de moins de 3 mois',
                'required': True,
            },
            {
                'type': 'STATUTS',
                'name': 'Statuts de l\'entreprise',
                'description': 'Statuts signés et datés',
                'required': True,
            },
            {
                'type': 'PIECE_IDENTITE_DIRIGEANT',
                'name': 'Pièce d\'identité du dirigeant',
                'description': 'Carte d\'identité ou passeport en cours de validité',
                'required': True,
            },
            {
                'type': 'RIB',
                'name': 'RIB de l\'entreprise',
                'description': 'Relevé d\'identité bancaire au nom de l\'entreprise',
                'required': True,
            },
        ]
        
        # Ajouter des documents spécifiques selon la forme juridique
        if entreprise.forme_juridique in ['SAS', 'SARL']:
            required_docs.append({
                'type': 'JUSTIFICATIF_DOMICILE',
                'name': 'Justificatif de domicile du dirigeant',
                'description': 'Facture ou quittance de moins de 3 mois',
                'required': False,
            })
        
        return required_docs
    
    def _validate_uploaded_file(self, file: UploadedFile) -> Dict:
        """Valide un fichier uploadé."""
        # Taille maximale (10 MB)
        max_size = 10 * 1024 * 1024
        if file.size > max_size:
            return {
                'valid': False,
                'error': 'Le fichier est trop volumineux (maximum 10 MB)'
            }
        
        # Types MIME autorisés
        allowed_types = [
            'application/pdf',
            'image/jpeg',
            'image/png',
            'image/gif',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        ]
        
        # Détecter le type MIME (simplifié)
        mime_type = 'application/octet-stream'
        if file.name.lower().endswith('.pdf'):
            mime_type = 'application/pdf'
        elif file.name.lower().endswith(('.jpg', '.jpeg')):
            mime_type = 'image/jpeg'
        elif file.name.lower().endswith('.png'):
            mime_type = 'image/png'
        elif file.name.lower().endswith('.gif'):
            mime_type = 'image/gif'
        
        if mime_type not in allowed_types:
            return {
                'valid': False,
                'error': 'Type de fichier non autorisé. Formats acceptés: PDF, JPEG, PNG, GIF, DOC, DOCX'
            }
        
        return {
            'valid': True,
            'mime_type': mime_type
        }
    
    def _check_verification_completion(self, verification: DocumentVerification):
        """Vérifie si une vérification peut être considérée comme complète."""
        required_docs = self._get_required_documents(verification.entreprise)
        required_types = [doc['type'] for doc in required_docs if doc['required']]
        
        # Vérifier si tous les documents requis sont approuvés
        approved_docs = verification.documents.filter(status='APPROUVE')
        approved_types = list(approved_docs.values_list('document_type', flat=True))
        
        missing_types = set(required_types) - set(approved_types)
        
        if not missing_types:
            # Tous les documents requis sont approuvés
            verification.status = 'PRET_POUR_VALIDATION'
            verification.save(update_fields=['status'])
            
            # Publier un événement pour notifier qu'elle est prête
            EventBus.publish(FoundationEvents.VERIFICATION_READY, {
                'verification_id': verification.id,
                'entreprise_id': verification.entreprise.id,
                'user_id': verification.entreprise.user.id,
            })
    
    def _calculate_completion_percentage(self, verification: DocumentVerification) -> int:
        """Calcule le pourcentage de completion d'une vérification."""
        required_docs = self._get_required_documents(verification.entreprise)
        required_count = len([doc for doc in required_docs if doc['required']])
        
        if required_count == 0:
            return 100
        
        approved_count = verification.documents.filter(status='APPROUVE').count()
        return min(100, int((approved_count / required_count) * 100))
