"""
Signals pour le module Automation
"""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from apps.foundation.services.event_bus import EventBus
from .models import Workflow, WorkflowExecution, Integration
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Workflow)
def workflow_saved(sender, instance, created, **kwargs):
    """Signal après la sauvegarde d'un workflow."""
    try:
        if created:
            # Publier un événement de création
            EventBus.publish(
                event_type='automation.workflow.created',
                data={
                    'workflow_id': str(instance.id),
                    'name': instance.name,
                    'organization_id': instance.organization.id,
                    'status': instance.status,
                },
                source='automation.signals'
            )
            logger.info(f"Workflow créé: {instance.name}")
        else:
            # Publier un événement de mise à jour
            EventBus.publish(
                event_type='automation.workflow.updated',
                data={
                    'workflow_id': str(instance.id),
                    'name': instance.name,
                    'status': instance.status,
                },
                source='automation.signals'
            )
    except Exception as e:
        logger.error(f"Erreur lors de la publication de l'événement workflow: {e}", exc_info=True)


@receiver(pre_delete, sender=Workflow)
def workflow_deleted(sender, instance, **kwargs):
    """Signal avant la suppression d'un workflow."""
    try:
        # Publier un événement de suppression
        EventBus.publish(
            event_type='automation.workflow.deleted',
            data={
                'workflow_id': str(instance.id),
                'name': instance.name,
                'organization_id': instance.organization.id,
            },
            source='automation.signals'
        )
        logger.info(f"Workflow supprimé: {instance.name}")
    except Exception as e:
        logger.error(f"Erreur lors de la publication de l'événement de suppression: {e}", exc_info=True)


@receiver(post_save, sender=WorkflowExecution)
def workflow_execution_status_changed(sender, instance, created, **kwargs):
    """Signal après un changement de statut d'exécution."""
    try:
        if created:
            # Nouvelle exécution
            EventBus.publish(
                event_type='automation.execution.started',
                data={
                    'execution_id': str(instance.id),
                    'workflow_id': str(instance.workflow.id),
                    'workflow_name': instance.workflow.name,
                    'status': instance.status,
                },
                source='automation.signals'
            )
        elif instance.status in ['completed', 'failed', 'cancelled']:
            # Exécution terminée
            EventBus.publish(
                event_type=f'automation.execution.{instance.status}',
                data={
                    'execution_id': str(instance.id),
                    'workflow_id': str(instance.workflow.id),
                    'workflow_name': instance.workflow.name,
                    'status': instance.status,
                    'duration': instance.duration,
                    'error_message': instance.error_message if instance.status == 'failed' else None,
                },
                source='automation.signals'
            )
    except Exception as e:
        logger.error(f"Erreur lors de la publication de l'événement d'exécution: {e}", exc_info=True)


@receiver(post_save, sender=Integration)
def integration_saved(sender, instance, created, **kwargs):
    """Signal après la sauvegarde d'une intégration."""
    try:
        if created:
            EventBus.publish(
                event_type='automation.integration.created',
                data={
                    'integration_id': str(instance.id),
                    'name': instance.name,
                    'type': instance.integration_type,
                    'organization_id': instance.organization.id,
                },
                source='automation.signals'
            )
            logger.info(f"Intégration créée: {instance.name}")
    except Exception as e:
        logger.error(f"Erreur lors de la publication de l'événement d'intégration: {e}", exc_info=True)
