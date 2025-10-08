"""
Système d'utilisateurs personnalisé pour la plateforme NoCode.
Gère les utilisateurs Client (personnes physiques) et Entreprise (personnes morales).
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
 
 


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé de base.
    Utilise l'email comme identifiant principal au lieu du username.
    """
    # Supprimer le champ username
    username = None
    
    # Email comme identifiant principal
    email = models.EmailField(
        unique=True,
        verbose_name="Adresse email",
        help_text="Adresse email utilisée pour la connexion"
    )
    
    # Configuration de l'authentification
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        db_table = 'foundation_user'
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        """Retourne le nom complet de l'utilisateur."""
        if hasattr(self, 'client') and self.client:
            return f"{self.client.prenom} {self.client.nom}"
        elif hasattr(self, 'entreprise') and self.entreprise:
            return self.entreprise.nom_entreprise
        return self.email
    
    @property
    def user_type(self):
        """Retourne le type d'utilisateur (CLIENT ou ENTREPRISE)."""
        if hasattr(self, 'client') and self.client:
            return 'CLIENT'
        elif hasattr(self, 'entreprise') and self.entreprise:
            return 'ENTREPRISE'
        return 'UNKNOWN'
    
    def get_display_name(self):
        """Retourne le nom d'affichage approprié."""
        return self.full_name
    
    def can_access_enterprise_features(self):
        """Vérifie si l'utilisateur peut accéder aux fonctionnalités entreprise."""
        if self.user_type == 'ENTREPRISE':
            return self.entreprise.est_verifiee
        return False


class Client(models.Model):
    """
    Profil Client - Personne physique.
    Extension du modèle User pour les particuliers.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='client'
    )
    
    # Champs obligatoires pour les clients
    nom = models.CharField(
        max_length=255,
        verbose_name="Nom de famille"
    )
    
    prenom = models.CharField(
        max_length=255,
        verbose_name="Prénom"
    )
    
    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        db_table = 'foundation_client'
    
    def __str__(self):
        return f"{self.prenom} {self.nom}"
    
    @property
    def nom_complet(self):
        """Retourne le nom complet du client."""
        return f"{self.prenom} {self.nom}"
    
    @property
    def nom_affichage(self):
        """Retourne le nom d'affichage (nom complet)."""
        return self.nom_complet


class Entreprise(models.Model):
    """
    Profil Entreprise - Personne morale.
    Extension du modèle User pour les entreprises.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='entreprise'
    )
    
    # Champs obligatoires pour les entreprises
    nom_entreprise = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Nom de l'entreprise"
    )
    
    # Statut de vérification (minimal)
    est_verifiee = models.BooleanField(
        default=False,
        verbose_name="Entreprise vérifiée"
    )
    
    class Meta:
        verbose_name = "Entreprise"
        verbose_name_plural = "Entreprises"
        db_table = 'foundation_entreprise'
    
    def __str__(self):
        return self.nom_entreprise
