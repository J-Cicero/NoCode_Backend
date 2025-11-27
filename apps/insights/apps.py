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

            # Les tâches périodiques sont maintenant gérées par Celery Beat
            # dans les settings (CELERY_BEAT_SCHEDULE)
            logger.info("Tâches périodiques Insights configurées via Celery Beat")

        except ImportError as e:
            logger.warning(f"Impossible de charger les composants Insights: {e}")
