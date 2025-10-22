"""
Tâches asynchrones pour le module Runtime.

Ce module contient les tâches asynchrones pour le déploiement des applications.
"""
import logging
from celery import shared_task
from django.db import transaction

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
            if app.deployment_type == 'kubernetes':
                deployment_manager = DeploymentManager(
                    app,
                    deployment_strategy=KubernetesDeployment()
                )
            else:
                deployment_manager = DeploymentManager(
                    app,
                    deployment_strategy=LocalDeployment()
                )
            
            try:
                # Exécuter le déploiement
                result = deployment_manager.deploy()
                
                # Mettre à jour le statut
                deployment_log.status = 'completed'
                deployment_log.details = {
                    'status': 'success',
                    'message': 'Déploiement réussi',
                    'details': result
                }
                deployment_log.save(update_fields=['status', 'details', 'updated_at'])
                
                # Mettre à jour l'application
                app.status = 'deployed'
                app.api_base_url = result.get('api_url')
                app.admin_url = result.get('admin_url')
                app.save(update_fields=['status', 'api_base_url', 'admin_url', 'updated_at'])
                
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
                deployment_log.details = {
                    'status': 'error',
                    'message': str(e),
                    'error_type': type(e).__name__
                }
                deployment_log.save(update_fields=['status', 'details', 'updated_at'])
                
                # Mettre à jour l'application
                app.status = 'deployment_failed'
                app.save(update_fields=['status', 'updated_at'])
                
                # Relancer la tâche si nécessaire
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
