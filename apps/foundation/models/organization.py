
import uuid
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .base import BaseModel


User = get_user_model()


class Organization(BaseModel):

    name = models.CharField(
        max_length=100,
        verbose_name="Nom de l'organisation"
    )
    
    slug = models.SlugField(
        blank=True,
        max_length=100,
        unique=True,
        verbose_name="Slug",
        help_text="Identifiant unique pour les URLs (généré automatiquement)"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
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
    
    class Meta:
        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"
        db_table = 'foundation_organization'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
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

    ROLE_CHOICES = [
        ('OWNER', 'Propriétaire'),
        ('MEMBER', 'Membre'),
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


class OrganizationSettings(BaseModel):

    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name='settings',
        verbose_name="Organisation"
    )
    
    session_timeout = models.PositiveIntegerField(
        default=24,
        verbose_name="Délai d'expiration de session (heures)",
        help_text="Durée d'inactivité avant déconnexion automatique"
    )
    
    custom_logo = models.URLField(
        blank=True,
        null=True,
        verbose_name="Logo personnalisé",
        help_text="URL du logo de l'organisation"
    )
    
    custom_theme = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Thème personnalisé",
        help_text="Configuration du thème de l'interface (couleurs, polices, etc.)"
    )
    
    email_notifications = models.BooleanField(
        default=True,
        verbose_name="Activer les notifications par email"
    )
    
    class Meta:
        verbose_name = "Paramètres d'organisation"
        verbose_name_plural = "Paramètres des organisations"
        db_table = 'foundation_organization_settings'
    
    def __str__(self):
        return f"Paramètres - {self.organization.name}"
    
    def save(self, *args, **kwargs):
        if self.session_timeout > 720:
            self.session_timeout = 720
        elif self.session_timeout < 1:
            self.session_timeout = 1
            
        super().save(*args, **kwargs)
