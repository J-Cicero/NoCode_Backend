"""
Tâches Celery pour la gestion de la vérification des entreprises.
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from ..models import DocumentVerification, DocumentUpload, Organization
from ..services.verification_service import VerificationService
from ..services.event_bus import EventBus
from .email_tasks import send_billing_notification

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_document_verification(self, document_upload_id):
    """
    Traite la vérification d'un document uploadé.
    """
    try:
        document = DocumentUpload.objects.get(id=document_upload_id)
        verification_service = VerificationService()
        
        # Analyser le document
        result = verification_service.analyze_document(document_upload_id)
        
        if not result.success:
            logger.error(f"Erreur lors de l'analyse du document: {result.error}")
            return {'success': False, 'error': result.error}
        
        # Mettre à jour le statut
        document.status = 'ANALYZED'
        document.analysis_result = result.data.get('analysis', {})
        document.save()
        
        EventBus.publish('document.analyzed', {
            'document_id': document_upload_id,
            'verification_id': document.verification.id,
            'entreprise_id': document.verification.entreprise.id,
        })
        
        logger.info(f"Document {document_upload_id} analysé avec succès")
        return {'success': True, 'analysis': result.data}
        
    except DocumentUpload.DoesNotExist:
        logger.error(f"Document {document_upload_id} non trouvé")
        return {'success': False, 'error': 'Document not found'}
    
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse du document: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def send_verification_status_update(self, verification_id, status):
    """
    Envoie une notification de mise à jour du statut de vérification.
    """
    try:
        verification = DocumentVerification.objects.get(id=verification_id)
        entreprise = verification.entreprise
        
        # Préparer le contexte selon le statut
        context = {
            'entreprise': entreprise,
            'verification': verification,
            'status': status,
        }
        
        # Déterminer le type de notification
        notification_types = {
            'APPROVED': 'verification_approved',
            'REJECTED': 'verification_rejected',
            'PENDING_REVIEW': 'verification_pending',
        }
        
        notification_type = notification_types.get(status)
        if not notification_type:
            logger.warning(f"Type de statut de vérification inconnu: {status}")
            return {'success': False, 'error': 'Unknown status'}
        
        # Envoyer l'email (réutiliser la fonction de notification)
        send_billing_notification.delay(
            notification_type,
            entreprise.user.id,  # Utiliser l'ID utilisateur comme organisation
            **context
        )
        
        EventBus.publish('verification.status_notified', {
            'verification_id': verification_id,
            'entreprise_id': entreprise.id,
            'status': status,
        })
        
        logger.info(f"Notification de vérification envoyée pour {verification_id}")
        return {'success': True}
        
    except DocumentVerification.DoesNotExist:
        logger.error(f"Vérification {verification_id} non trouvée")
        return {'success': False, 'error': 'Verification not found'}
    
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de la notification: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_expired_verifications():
    """
    Nettoie les vérifications expirées.
    """
    try:
        # Supprimer les vérifications abandonnées depuis plus de 30 jours
        expiry_date = timezone.now() - timedelta(days=30)
        
        expired_verifications = DocumentVerification.objects.filter(
            status='PENDING',
            date_creation__lt=expiry_date,
        )
        
        count = expired_verifications.count()
        
        # Marquer comme expirées plutôt que supprimer
        expired_verifications.update(status='EXPIRED')
        
        EventBus.publish('verifications.cleanup', {
            'expired_count': count,
        })
        
        logger.info(f"Nettoyage des vérifications: {count} vérifications expirées")
        return {'success': True, 'expired_count': count}
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des vérifications: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def auto_approve_simple_verifications():
    """
    Approuve automatiquement les vérifications simples.
    """
    try:
        # Récupérer les vérifications en attente avec tous les documents analysés
        pending_verifications = DocumentVerification.objects.filter(
            status='PENDING_REVIEW'
        )
        
        auto_approved = 0
        
        for verification in pending_verifications:
            # Vérifier si tous les documents sont valides
            documents = verification.documents.all()
            
            if not documents.exists():
                continue
            
            all_valid = all(
                doc.status == 'APPROVED' and 
                doc.analysis_result.get('confidence', 0) > 0.8
                for doc in documents
            )
            
            if all_valid:
                # Auto-approuver
                verification.status = 'APPROVED'
                verification.reviewed_by = None  # Auto-approval
                verification.date_review = timezone.now()
                verification.save()
                
                # Mettre à jour l'entreprise
                verification.entreprise.verification_status = 'VERIFIED'
                verification.entreprise.is_verified = True
                verification.entreprise.save()
                
                # Envoyer une notification
                send_verification_status_update.delay(verification.id, 'APPROVED')
                
                auto_approved += 1
        
        logger.info(f"Auto-approbation: {auto_approved} vérifications approuvées")
        return {'success': True, 'auto_approved': auto_approved}
        
    except Exception as e:
        logger.error(f"Erreur lors de l'auto-approbation: {e}")
        return {'success': False, 'error': str(e)}
