"""
Signaux liés aux organisations et à leurs membres.
"""
import logging
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from ..models import Organization, OrganizationMember, OrganizationSettings

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Organization)
def organization_post_save(sender, instance, created, **kwargs):
    """
    Déclenché après l'enregistrement d'une organisation.
    """
    if created:
        logger.info(f"Nouvelle organisation créée : {instance.name}")
        # Création des paramètres par défaut pour la nouvelle organisation
        OrganizationSettings.objects.get_or_create(organization=instance)
        logger.info(f"Paramètres par défaut créés pour l'organisation : {instance.name}")

@receiver(post_save, sender=OrganizationMember)
def organization_member_post_save(sender, instance, created, **kwargs):
    """
    Déclenché après l'ajout d'un membre à une organisation.
    """
    if created:
        logger.info(
            f"Nouveau membre ajouté à l'organisation {instance.organization.name} : "
            f"{instance.user.email} (rôle: {instance.role})"
        )

@receiver(m2m_changed, sender=Organization.members.through)
def organization_members_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    """
    Déclenché lorsque les membres d'une organisation changent.
    """
    if action in ["post_add", "post_remove", "post_clear"]:
        logger.info(
            f"Membres de l'organisation {instance.name} mis à jour. "
            f"Action: {action}"
        )
