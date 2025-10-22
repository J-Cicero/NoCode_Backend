"""
Configuration de l'application Runtime.
Gère la génération et l'exécution des applications créées avec le Studio.
"""
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class RuntimeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.runtime'
    verbose_name = 'Runtime'

    def ready(self):
        # Importer les signaux pour les activer
        try:
            from . import signals  # noqa
            logger.info("Signaux Runtime chargés avec succès")
        except ImportError as e:
            logger.warning(f"Impossible de charger les signaux Runtime: {e}")
