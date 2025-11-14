from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
import uuid
from .base import BaseModel

class User(BaseModel, AbstractUser):
    """Utilisateur du système (CLIENT ou ADMIN)"""
    username = None
    first_name = None
    last_name = None
    
    ROLE_CHOICES = [
        ('CLIENT', 'Client'),
        ('ADMIN', 'Administrateur'),
    ]
    
    tracking_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Tracking ID",
        help_text="Identifiant public unique utilisé dans les URLs et APIs"
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='CLIENT',
        verbose_name="Rôle"
    )
    
    email = models.EmailField(
        unique=True,
        verbose_name="Adresse email",
        help_text="L'adresse email est utilisée comme identifiant de connexion."
    )
    
    nom = models.CharField(
        max_length=255,
        verbose_name="Nom de famille"
    )
    
    prenom = models.CharField(
        max_length=255,
        verbose_name="Prénom"
    )
    
    numero_telephone = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?\d{8,15}$',
                message="Le numéro de téléphone doit contenir entre 8 et 15 chiffres.",
                code='invalid_phone'
            )
        ],
        verbose_name="Numéro de téléphone",
        unique=True
    )
    
    pays = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Pays"
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom', 'prenom']
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        db_table = 'foundation_user'
        indexes = [
            models.Index(fields=['tracking_id']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        return f"{self.prenom} {self.nom}"
    
    @property
    def is_admin(self):
        """Vérifie si l'utilisateur est admin"""
        return self.role == 'ADMIN' or self.is_superuser
    
    @property
    def is_client(self):
        """Vérifie si l'utilisateur est client"""
        return self.role == 'CLIENT'
    
    def get_display_name(self):
        return self.full_name
    
    def get_organizations(self):
        """Retourne les organisations dont l'utilisateur est membre"""
        return self.organization_memberships.filter(status='ACTIVE').select_related('organization')