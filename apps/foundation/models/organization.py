"""
Système d'organisations pour le multi-tenancy.
Gère les organisations, membres, invitations et paramètres.
"""
from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from .base import BaseModel


User = get_user_model()


class Organization(BaseModel):
    """
    Modèle Organisation - Entité tenant pour le multi-tenancy.
    Chaque organisation représente un workspace isolé.
    """
    # Informations de base
    name = models.CharField(
        max_length=255,
        verbose_name="Nom de l'organisation"
    )
    
    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name="Slug",
        help_text="Identifiant unique pour les URLs (généré automatiquement)"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    # Propriétaire de l'organisation
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_organizations',
        verbose_name="Propriétaire"
    )
    
    class Meta:
        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"
        db_table = 'foundation_organization'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Override save pour générer automatiquement le slug."""
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            
            # Assurer l'unicité du slug
            while Organization.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        super().save(*args, **kwargs)


class OrganizationMember(BaseModel):
    """
    Relation User-Organization avec rôles et permissions.
    """
    ROLE_CHOICES = [
        ('OWNER', 'Propriétaire'),
        ('ADMIN', 'Administrateur'),
        ('EDITOR', 'Éditeur'),
        ('VIEWER', 'Observateur'),
    ]
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name="Organisation"
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='organization_memberships',
        verbose_name="Utilisateur"
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='VIEWER',
        verbose_name="Rôle"
    )
    
    # Date d'adhésion
    joined_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Rejoint le"
    )
    
    class Meta:
        verbose_name = "Membre d'organisation"
        verbose_name_plural = "Membres d'organisation"
        db_table = 'foundation_organization_member'
        unique_together = ['organization', 'user']
        ordering = ['role', 'joined_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.role})"
