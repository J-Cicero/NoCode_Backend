
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from .base import BaseModel
import uuid

User = get_user_model()

class Organization(BaseModel):
    
    tracking_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Tracking ID",
        help_text="Identifiant public unique utilisé dans les URLs et APIs"
    )
    
    TYPE_CHOICES = [
        ('PERSONAL', 'Personnel'),
        ('BUSINESS', 'Entreprise'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspendue'),
    ]

    name = models.CharField(
        max_length=100,
        verbose_name="Nom de l'organisation"
    )
    
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='PERSONAL',
        verbose_name="Type d'organisation"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        verbose_name="Statut"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    city = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Ville",
        help_text="Ville où est basée l'organisation"
    )
    
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_organizations',
        verbose_name="Propriétaire"
    )
    
    numero_certification = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Numéro de certification",
        help_text="Numéro SIRET, KBIS ou autre certification officielle"
    )
    
    is_active = models.BooleanField(
        default=False,
        verbose_name="Organisation active",
        help_text="Les organisations doivent être validées avant d'être activées"
    )
    
    is_verified = models.BooleanField(
        default=False,
        verbose_name="Organisation vérifiée"
    )
    
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de vérification"
    )
    
    max_members = models.PositiveIntegerField(
        default=5,
        verbose_name="Nombre maximum de membres",
        help_text="Limite définie par l'abonnement"
    )
    
    max_projects = models.PositiveIntegerField(
        default=3,
        verbose_name="Nombre maximum de projets",
        help_text="Limite définie par l'abonnement"
    )
    
    class Meta:
        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"
        db_table = 'foundation_organization'
        ordering = ['name']


    def __str__(self):
        return self.name
    
    def activate(self):
        self.is_active = True
        self.save(update_fields=['is_active'])
    
    def deactivate(self):
        self.is_active = False
        self.save(update_fields=['is_active'])
    
    def verify(self):
        self.is_verified = True
        self.verified_at = timezone.now()
        self.is_active = True
        self.save(update_fields=['is_verified', 'verified_at', 'is_active'])
    
    @property
    def can_operate(self):
        return self.is_active and self.is_verified
    
    @property
    def status_display(self):
        if not self.is_active:
            return "Inactive"
        elif not self.is_verified:
            return "En attente de vérification"
        else:
            return "Active et vérifiée"



class OrganizationMember(BaseModel):

    tracking_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Tracking ID",
        help_text="Identifiant public unique utilisé dans les URLs et APIs"
    )

    ROLE_CHOICES = [
        ('OWNER', 'Propriétaire'),
        ('ADMIN', 'Administrateur'),
        ('MEMBER', 'Membre'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Actif'),
        ('INACTIVE', 'Inactif'),
        ('PENDING', 'En attente'),
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
        default='MEMBER',
        verbose_name="Rôle"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        verbose_name="Statut"
    )
    
    joined_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Rejoint le"
    )
    
    class Meta:
        unique_together = ('organization', 'user')
        verbose_name = "Membre d'organisation"
        verbose_name_plural = "Membres d'organisation"
        db_table = 'foundation_organization_member'
        ordering = ['organization', 'user__email']

    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.get_role_display()})"



