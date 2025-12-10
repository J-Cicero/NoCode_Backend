"""
Signals pour le module foundation.
Gère la création automatique d'organisations personnelles et autres logiques.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Organization, OrganizationMember

User = get_user_model()


@receiver(post_save, sender=User)
def create_personal_organization(sender, instance, created, **kwargs):
    """
    Crée automatiquement une organisation personnelle pour chaque nouvel utilisateur.
    """
    if created:
        # Créer l'organisation personnelle
        personal_org = Organization.objects.create(
            name=f"Espace personnel - {instance.full_name or instance.email}",
            type='PERSONAL',
            status='ACTIVE',
            description="Espace personnel pour vos projets individuels",
            owner=instance,
            is_active=True,
            is_verified=True,  # Auto-vérifié pour les espaces personnels
            max_members=1,  # Seulement le propriétaire
            max_projects=10,  # Limite raisonnable pour les projets personnels
            created_by=instance
        )
        
        # Ajouter l'utilisateur comme membre OWNER
        OrganizationMember.objects.create(
            organization=personal_org,
            user=instance,
            role='OWNER',
            status='ACTIVE',
            created_by=instance
        )


@receiver(post_save, sender=User)
def save_user_personal_organization(sender, instance, **kwargs):
    """
    Signal de sauvegarde pour éviter les problèmes avec les signaux Django.
    """
    pass  # Nécessaire pour que le signal post_save fonctionne correctement
