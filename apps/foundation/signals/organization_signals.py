
import logging
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from ..models import Organization, OrganizationMember

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Organization)
def organization_post_save(sender, instance, created, **kwargs):

    if created:
        logger.info(f"Nouvelle organisation créée : {instance.name}")

@receiver(post_save, sender=OrganizationMember)
def organization_member_post_save(sender, instance, created, **kwargs):

    if created:
        logger.info(
            f"Nouveau membre ajouté à l'organisation {instance.organization.name} : "
            f"{instance.user.email} (rôle: {instance.role})"
        )

