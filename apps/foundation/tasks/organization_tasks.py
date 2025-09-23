"""
Tâches Celery pour la gestion des organisations.
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from ..models import Organization, OrganizationInvitation, OrganizationMember
from ..services.organization_service import OrganizationService
from ..services.event_bus import EventBus

logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_invitations():
    """
    Nettoie les invitations expirées.
    """
    try:
        # Supprimer les invitations expirées depuis plus de 7 jours
        expiry_date = timezone.now() - timedelta(days=7)
        
        expired_invitations = OrganizationInvitation.objects.filter(
            status='SENT',
            date_creation__lt=expiry_date,
        )
        
        count = expired_invitations.count()
        
        # Marquer comme expirées
        expired_invitations.update(status='EXPIRED')
        
        EventBus.publish('invitations.cleanup', {
            'expired_count': count,
        })
        
        logger.info(f"Nettoyage des invitations: {count} invitations expirées")
        return {'success': True, 'expired_count': count}
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des invitations: {e}")
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def sync_organization_data(self, organization_id):
    """
    Synchronise les données d'une organisation.
    """
    try:
        organization = Organization.objects.get(id=organization_id)
        organization_service = OrganizationService()
        
        # Synchroniser avec les services externes (Stripe, etc.)
        result = organization_service.sync_external_data(organization_id)
        
        if not result.success:
            logger.error(f"Erreur lors de la synchronisation: {result.error}")
            return {'success': False, 'error': result.error}
        
        EventBus.publish('organization.synced', {
            'organization_id': organization_id,
        })
        
        logger.info(f"Organisation {organization_id} synchronisée")
        return {'success': True}
        
    except Organization.DoesNotExist:
        logger.error(f"Organisation {organization_id} non trouvée")
        return {'success': False, 'error': 'Organization not found'}
    
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def generate_organization_report(self, organization_id, report_type='monthly'):
    """
    Génère un rapport pour une organisation.
    """
    try:
        organization = Organization.objects.get(id=organization_id)
        organization_service = OrganizationService()
        
        # Générer le rapport
        result = organization_service.generate_report(organization_id, report_type)
        
        if not result.success:
            logger.error(f"Erreur lors de la génération du rapport: {result.error}")
            return {'success': False, 'error': result.error}
        
        EventBus.publish('organization.report_generated', {
            'organization_id': organization_id,
            'report_type': report_type,
        })
        
        logger.info(f"Rapport {report_type} généré pour l'organisation {organization_id}")
        return {'success': True, 'report': result.data}
        
    except Organization.DoesNotExist:
        logger.error(f"Organisation {organization_id} non trouvée")
        return {'success': False, 'error': 'Organization not found'}
    
    except Exception as e:
        logger.error(f"Erreur lors de la génération du rapport: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}
