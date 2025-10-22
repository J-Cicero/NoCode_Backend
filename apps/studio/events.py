"""
Événements et listeners pour le module Studio.
Intégration avec l'EventBus de Foundation.
"""
from apps.foundation.services.event_bus import EventBus, event_listener
import logging

logger = logging.getLogger(__name__)


class StudioEvents:
    """
    Constantes pour les événements du module Studio.
    """
    # Événements de projet
    PROJECT_CREATED = 'studio.project.created'
    PROJECT_UPDATED = 'studio.project.updated'
    PROJECT_DELETED = 'studio.project.deleted'
    PROJECT_EXPORTED = 'studio.project.exported'
    PROJECT_IMPORTED = 'studio.project.imported'
    
    # Événements de page
    PAGE_CREATED = 'studio.page.created'
    PAGE_UPDATED = 'studio.page.updated'
    PAGE_DELETED = 'studio.page.deleted'
    PAGE_PUBLISHED = 'studio.page.published'
    
    # Événements de composant
    COMPONENT_ADDED = 'studio.component.added'
    COMPONENT_UPDATED = 'studio.component.updated'
    COMPONENT_REMOVED = 'studio.component.removed'
    COMPONENT_MOVED = 'studio.component.moved'
    
    # Événements de schéma
    SCHEMA_CREATED = 'studio.schema.created'
    SCHEMA_UPDATED = 'studio.schema.updated'
    SCHEMA_DELETED = 'studio.schema.deleted'
    TABLE_CREATED = 'studio.table.created'
    
    # Événements de collaboration
    USER_JOINED_PROJECT = 'studio.collaboration.user_joined'
    USER_LEFT_PROJECT = 'studio.collaboration.user_left'
    ELEMENT_LOCKED = 'studio.collaboration.element_locked'
    ELEMENT_UNLOCKED = 'studio.collaboration.element_unlocked'
    
    # Événements de déploiement
    DEPLOYMENT_STARTED = 'studio.deployment.started'
    DEPLOYMENT_COMPLETED = 'studio.deployment.completed'
    DEPLOYMENT_FAILED = 'studio.deployment.failed'


# Listeners d'événements

@event_listener(StudioEvents.PROJECT_CREATED, priority=10)
def on_project_created(event_data):
    """
    Gère la création d'un projet.
    """
    try:
        project_id = event_data.get('project_id')
        user_id = event_data.get('user_id')
        
        logger.info(f"Projet {project_id} créé par l'utilisateur {user_id}")
        
        # Créer une page d'accueil par défaut si pas déjà fait
        # (géré dans la vue, mais on peut ajouter d'autres actions ici)
        
        # Envoyer une notification
        from apps.studio.services import NotificationService
        NotificationService.send_project_created_notification(project_id, user_id)
        
        return True
    except Exception as e:
        logger.error(f"Erreur dans on_project_created: {e}", exc_info=True)
        return False


@event_listener(StudioEvents.PAGE_UPDATED, priority=5)
def on_page_updated(event_data):
    """
    Gère la mise à jour d'une page.
    """
    try:
        page_id = event_data.get('page_id')
        project_id = event_data.get('project_id')
        changes = event_data.get('changes', {})
        
        logger.info(f"Page {page_id} du projet {project_id} mise à jour")
        
        # Invalider le cache si nécessaire
        from django.core.cache import cache
        cache.delete(f'page_{page_id}_config')
        
        # Notifier les utilisateurs connectés via WebSocket
        # (déjà géré dans le consumer, mais on peut ajouter d'autres actions)
        
        return True
    except Exception as e:
        logger.error(f"Erreur dans on_page_updated: {e}", exc_info=True)
        return False


@event_listener(StudioEvents.SCHEMA_CREATED, priority=10)
def on_schema_created(event_data):
    """
    Gère la création d'un schéma de données.
    """
    try:
        schema_id = event_data.get('schema_id')
        project_id = event_data.get('project_id')
        table_name = event_data.get('table_name')
        
        logger.info(f"Schéma {table_name} créé pour le projet {project_id}")
        
        # Mettre à jour les métadonnées du projet
        # Générer la documentation automatique
        # etc.
        
        return True
    except Exception as e:
        logger.error(f"Erreur dans on_schema_created: {e}", exc_info=True)
        return False


@event_listener(StudioEvents.ELEMENT_LOCKED, priority=5)
def on_element_locked(event_data):
    """
    Gère le verrouillage d'un élément.
    """
    try:
        element_type = event_data.get('element_type')
        element_id = event_data.get('element_id')
        user_id = event_data.get('user_id')
        
        logger.debug(f"Élément {element_type}:{element_id} verrouillé par {user_id}")
        
        # Enregistrer dans les logs d'activité
        from apps.foundation.models import ActivityLog
        ActivityLog.objects.create(
            user_id=user_id,
            action='element_locked',
            details={
                'element_type': element_type,
                'element_id': element_id,
            }
        )
        
        return True
    except Exception as e:
        logger.error(f"Erreur dans on_element_locked: {e}", exc_info=True)
        return False


@event_listener(StudioEvents.DEPLOYMENT_COMPLETED, priority=10)
def on_deployment_completed(event_data):
    """
    Gère la fin d'un déploiement.
    """
    try:
        project_id = event_data.get('project_id')
        deployment_url = event_data.get('deployment_url')
        
        logger.info(f"Déploiement du projet {project_id} terminé: {deployment_url}")
        
        # Envoyer une notification par email
        # Mettre à jour le statut du projet
        # etc.
        
        return True
    except Exception as e:
        logger.error(f"Erreur dans on_deployment_completed: {e}", exc_info=True)
        return False


def register_studio_events():
    """
    Enregistre tous les événements Studio.
    Cette fonction doit être appelée au démarrage de l'application.
    """
    logger.info("Enregistrement des événements Studio")
    
    # Les événements sont déjà enregistrés via le décorateur @event_listener
    # Cette fonction peut être utilisée pour des enregistrements dynamiques
    
    # Exemple d'enregistrement manuel:
    # EventBus.subscribe(StudioEvents.PROJECT_CREATED, custom_handler, priority=5)
    
    logger.info("Événements Studio enregistrés avec succès")
