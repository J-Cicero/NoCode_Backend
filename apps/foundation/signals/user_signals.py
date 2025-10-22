"""
Signaux liés aux utilisateurs.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from ..models import User, Client

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """
    Déclenché après l'enregistrement d'un utilisateur.
    """
    if created:
        logger.info(f"Nouvel utilisateur créé : {instance.email}")
        # Création d'un profil client par défaut si nécessaire
        if not hasattr(instance, 'client'):
            Client.objects.create(user=instance, email=instance.email)
            logger.info(f"Profil client créé pour l'utilisateur : {instance.email}")

@receiver(post_save, sender=Client)
def client_post_save(sender, instance, created, **kwargs):
    """
    Déclenché après l'enregistrement d'un client.
    """
    if created:
        logger.info(f"Nouveau client créé : {instance.email}")
    else:
        logger.info(f"Client mis à jour : {instance.email}")
