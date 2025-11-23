
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
import logging

logger = logging.getLogger(__name__)

@receiver(post_save)
def log_model_changes(sender, instance, created, **kwargs):
    """Log tous les changements de modèles pour le debugging."""
    if created:
        logger.info(f"Created {sender.__name__}: {instance.pk}")
    else:
        logger.info(f"Updated {sender.__name__}: {instance.pk}")
