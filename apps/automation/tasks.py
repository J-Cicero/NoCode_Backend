"""
Tâches asynchrones Celery pour le module Automation
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def execute_workflow_async(self, workflow_id: str, input_data: dict = None, user_id: int = None):
    """
    Exécute un workflow de manière asynchrone.
    
    Args:
        workflow_id: ID du workflow à exécuter
        input_data: Données d'entrée
        user_id: ID de l'utilisateur qui a déclenché l'exécution
    """
    from .models import Workflow
    from .services import WorkflowEngine
    from apps.foundation.models import User
    
    try:
        # Récupérer le workflow
        workflow = Workflow.objects.get(id=workflow_id)
        
        # Récupérer l'utilisateur si fourni
        triggered_by = None
        if user_id:
            triggered_by = User.objects.get(id=user_id)
        
        # Créer et exécuter le moteur
        engine = WorkflowEngine(workflow)
        execution = engine.execute(
            input_data=input_data or {},
            triggered_by=triggered_by
        )
        
        logger.info(f"Workflow {workflow.name} exécuté avec succès, ID: {execution.id}")
        
        return {
            'success': True,
            'execution_id': str(execution.id),
            'status': execution.status,
        }
        
    except Workflow.DoesNotExist:
        logger.error(f"Workflow {workflow_id} introuvable")
        return {
            'success': False,
            'error': 'Workflow introuvable',
        }
    
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution du workflow: {e}", exc_info=True)
        
        # Retry avec backoff exponentiel
        try:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            return {
                'success': False,
                'error': str(e),
            }


@shared_task
def process_webhook_trigger(trigger_id: str, webhook_data: dict):
    """
    Traite un déclencheur webhook.
    
    Args:
        trigger_id: ID du trigger
        webhook_data: Données reçues du webhook
    """
    from .models import Trigger
    
    try:
        trigger = Trigger.objects.select_related('workflow').get(id=trigger_id)
        
        if not trigger.is_active:
            logger.warning(f"Trigger {trigger_id} inactif")
            return
        
        # Lancer l'exécution du workflow
        execute_workflow_async.delay(
            workflow_id=str(trigger.workflow.id),
            input_data=webhook_data
        )
        
        logger.info(f"Workflow déclenché par webhook pour le trigger {trigger_id}")
        
    except Trigger.DoesNotExist:
        logger.error(f"Trigger {trigger_id} introuvable")
    except Exception as e:
        logger.error(f"Erreur lors du traitement du webhook: {e}", exc_info=True)


@shared_task
def process_scheduled_triggers():
    """
    Traite les déclencheurs planifiés (cron).
    Cette tâche devrait être exécutée régulièrement (ex: chaque minute).
    """
    from .models import Trigger
    from croniter import croniter
    from datetime import datetime
    
    try:
        # Récupérer tous les triggers actifs de type schedule
        triggers = Trigger.objects.filter(
            trigger_type='schedule',
            is_active=True
        ).select_related('workflow')
        
        now = datetime.now()
        
        for trigger in triggers:
            try:
                cron_expression = trigger.cron_expression
                
                if not cron_expression:
                    continue
                
                # Vérifier si le cron doit s'exécuter maintenant
                cron = croniter(cron_expression, now)
                next_run = cron.get_next(datetime)
                
                # Si le prochain run est dans la prochaine minute
                if next_run <= now + timedelta(minutes=1):
                    logger.info(f"Déclenchement du workflow planifié: {trigger.workflow.name}")
                    
                    execute_workflow_async.delay(
                        workflow_id=str(trigger.workflow.id),
                        input_data={'triggered_by': 'schedule', 'cron': cron_expression}
                    )
                    
            except Exception as e:
                logger.error(f"Erreur lors du traitement du trigger {trigger.id}: {e}", exc_info=True)
                continue
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement des triggers planifiés: {e}", exc_info=True)


@shared_task
def cleanup_old_executions(days: int = 30):
    """
    Nettoie les anciennes exécutions de workflows.
    
    Args:
        days: Nombre de jours à conserver
    """
    from .models import WorkflowExecution
    
    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Supprimer les exécutions anciennes (sauf celles en cours)
        deleted_count = WorkflowExecution.objects.filter(
            created_at__lt=cutoff_date,
            status__in=['completed', 'failed', 'cancelled']
        ).delete()[0]
        
        logger.info(f"Nettoyage: {deleted_count} exécutions supprimées")
        
        return {
            'success': True,
            'deleted_count': deleted_count,
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des exécutions: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
        }


@shared_task
def cleanup_stale_executions():
    """
    Nettoie les exécutions bloquées en statut 'running' depuis trop longtemps.
    """
    from .models import WorkflowExecution
    
    try:
        # Exécutions en cours depuis plus de 2 heures
        cutoff_time = timezone.now() - timedelta(hours=2)
        
        stale_executions = WorkflowExecution.objects.filter(
            status='running',
            started_at__lt=cutoff_time
        )
        
        count = stale_executions.count()
        
        # Marquer comme échouées
        stale_executions.update(
            status='failed',
            error_message='Exécution expirée (timeout)',
            completed_at=timezone.now()
        )
        
        logger.info(f"Nettoyage: {count} exécutions bloquées marquées comme échouées")
        
        return {
            'success': True,
            'cleaned_count': count,
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des exécutions bloquées: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
        }


@shared_task
def send_workflow_notification(execution_id: str, notification_type: str):
    """
    Envoie une notification concernant une exécution de workflow.
    
    Args:
        execution_id: ID de l'exécution
        notification_type: Type de notification (completed, failed, etc.)
    """
    from .models import WorkflowExecution
    from apps.foundation.services.event_bus import EventBus
    
    try:
        execution = WorkflowExecution.objects.select_related('workflow', 'triggered_by').get(id=execution_id)
        
        # Publier un événement
        EventBus.publish(
            event_type=f'automation.notification.{notification_type}',
            data={
                'execution_id': str(execution.id),
                'workflow_name': execution.workflow.name,
                'status': execution.status,
                'user_id': execution.triggered_by.id if execution.triggered_by else None,
            },
            source='automation.tasks'
        )
        
        logger.info(f"Notification envoyée pour l'exécution {execution_id}")
        
    except WorkflowExecution.DoesNotExist:
        logger.error(f"Exécution {execution_id} introuvable")
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de la notification: {e}", exc_info=True)


@shared_task
def retry_failed_step(execution_id: str, step_id: str):
    """
    Réessaie une étape échouée dans un workflow.
    
    Args:
        execution_id: ID de l'exécution
        step_id: ID de l'étape à réessayer
    """
    from .models import WorkflowExecution, WorkflowStep
    from .services import WorkflowEngine
    
    try:
        execution = WorkflowExecution.objects.select_related('workflow').get(id=execution_id)
        step = WorkflowStep.objects.get(workflow=execution.workflow, step_id=step_id)
        
        # Créer un nouveau moteur avec le contexte existant
        engine = WorkflowEngine(execution.workflow)
        engine.execution = execution
        engine.context = execution.context
        
        # Réessayer l'étape
        engine._execute_step(step)
        
        logger.info(f"Étape {step_id} réessayée avec succès")
        
        return {
            'success': True,
            'step_id': step_id,
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la nouvelle tentative de l'étape: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
        }


@shared_task
def export_workflow_execution_logs(execution_id: str):
    """
    Exporte les logs d'une exécution de workflow.
    
    Args:
        execution_id: ID de l'exécution
    """
    from .models import WorkflowExecution, WorkflowExecutionLog
    import json
    
    try:
        execution = WorkflowExecution.objects.select_related('workflow').get(id=execution_id)
        logs = WorkflowExecutionLog.objects.filter(execution=execution).order_by('created_at')
        
        export_data = {
            'execution_id': str(execution.id),
            'workflow_name': execution.workflow.name,
            'status': execution.status,
            'started_at': execution.started_at.isoformat() if execution.started_at else None,
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'duration': execution.duration,
            'logs': [
                {
                    'timestamp': log.created_at.isoformat(),
                    'level': log.level,
                    'step_id': log.step_id,
                    'message': log.message,
                    'details': log.details,
                }
                for log in logs
            ],
        }
        
        # Dans une vraie impl, sauvegarder dans S3 ou similaire
        logger.info(f"Logs exportés pour l'exécution {execution_id}")
        
        return {
            'success': True,
            'logs_count': logs.count(),
            'export_data': export_data,
        }
        
    except WorkflowExecution.DoesNotExist:
        logger.error(f"Exécution {execution_id} introuvable")
        return {
            'success': False,
            'error': 'Exécution introuvable',
        }
    except Exception as e:
        logger.error(f"Erreur lors de l'export des logs: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
        }


@shared_task
def update_integration_stats():
    """
    Met à jour les statistiques des intégrations.
    """
    from .models import Integration
    
    try:
        integrations = Integration.objects.all()
        
        for integration in integrations:
            # Calculer et mettre à jour les stats
            # Dans une vraie impl, agréger depuis Redis ou cache
            pass
        
        logger.info("Statistiques des intégrations mises à jour")
        
        return {
            'success': True,
            'integrations_count': integrations.count(),
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des stats: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
        }
