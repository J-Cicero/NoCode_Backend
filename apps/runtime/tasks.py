"""
Tâches asynchrones pour le module Runtime.

Ce module contient les tâches asynchrones pour le déploiement des applications.
"""
import logging
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from .models import DeploymentLog, GeneratedApp
from .services import DeploymentManager, KubernetesDeployment, LocalDeployment

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def deploy_app_task(self, deployment_log_id):
   
    try:
        with transaction.atomic():
            # Récupérer le journal de déploiement
            deployment_log = DeploymentLog.objects.select_for_update().get(
                id=deployment_log_id,
                status__in=['pending', 'in_progress']
            )
            
            # Mettre à jour le statut
            deployment_log.status = 'in_progress'
            deployment_log.save(update_fields=['status', 'updated_at'])

            # Récupérer l'application associée
            app = deployment_log.app

            # Initialiser le gestionnaire de déploiement
            # - production => kubernetes
            # - local/staging => local
            strategy = KubernetesDeployment() if app.deployment_target == 'production' else LocalDeployment()
            deployment_manager = DeploymentManager(app, deployment_strategy=strategy)
            
            try:
                # Exécuter le déploiement
                result = deployment_manager.deploy()
                
                # Normaliser résultat
                payload = result if isinstance(result, dict) else {}

                # Mettre à jour le statut
                deployment_log.status = 'completed'
                deployment_log.completed_at = deployment_log.completed_at or timezone.now()
                deployment_log.details = payload or {'status': 'success'}
                deployment_log.error_message = ''
                deployment_log.save(update_fields=['status', 'completed_at', 'details', 'error_message', 'updated_at'])

                # Mettre à jour l'application
                app.status = 'deployed'
                if isinstance(payload, dict):
                    app.api_base_url = payload.get('api_url', app.api_base_url)
                    app.admin_url = payload.get('admin_url', app.admin_url)
                app.last_deployed_at = deployment_log.completed_at
                app.save(update_fields=['status', 'api_base_url', 'admin_url', 'last_deployed_at', 'updated_at'])
                
                return {
                    'status': 'success',
                    'message': 'Déploiement réussi',
                    'deployment_id': str(deployment_log.id),
                    'app_id': str(app.id)
                }
                
            except Exception as e:
                # En cas d'erreur, mettre à jour le statut et relancer la tâche
                logger.error(f"Erreur lors du déploiement: {str(e)}", exc_info=True)
                
                deployment_log.status = 'failed'
                deployment_log.completed_at = timezone.now()
                deployment_log.error_message = str(e)
                deployment_log.details = {
                    'status': 'error',
                    'message': str(e),
                    'error_type': type(e).__name__
                }
                deployment_log.save(update_fields=['status', 'completed_at', 'details', 'error_message', 'updated_at'])

                # Mettre à jour l'application
                app.status = 'deployment_failed'
                app.save(update_fields=['status', 'updated_at'])
                
                # Relancer la tâche si nécessaire (désactivé en tests/eager pour éviter rollback)
                if not getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
                    if self.request.retries < self.max_retries:
                        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
                
                return {
                    'status': 'error',
                    'message': 'Échec du déploiement après plusieurs tentatives',
                    'error': str(e),
                    'deployment_id': str(deployment_log.id),
                    'app_id': str(app.id)
                }
                
    except DeploymentLog.DoesNotExist:
        logger.error(f"Journal de déploiement non trouvé: {deployment_log_id}")
        return {
            'status': 'error',
            'message': f'Journal de déploiement non trouvé: {deployment_log_id}'
        }
    except Exception as e:
        logger.error(f"Erreur inattendue lors du déploiement: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'message': 'Erreur inattendue lors du déploiement',
            'error': str(e)
        }
