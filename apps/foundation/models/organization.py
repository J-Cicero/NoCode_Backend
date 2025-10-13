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
    
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_organizations',
        verbose_name="Propriétaire"
    )
    
    # Champ de sécurité pour l'activation
    is_active = models.BooleanField(
        default=False,  # FALSE par défaut pour les organisations
        verbose_name="Organisation active",
        help_text="Les organisations doivent être validées avant d'être activées"
    )
    
    # Champs de vérification
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
    
    def activate(self, admin_user=None):
        """Active l'organisation après validation."""
        self.is_active = True
        self.save(update_fields=['is_active'])
        
        # Log de l'activation
        if admin_user:
            from .activity import ActivityLog
            ActivityLog.objects.create(
                user=admin_user,
                action='organization_activated',
                content_object=self,
                details={'organization_id': self.id, 'organization_name': self.name}
            )
    
    def deactivate(self, admin_user=None, reason=''):
        """Désactive l'organisation."""
        self.is_active = False
        self.save(update_fields=['is_active'])
        
        # Log de la désactivation
        if admin_user:
            from .activity import ActivityLog
            ActivityLog.objects.create(
                user=admin_user,
                action='organization_deactivated',
                content_object=self,
                details={'organization_id': self.id, 'organization_name': self.name, 'reason': reason}
            )
    
    def verify(self, admin_user=None):
        """Marque l'organisation comme vérifiée ET l'active."""
        self.is_verified = True
        self.verified_at = timezone.now()
        self.is_active = True  # Activation automatique après vérification
        self.save(update_fields=['is_verified', 'verified_at', 'is_active'])
        
        # Log de la vérification
        if admin_user:
            from .activity import ActivityLog
            ActivityLog.objects.create(
                user=admin_user,
                action='organization_verified',
                content_object=self,
                details={'organization_id': self.id, 'organization_name': self.name}
            )
    
    @property
    def can_operate(self):
        """Vérifie si l'organisation peut fonctionner (active ET vérifiée)."""
        return self.is_active and self.is_verified
    
    @property
    def status_display(self):
        """Retourne le statut lisible de l'organisation."""
        if not self.is_active:
            return "Inactive"
        elif not self.is_verified:
            return "En attente de vérification"
        else:
            return "Active et vérifiée"


class OrganizationMember(BaseModel):

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
        return self.status == 'EXPIRED' or (
            self.status == 'PENDING' and 
            timezone.now() > self.expires_at
        )
    
    def send_invitation_email(self, request=None):
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
        
        self.status = 'ACCEPTED'
        self.accepted_at = timezone.now()
        self.save(update_fields=['status', 'accepted_at', 'updated_at'])
    
    def revoke(self):
        if self.status == 'PENDING':
            self.status = 'REVOKED'
            self.save(update_fields=['status', 'updated_at'])
    
    def save(self, *args, **kwargs):
        if self.status == 'PENDING' and self.is_expired:
            self.status = 'EXPIRED'
        
        if not self.pk and not self.token:
            self.token = uuid.uuid4()
            
        super().save(*args, **kwargs)
