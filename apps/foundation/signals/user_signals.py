
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from ..models import User, Organization, OrganizationMember

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):

    if created:
        logger.info(f"Nouvel utilisateur créé : {instance.email}")
        
        # Créer automatiquement une organisation personnelle pour le client
        personal_org = Organization.objects.create(
            name=f"Espace personnel - {instance.full_name or instance.email}",
            type='PERSONAL',
            status='ACTIVE',
            owner=instance,  # Ajouter le owner
            created_by=instance
        )
        
        # Ajouter l'utilisateur comme owner de son organisation personnelle
        OrganizationMember.objects.create(
            user=instance,
            organization=personal_org,
            role='OWNER',
            status='ACTIVE'
        )
        
        logger.info(f"Organisation personnelle créée pour {instance.email}: {personal_org.tracking_id}")
