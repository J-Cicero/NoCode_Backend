"""
Configuration de l'application Insights.
Module d'analytics et monitoring pour la plateforme NoCode.
"""
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class InsightsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.insights'
    verbose_name = 'Insights - Analytics & Monitoring'

    def ready(self):
        """Initialisation du module Insights."""
        try:
            # Importer les signaux pour les activer
            from . import signals  # noqa
            logger.info("Signaux Insights chargés avec succès")

            # Démarrer les tâches périodiques si nécessaire
            from .tasks import start_periodic_tasks
            start_periodic_tasks()

        except ImportError as e:
            logger.warning(f"Impossible de charger les composants Insights: {e}")
