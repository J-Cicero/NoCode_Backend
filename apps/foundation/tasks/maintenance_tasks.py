"""
Tâches Celery pour la maintenance du système Foundation.
"""
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.sessions.models import Session
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def cleanup_expired_sessions(self):
    """
    Tâche périodique pour nettoyer les sessions expirées.
    
    Cette tâche est exécutée toutes les heures pour supprimer
    les sessions expirées de la base de données.
    """
    try:
        logger.info("Début du nettoyage des sessions expirées")
        
        # Calculer la date d'expiration (24h par défaut)
        expiry_date = timezone.now() - timedelta(days=1)
        
        # Supprimer les sessions expirées
        deleted_count, _ = Session.objects.filter(expire_date__lt=expiry_date).delete()
        
        logger.info(f"Nettoyage des sessions terminé: {deleted_count} sessions supprimées")
        
        return {
            'status': 'success',
            'message': f'{deleted_count} sessions expirées supprimées',
            'deleted_count': deleted_count
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des sessions: {str(e)}", exc_info=True)
        
        # Retry avec backoff exponentiel
        if self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)  # 1min, 2min, 4min
            raise self.retry(exc=e, countdown=countdown)
        
        return {
            'status': 'error',
            'message': f'Échec du nettoyage après {self.max_retries} tentatives',
            'error': str(e)
        }


@shared_task(bind=True, max_retries=2)
def cleanup_old_audit_logs(self, days: int = 90):
    """
    Nettoie les anciens logs d'audit.
    
    Args:
        days: Nombre de jours de conservation (défaut: 90)
    """
    try:
        from ..models import AuditLog
        
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count, _ = AuditLog.objects.filter(
            created_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Nettoyage des logs d'audit: {deleted_count} entrées supprimées")
        
        return {
            'status': 'success',
            'deleted_count': deleted_count
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des logs d'audit: {str(e)}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=300)
        
        return {
            'status': 'error',
            'error': str(e)
        }


@shared_task(bind=True, max_retries=2)
def update_user_statistics(self):
    """
    Met à jour les statistiques des utilisateurs.
    """
    try:
        from django.contrib.auth import get_user_model
        from django.db.models import Count
        
        User = get_user_model()
        
        # Statistiques par organisation
        org_stats = User.objects.values('organizations__name').annotate(
            user_count=Count('id')
        ).order_by('-user_count')
        
        logger.info(f"Statistiques utilisateurs mises à jour: {list(org_stats)}")
        
        return {
            'status': 'success',
            'organization_stats': list(org_stats),
            'total_users': User.objects.count()
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des statistiques: {str(e)}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=300)
        
        return {
            'status': 'error',
            'error': str(e)
        }
