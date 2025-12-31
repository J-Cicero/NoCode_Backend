"""
Signals pour le module Automation
"""
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from apps.foundation.services.event_bus import EventBus
from .models import Workflow, WorkflowExecution, Integration
from apps.studio.models import DataSchema, FieldSchema, ComponentInstance, Page
from apps.runtime.builders.model_builder import ModelBuilder
# Insights est optionnel (peut être désactivé dans INSTALLED_APPS)
try:
    from apps.insights.models import UserActivity, SystemMetric
except Exception:  # pragma: no cover
    UserActivity = None
    SystemMetric = None


def log_metric(metric_type: str, value: int = 1, tags: dict | None = None, **extra):
    """Enregistre une métrique Insights si le module est activé."""
    if SystemMetric is None:
        return
    SystemMetric.objects.create(metric_type=metric_type, value=value, tags=tags or {}, **extra)


def log_activity(**kwargs):
    """Enregistre une activité utilisateur Insights si le module est activé."""
    if UserActivity is None:
        return
    UserActivity.objects.create(**kwargs)

import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Workflow)
def workflow_saved(sender, instance, created, **kwargs):
    """Signal après la sauvegarde d'un workflow."""
    try:
        if created:
            # Publier un événement de création
            EventBus.publish(
                event_name='automation.workflow.created',
                event_data={
                    'workflow_id': str(instance.id),
                    'name': instance.name,
                    'organization_id': instance.organization.id,
                    'status': instance.status,
                },
                source_module='automation.signals',
                user=instance.created_by,
            )
            logger.info(f"Workflow créé: {instance.name}")
        else:
            # Publier un événement de mise à jour
            EventBus.publish(
                event_name='automation.workflow.updated',
                event_data={
                    'workflow_id': str(instance.id),
                    'name': instance.name,
                    'status': instance.status,
                },
                source_module='automation.signals',
                user=instance.created_by,
            )
    except Exception as e:
        logger.error(f"Erreur lors de la publication de l'événement workflow: {e}", exc_info=True)


@receiver(pre_delete, sender=Workflow)
def workflow_deleted(sender, instance, **kwargs):
    """Signal avant la suppression d'un workflow."""
    try:
        # Publier un événement de suppression
        EventBus.publish(
            event_name='automation.workflow.deleted',
            event_data={
                'workflow_id': str(instance.id),
                'name': instance.name,
                'organization_id': instance.organization.id,
            },
            source_module='automation.signals',
            user=instance.created_by,
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
                event_name='automation.execution.started',
                event_data={
                    'execution_id': str(instance.id),
                    'workflow_id': str(instance.workflow.id),
                    'workflow_name': instance.workflow.name,
                    'status': instance.status,
                },
                source_module='automation.signals',
                user=instance.triggered_by,
            )
        elif instance.status in ['completed', 'failed', 'cancelled']:
            # Exécution terminée
            EventBus.publish(
                event_name=f'automation.execution.{instance.status}',
                event_data={
                    'execution_id': str(instance.id),
                    'workflow_id': str(instance.workflow.id),
                    'workflow_name': instance.workflow.name,
                    'status': instance.status,
                    'duration': instance.duration,
                    'error_message': instance.error_message if instance.status == 'failed' else None,
                },
                source_module='automation.signals',
                user=instance.triggered_by,
            )
    except Exception as e:
        logger.error(f"Erreur lors de la publication de l'événement d'exécution: {e}", exc_info=True)


@receiver(post_save, sender=Integration)
def integration_saved(sender, instance, created, **kwargs):
    """Signal après la sauvegarde d'une intégration."""
    try:
        if created:
            EventBus.publish(
                event_name='automation.integration.created',
                event_data={
                    'integration_id': str(instance.id),
                    'name': instance.name,
                    'type': instance.integration_type,
                    'organization_id': instance.organization.id,
                },
                source_module='automation.signals',
            )
            logger.info(f"Intégration créée: {instance.name}")
    except Exception as e:
        logger.error(f"Erreur lors de la publication de l'événement d'intégration: {e}", exc_info=True)


# ============================================
# SIGNAUX POUR LA GÉNÉRATION AUTOMATIQUE NOCODE
# ============================================

@receiver(post_save, sender=DataSchema)
def auto_generate_django_model(sender, instance, created, **kwargs):
    """
    SIGNAL CRITIQUE :
    Quand une table est créée/modifiée, générer automatiquement le modèle Django.
    """
    try:
        if created:
            logger.info(f"🚀 DÉBUT - Création automatique du modèle pour la table: {instance.display_name}")
            print(f"🚀 DÉBUT - Création automatique du modèle pour la table: {instance.display_name}")
            
            # Utiliser ModelBuilder pour générer le modèle
            logger.info(f"📦 Initialisation ModelBuilder pour le projet: {instance.project.name}")
            print(f"📦 Initialisation ModelBuilder pour le projet: {instance.project.name}")
            
            builder = ModelBuilder(instance.project)
            logger.info(f"⚙️ Appel de generate_model_from_schema()")
            print(f"⚙️ Appel de generate_model_from_schema()")
            
            model_file = builder.generate_model_from_schema(instance)
            logger.info(f"✅ Fichier modèle généré: {model_file}")
            print(f"✅ Fichier modèle généré: {model_file}")
            
            # Logger dans Insights
            log_metric(
                metric_type='table_created',
                value=1,
                tags={
                    'project_id': instance.project.id,
                    'table_name': instance.table_name,
                    'schema_id': instance.id,
                },
            )
            
            # Créer UserActivity seulement si le projet a une organisation
            if instance.project.organization:
                log_activity(
                    user=instance.project.created_by,
                    organization=instance.project.organization,
                    activity_type='AUTO_MODEL_GENERATE',
                    description=f"Modèle Django généré automatiquement pour la table '{instance.display_name}'",
                )
            
            logger.info(f"✅ Modèle généré avec succès: {model_file}")
            print(f"✅ SUCCÈS COMPLET - Modèle généré: {model_file}")
            
        else:
            # Si modification, régénérer le modèle
            logger.info(f"Mise à jour du modèle pour la table: {instance.display_name}")
            
            builder = ModelBuilder(instance.project)
            model_file = builder.generate_model_from_schema(instance)
            
            logger.info(f"✅ Modèle mis à jour: {model_file}")
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de la génération automatique du modèle pour {instance.display_name}: {e}")
        print(f"❌ ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        
        # Logger l'erreur dans Insights
        log_metric(
            metric_type='model_generation_error',
            value=1,
            tags={
                'project_id': instance.project.id,
                'table_name': instance.table_name,
                'error': str(e),
            },
        )


@receiver(post_save, sender=FieldSchema)
def auto_add_field_to_model(sender, instance, created, **kwargs):
    """
    SIGNAL CRITIQUE :
    Quand un champ est ajouté à une table, mettre à jour le modèle Django.
    """
    try:
        if created:
            logger.info(f"Ajout automatique du champ '{instance.name}' à la table '{instance.schema.display_name}'")
            
            # Utiliser ModelBuilder pour mettre à jour le modèle
            builder = ModelBuilder(instance.schema.project)
            builder.add_field_to_existing_model(instance.schema, instance)
            
            # Logger dans Insights
            log_metric(
                metric_type='field_added',
                value=1,
                tags={
                    'project_id': instance.schema.project.id,
                    'table_name': instance.schema.table_name,
                    'field_name': instance.name,
                    'field_type': instance.field_type,
                },
            )
            
            # Créer UserActivity seulement si le projet a une organisation
            if instance.schema.project.organization:
                log_activity(
                    user=instance.schema.project.created_by,
                    organization=instance.schema.project.organization,
                    activity_type='AUTO_FIELD_ADD',
                    description=f"Champ '{instance.display_name}' ajouté automatiquement à la table '{instance.schema.display_name}'",
                )
            
            logger.info(f"✅ Champ '{instance.name}' ajouté avec succès")
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'ajout du champ '{instance.name}': {e}")
        
        # Logger l'erreur
        log_metric(
            metric_type='field_add_error',
            value=1,
            tags={
                'project_id': instance.schema.project.id,
                'table_name': instance.schema.table_name,
                'field_name': instance.name,
                'error': str(e),
            },
        )


@receiver(pre_save, sender=ComponentInstance)
def auto_create_page_if_needed(sender, instance, **kwargs):
    """
    SIGNAL CRITIQUE :
    Quand un composant est ajouté à un projet, vérifier si une page existe.
    Si aucune page n'existe, en créer une automatiquement.
    """
    try:
        # Vérifier si c'est une nouvelle instance
        if instance.pk is None:
            project = instance.page.project if instance.page else None
            
            # Si pas de page, on doit la créer après sauvegarde du composant
            if project and not project.pages.exists():
                # Marquer pour création post-sauvegarde
                instance._needs_page_creation = True
                logger.info(f"Premier composant ajouté au projet {project.name} - création de page automatique prévue")
                
    except Exception as e:
        logger.error(f"❌ Erreur dans signal auto_create_page_if_needed: {e}")


@receiver(post_save, sender=ComponentInstance)
def handle_post_component_save(sender, instance, created, **kwargs):
    """
    Gère les actions post-sauvegarde des composants.
    """
    try:
        if created and hasattr(instance, '_needs_page_creation'):
            # Créer la page automatiquement
            project = instance.page.project
            
            page = Page.objects.create(
                project=project,
                name="Page d'accueil",
                route="home",
                is_home=True,
                config={
                    'components': [
                        {
                            'id': instance.id,
                            'component_type': instance.component.name,
                            'config': instance.config,
                            'order': instance.order
                        }
                    ]
                }
            )
            
            # Déplacer le composant vers cette page
            instance.page = page
            instance.save(update_fields=['page'])
            
            # Logger dans Insights
            log_metric(
                metric_type='auto_page_created',
                value=1,
                tags={
                    'project_id': project.id,
                    'page_id': page.id,
                    'component_id': instance.id,
                },
            )
            
            # Créer UserActivity seulement si le projet a une organisation
            if project.organization:
                log_activity(
                    user=project.created_by,
                    organization=project.organization,
                    activity_type='AUTO_PAGE_CREATE',
                    description=f"Page '{page.name}' créée automatiquement lors du premier drag & drop",
                )
            
            logger.info(f"✅ Page '{page.name}' créée automatiquement pour le projet {project.name}")
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création automatique de page: {e}")


@receiver(post_save, sender=Page)
def auto_save_page_config(sender, instance, **kwargs):
    """
    SIGNAL CRITIQUE :
    Quand une page est modifiée, déclencher l'auto-save et la mise à jour du projet.
    """
    try:
        # Logger l'activité
        if hasattr(instance, '_user_from_request'):
            log_activity(
                user=instance._user_from_request,
                activity_type='PAGE_UPDATE',
                description=f"Page '{instance.name}' mise à jour automatiquement",
            )
        
        logger.info(f"Page '{instance.name}' sauvegardée automatiquement")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'auto-save de la page: {e}")
