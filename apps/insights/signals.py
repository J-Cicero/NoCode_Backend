"""
Signaux pour le module Insights.

Connecte automatiquement les événements Django aux systèmes
de tracking et de métriques.
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.auth import get_user_model

from .models import UserActivity
from .services import ActivityTracker

logger = logging.getLogger(__name__)
User = get_user_model()

@receiver(user_logged_in)
def track_user_login(sender, request, user, **kwargs):
    """Trace les connexions utilisateur."""
    try:
        ActivityTracker.track_login(user, request)
    except Exception as e:
        logger.error(f"Erreur lors du tracking de connexion: {str(e)}")

@receiver(user_logged_out)
def track_user_logout(sender, request, user, **kwargs):
    """Trace les déconnexions utilisateur."""
    try:
        ActivityTracker.track_logout(user, request)
    except Exception as e:
        logger.error(f"Erreur lors du tracking de déconnexion: {str(e)}")

@receiver(post_save, sender='foundation.Organization')
def track_organization_changes(sender, instance, created, **kwargs):
    """Trace les changements d'organisation."""
    try:
        user = instance.owner

        if created:
            ActivityTracker.track_user_action(
                user=user,
                action_type='organization.created',
                description=f'Création de l\'organisation {instance.name}',
                content_object=instance
            )
        else:
            ActivityTracker.track_user_action(
                user=user,
                action_type='organization.updated',
                description=f'Mise à jour de l\'organisation {instance.name}',
                content_object=instance
            )
    except Exception as e:
        logger.error(f"Erreur lors du tracking d'organisation: {str(e)}")

@receiver(post_save, sender='studio.Project')
def track_project_changes(sender, instance, created, **kwargs):
    """Trace les changements de projet."""
    try:
        user = instance.created_by

        if created:
            ActivityTracker.track_project_action(
                user=user,
                project=instance,
                action_type='created'
            )
        else:
            ActivityTracker.track_project_action(
                user=user,
                project=instance,
                action_type='updated'
            )
    except Exception as e:
        logger.error(f"Erreur lors du tracking de projet: {str(e)}")

@receiver(post_save, sender='runtime.GeneratedApp')
def track_app_changes(sender, instance, created, **kwargs):
    """Trace les changements d'application."""
    try:
        user = instance.project.created_by

        if created:
            ActivityTracker.track_app_action(
                user=user,
                app=instance,
                action_type='created'
            )
        elif instance.status == 'deployed' and not created:
            ActivityTracker.track_app_action(
                user=user,
                app=instance,
                action_type='deployed'
            )
        elif instance.status == 'error' and not created:
            ActivityTracker.track_app_action(
                user=user,
                app=instance,
                action_type='failed'
            )
    except Exception as e:
        logger.error(f"Erreur lors du tracking d'application: {str(e)}")
