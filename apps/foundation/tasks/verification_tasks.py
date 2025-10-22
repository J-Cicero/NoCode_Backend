"""
Tâches Celery pour la gestion de la vérification des organisations.
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from ..models import DocumentVerification, Organization
from ..services.event_bus import EventBus
from .email_tasks import send_billing_notification

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_verification_status_update(self, verification_id, status):
    """
    Envoie une notification de mise à jour du statut de vérification.
    """
    try:
        verification = DocumentVerification.objects.get(id=verification_id)
        organization = verification.organization
        
        # Préparer le contexte selon le statut
        context = {
            'organization': organization,
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
            organization.owner.id if organization.owner else None,
            **context
        )
        
        EventBus.publish('verification.status_notified', {
            'verification_id': verification_id,
            'organization_id': organization.id,
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
    
    Marque comme expirées les vérifications en statut PENDING depuis plus de 30 jours.
    Cette tâche doit être exécutée régulièrement via Celery Beat.
    """
    try:
        # Supprimer les vérifications abandonnées depuis plus de 30 jours
        expiry_date = timezone.now() - timedelta(days=30)
        
        expired_verifications = DocumentVerification.objects.filter(
            status='PENDING',
            created_at__lt=expiry_date,
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
