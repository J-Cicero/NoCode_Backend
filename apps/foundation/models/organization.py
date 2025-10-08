"""
Système d'organisations pour le multi-tenancy.
Gère les organisations, membres, invitations et paramètres.
"""
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
        unique_together = ('organization', 'user')
        verbose_name = "Membre d'organisation"
        verbose_name_plural = "Membres d'organisation"
        db_table = 'foundation_organization_member'
        ordering = ['organization', 'user__last_name', 'user__first_name']

    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.get_role_display()})"


class OrganizationInvitation(BaseModel):
    """
    Modèle pour gérer les invitations à rejoindre une organisation.
    """
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('ACCEPTED', 'Acceptée'),
        ('EXPIRED', 'Expirée'),
        ('REVOKED', 'Révoquée')
    ]

    email = models.EmailField(
        verbose_name="Email invité"
    )
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='invitations',
        verbose_name="Organisation"
    )
    
    invited_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
        verbose_name="Invité par"
    )
    
    role = models.CharField(
        max_length=20,
        choices=OrganizationMember.ROLE_CHOICES,
        default='VIEWER',
        verbose_name="Rôle"
    )
    
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name="Jeton d'invitation"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Statut"
    )
    
    expires_at = models.DateTimeField(
        default=lambda: timezone.now() + timedelta(days=7),
        verbose_name="Date d'expiration"
    )
    
    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'acceptation"
    )
    
    class Meta:
        verbose_name = "Invitation d'organisation"
        verbose_name_plural = "Invitations d'organisation"
        db_table = 'foundation_organization_invitation'
        ordering = ['-created_at']
        unique_together = ('email', 'organization')
    
    def __str__(self):
        return f"Invitation pour {self.email} à {self.organization.name}"
    
    @property
    def is_expired(self):
        """Vérifie si l'invitation a expiré."""
        return self.status == 'EXPIRED' or (
            self.status == 'PENDING' and 
            timezone.now() > self.expires_at
        )
    
    def send_invitation_email(self, request=None):
        """Envoie l'email d'invitation."""
        context = {
            'organization': self.organization,
            'invitation': self,
            'inviter': self.invited_by.get_full_name() or self.invited_by.email,
            'expires_in_days': (self.expires_at - timezone.now()).days,
            'accept_url': f"{settings.FRONTEND_URL}/invitations/accept/{self.token}/"
        }
        
        subject = f"Invitation à rejoindre {self.organization.name}"
        message = render_to_string('emails/organization_invitation.txt', context)
        html_message = render_to_string('emails/organization_invitation.html', context)
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.email],
            html_message=html_message,
            fail_silently=False
        )
    
    def accept(self, user):
        """Accepte l'invitation pour un utilisateur."""
        if self.status != 'PENDING':
            raise ValueError("Cette invitation n'est plus valide.")
            
        if self.is_expired:
            self.status = 'EXPIRED'
            self.save(update_fields=['status'])
            raise ValueError("Cette invitation a expiré.")
        
        # Crée le membre de l'organisation
        OrganizationMember.objects.create(
            organization=self.organization,
            user=user,
            role=self.role
        )
        
        # Met à jour le statut de l'invitation
        self.status = 'ACCEPTED'
        self.accepted_at = timezone.now()
        self.save(update_fields=['status', 'accepted_at', 'updated_at'])
    
    def revoke(self):
        """Révoque l'invitation."""
        if self.status == 'PENDING':
            self.status = 'REVOKED'
            self.save(update_fields=['status', 'updated_at'])
    
    def save(self, *args, **kwargs):
        # Met à jour automatiquement le statut si l'invitation a expiré
        if self.status == 'PENDING' and self.is_expired:
            self.status = 'EXPIRED'
        
        # Génère un nouveau token si c'est une nouvelle invitation
        if not self.pk and not self.token:
            self.token = uuid.uuid4()
            
        super().save(*args, **kwargs)
