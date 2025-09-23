"""
Système d'organisations pour le multi-tenancy.
Gère les organisations, membres, invitations et paramètres.
"""
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model
from .base import BaseModel
from .mixins import StatusMixin, MetadataMixin, SlugMixin
import secrets
import string


User = get_user_model()


class Organization(BaseModel, StatusMixin, MetadataMixin):
    """
    Modèle Organisation - Entité tenant pour le multi-tenancy.
    Chaque organisation représente un workspace isolé.
    """
    TYPE_CHOICES = [
        ('PERSONAL', 'Personnel'),
        ('BUSINESS', 'Entreprise'),
        ('TEAM', 'Équipe'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Actif'),
        ('SUSPENDED', 'Suspendu'),
        ('DELETED', 'Supprimé'),
    ]
    
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
    
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='PERSONAL',
        verbose_name="Type d'organisation"
    )
    
    # Propriétaire de l'organisation
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_organizations',
        verbose_name="Propriétaire"
    )
    
    # Statut (hérité de StatusMixin)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        verbose_name="Statut"
    )
    
    # Paramètres visuels
    logo = models.ImageField(
        upload_to='organizations/logos/',
        null=True,
        blank=True,
        verbose_name="Logo"
    )
    
    color_primary = models.CharField(
        max_length=7,
        default='#007bff',
        validators=[
            RegexValidator(
                regex=r'^#[0-9A-Fa-f]{6}$',
                message="La couleur doit être au format hexadécimal (#RRGGBB)"
            )
        ],
        verbose_name="Couleur principale"
    )
    
    # Paramètres techniques
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        verbose_name="Fuseau horaire"
    )
    
    language = models.CharField(
        max_length=10,
        default='fr',
        choices=[
            ('fr', 'Français'),
            ('en', 'English'),
            ('es', 'Español'),
        ],
        verbose_name="Langue"
    )
    
    # Limites et quotas
    max_members = models.PositiveIntegerField(
        default=5,
        verbose_name="Nombre maximum de membres"
    )
    
    max_projects = models.PositiveIntegerField(
        default=3,
        verbose_name="Nombre maximum de projets"
    )
    
    # Paramètres de facturation
    billing_email = models.EmailField(
        blank=True,
        verbose_name="Email de facturation"
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
    
    @property
    def member_count(self):
        """Retourne le nombre de membres actifs."""
        return self.members.filter(status='ACTIVE').count()
    
    @property
    def project_count(self):
        """Retourne le nombre de projets actifs."""
        # Sera implémenté quand le module Studio sera créé
        return 0
    
    @property
    def can_add_member(self):
        """Vérifie si on peut ajouter un nouveau membre."""
        return self.member_count < self.max_members
    
    @property
    def can_create_project(self):
        """Vérifie si on peut créer un nouveau projet."""
        return self.project_count < self.max_projects
    
    def get_absolute_url(self):
        """Retourne l'URL de l'organisation."""
        return f"/org/{self.slug}/"
    
    def is_member(self, user):
        """Vérifie si un utilisateur est membre de l'organisation."""
        return self.members.filter(user=user, status='ACTIVE').exists()
    
    def get_member_role(self, user):
        """Retourne le rôle d'un utilisateur dans l'organisation."""
        try:
            member = self.members.get(user=user, status='ACTIVE')
            return member.role
        except OrganizationMember.DoesNotExist:
            return None


class OrganizationMember(BaseModel, StatusMixin):
    """
    Relation User-Organization avec rôles et permissions.
    """
    ROLE_CHOICES = [
        ('OWNER', 'Propriétaire'),
        ('ADMIN', 'Administrateur'),
        ('EDITOR', 'Éditeur'),
        ('VIEWER', 'Observateur'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Actif'),
        ('INVITED', 'Invité'),
        ('SUSPENDED', 'Suspendu'),
        ('LEFT', 'Parti'),
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
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        verbose_name="Statut"
    )
    
    # Qui a invité ce membre
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='organization_invitations_sent',
        verbose_name="Invité par"
    )
    
    # Dates importantes
    joined_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Rejoint le"
    )
    
    last_activity = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Dernière activité"
    )
    
    # Permissions personnalisées
    custom_permissions = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Permissions personnalisées"
    )
    
    class Meta:
        verbose_name = "Membre d'organisation"
        verbose_name_plural = "Membres d'organisation"
        db_table = 'foundation_organization_member'
        unique_together = ['organization', 'user']
        ordering = ['role', 'joined_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.role})"
    
    @property
    def can_manage_members(self):
        """Vérifie si le membre peut gérer d'autres membres."""
        return self.role in ['OWNER', 'ADMIN']
    
    @property
    def can_edit_projects(self):
        """Vérifie si le membre peut éditer les projets."""
        return self.role in ['OWNER', 'ADMIN', 'EDITOR']
    
    @property
    def can_view_billing(self):
        """Vérifie si le membre peut voir la facturation."""
        return self.role in ['OWNER', 'ADMIN']
    
    @property
    def can_manage_organization(self):
        """Vérifie si le membre peut gérer l'organisation."""
        return self.role == 'OWNER'
    
    def update_last_activity(self):
        """Met à jour la dernière activité du membre."""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])


class OrganizationInvitation(BaseModel):
    """
    Invitations en attente pour rejoindre une organisation.
    """
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('ACCEPTED', 'Acceptée'),
        ('DECLINED', 'Refusée'),
        ('EXPIRED', 'Expirée'),
        ('CANCELLED', 'Annulée'),
    ]
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='invitations',
        verbose_name="Organisation"
    )
    
    # Email de la personne invitée
    email = models.EmailField(
        verbose_name="Email de l'invité"
    )
    
    # Rôle proposé
    role = models.CharField(
        max_length=20,
        choices=OrganizationMember.ROLE_CHOICES,
        default='VIEWER',
        verbose_name="Rôle proposé"
    )
    
    # Statut de l'invitation
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Statut"
    )
    
    # Qui a envoyé l'invitation
    invited_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
        verbose_name="Invité par"
    )
    
    # Token sécurisé pour l'invitation
    token = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Token d'invitation"
    )
    
    # Message personnalisé
    message = models.TextField(
        blank=True,
        verbose_name="Message personnalisé"
    )
    
    # Dates
    expires_at = models.DateTimeField(
        verbose_name="Expire le"
    )
    
    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Acceptée le"
    )
    
    accepted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_invitations',
        verbose_name="Acceptée par"
    )
    
    class Meta:
        verbose_name = "Invitation d'organisation"
        verbose_name_plural = "Invitations d'organisation"
        db_table = 'foundation_organization_invitation'
        unique_together = ['organization', 'email', 'status']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invitation {self.email} -> {self.organization.name}"
    
    def save(self, *args, **kwargs):
        """Override save pour générer le token et la date d'expiration."""
        if not self.token:
            self.token = self.generate_token()
        
        if not self.expires_at:
            # Expiration dans 7 jours
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_token():
        """Génère un token sécurisé pour l'invitation."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(64))
    
    @property
    def is_expired(self):
        """Vérifie si l'invitation a expiré."""
        return timezone.now() > self.expires_at
    
    @property
    def is_pending(self):
        """Vérifie si l'invitation est en attente."""
        return self.status == 'PENDING' and not self.is_expired
    
    def accept(self, user):
        """Accepte l'invitation et crée le membre."""
        if not self.is_pending:
            raise ValueError("Cette invitation ne peut pas être acceptée")
        
        if user.email != self.email:
            raise ValueError("L'email ne correspond pas à l'invitation")
        
        # Créer le membre
        member, created = OrganizationMember.objects.get_or_create(
            organization=self.organization,
            user=user,
            defaults={
                'role': self.role,
                'status': 'ACTIVE',
                'invited_by': self.invited_by,
            }
        )
        
        # Marquer l'invitation comme acceptée
        self.status = 'ACCEPTED'
        self.accepted_at = timezone.now()
        self.accepted_by = user
        self.save(update_fields=['status', 'accepted_at', 'accepted_by'])
        
        return member
    
    def decline(self):
        """Refuse l'invitation."""
        if not self.is_pending:
            raise ValueError("Cette invitation ne peut pas être refusée")
        
        self.status = 'DECLINED'
        self.save(update_fields=['status'])
    
    def cancel(self):
        """Annule l'invitation."""
        if self.status not in ['PENDING']:
            raise ValueError("Cette invitation ne peut pas être annulée")
        
        self.status = 'CANCELLED'
        self.save(update_fields=['status'])


class OrganizationSettings(BaseModel):
    """
    Paramètres spécifiques à une organisation.
    """
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name='settings',
        verbose_name="Organisation"
    )
    
    # Paramètres généraux stockés en JSON
    settings = models.JSONField(
        default=dict,
        verbose_name="Paramètres",
        help_text="Paramètres de configuration au format JSON"
    )
    
    # Rôle par défaut pour les nouveaux membres
    default_user_role = models.CharField(
        max_length=20,
        choices=OrganizationMember.ROLE_CHOICES,
        default='VIEWER',
        verbose_name="Rôle par défaut"
    )
    
    # Inscription publique autorisée
    allow_public_signup = models.BooleanField(
        default=False,
        verbose_name="Autoriser l'inscription publique"
    )
    
    # Domaines autorisés pour l'inscription automatique
    allowed_email_domains = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Domaines email autorisés",
        help_text="Liste des domaines email autorisés pour l'inscription automatique"
    )
    
    # Paramètres de notification
    notification_settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Paramètres de notification"
    )
    
    # Paramètres de sécurité
    security_settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Paramètres de sécurité"
    )
    
    class Meta:
        verbose_name = "Paramètres d'organisation"
        verbose_name_plural = "Paramètres d'organisation"
        db_table = 'foundation_organization_settings'
    
    def __str__(self):
        return f"Paramètres - {self.organization.name}"
    
    def get_setting(self, key, default=None):
        """Récupère une valeur des paramètres."""
        return self.settings.get(key, default)
    
    def set_setting(self, key, value):
        """Définit une valeur dans les paramètres."""
        self.settings[key] = value
        self.save(update_fields=['settings'])
    
    def update_settings(self, data):
        """Met à jour plusieurs paramètres."""
        self.settings.update(data)
        self.save(update_fields=['settings'])
    
    def is_email_domain_allowed(self, email):
        """Vérifie si un domaine email est autorisé."""
        if not self.allowed_email_domains:
            return False
        
        domain = email.split('@')[-1].lower()
        return domain in [d.lower() for d in self.allowed_email_domains]
