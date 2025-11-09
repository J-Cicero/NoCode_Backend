"""
Système d'utilisateurs personnalisé pour la plateforme NoCode.
Gère les utilisateurs Client (personnes physiques). Les organisations sont gérées via le modèle Organization.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class User(AbstractUser):
    username = None
    first_name = None
    last_name = None
    
    tracking_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name="ID de suivi",
        help_text="Identifiant public unique pour les requêtes API"
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
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        return f"{self.prenom} {self.nom}"
    
    @property
    def user_type(self):
        if hasattr(self, 'client') and self.client:
            return 'CLIENT'
        return 'UNKNOWN'
    
    def get_display_name(self):
        return self.full_name
    
    def can_access_organization_features(self):
        return hasattr(self, 'organization_members') and self.organization_members.exists()


class Client(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='client'
    )
    
    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        db_table = 'foundation_client'
    
    def __str__(self):
        return f"{self.user.prenom} {self.user.nom}"
    
    @property
    def nom_complet(self):
        return f"{self.user.prenom} {self.user.nom}"
    
    @property
    def nom_affichage(self):
        return self.nom_complet


