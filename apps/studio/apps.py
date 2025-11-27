from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class StudioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.studio'
    verbose_name = 'Studio - NoCode Builder'
    
    def ready(self):
        """Initialisation du module Studio."""
        try:
            # Importer les signaux pour les activer
            from . import signals  # noqa
            from . import signals_auto_generation  # noqa
            logger.info("Signaux Studio chargés avec succès")
            
        except ImportError as e:
            logger.warning(f"Impossible de charger les composants Studio: {e}")
