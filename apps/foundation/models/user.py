"""
Système d'utilisateurs personnalisé pour la plateforme NoCode.
Gère les utilisateurs Client (personnes physiques) et Entreprise (personnes morales).
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from .base import BaseModel
from .mixins import StatusMixin, MetadataMixin


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
    
    # Champs obligatoires selon les spécifications
    pays = models.CharField(
        max_length=100,
        verbose_name="Pays",
        help_text="Pays de résidence"
    )
    
    numero_telephone = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Le numéro de téléphone doit être au format international (+33123456789)"
            )
        ],
        verbose_name="Numéro de téléphone",
        help_text="Numéro de téléphone au format international"
    )
    
    # Champs additionnels
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name="Avatar"
    )
    
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
        verbose_name="Langue préférée"
    )
    
    # Paramètres de notification
    email_notifications = models.BooleanField(
        default=True,
        verbose_name="Notifications par email"
    )
    
    marketing_emails = models.BooleanField(
        default=False,
        verbose_name="Emails marketing"
    )
    
    # Métadonnées pour informations supplémentaires
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées utilisateur"
    )
    
    # Configuration de l'authentification
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['pays', 'numero_telephone']
    
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
    
    # Champ optionnel
    surnom = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Surnom",
        help_text="Nom d'affichage préféré (optionnel)"
    )
    
    # Informations personnelles additionnelles
    date_naissance = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de naissance"
    )
    
    profession = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Profession"
    )
    
    # Adresse
    adresse_ligne1 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Adresse ligne 1"
    )
    
    adresse_ligne2 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Adresse ligne 2"
    )
    
    ville = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Ville"
    )
    
    code_postal = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Code postal"
    )
    
    # Préférences client
    newsletter = models.BooleanField(
        default=True,
        verbose_name="Inscription newsletter"
    )
    
    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        db_table = 'foundation_client'
    
    def __str__(self):
        if self.surnom:
            return f"{self.prenom} '{self.surnom}' {self.nom}"
        return f"{self.prenom} {self.nom}"
    
    @property
    def nom_complet(self):
        """Retourne le nom complet du client."""
        return f"{self.prenom} {self.nom}"
    
    @property
    def nom_affichage(self):
        """Retourne le nom d'affichage préféré."""
        return self.surnom if self.surnom else self.nom_complet


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
    
    # Champs optionnels mais importants
    numero_siret = models.CharField(
        max_length=14,
        unique=True,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\d{14}$',
                message="Le numéro SIRET doit contenir exactement 14 chiffres"
            )
        ],
        verbose_name="Numéro SIRET",
        help_text="Numéro SIRET à 14 chiffres"
    )
    
    site_web = models.URLField(
        blank=True,
        null=True,
        verbose_name="Site web",
        help_text="URL du site web de l'entreprise"
    )
    
    # Statut de vérification
    est_verifiee = models.BooleanField(
        default=False,
        verbose_name="Entreprise vérifiée",
        help_text="Indique si l'entreprise a été vérifiée administrativement"
    )
    
    date_verification = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de vérification"
    )
    
    # Informations entreprise
    secteur_activite = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Secteur d'activité"
    )
    
    taille_entreprise = models.CharField(
        max_length=50,
        choices=[
            ('TPE', 'Très petite entreprise (1-9 salariés)'),
            ('PME', 'Petite et moyenne entreprise (10-249 salariés)'),
            ('ETI', 'Entreprise de taille intermédiaire (250-4999 salariés)'),
            ('GE', 'Grande entreprise (5000+ salariés)'),
        ],
        blank=True,
        verbose_name="Taille de l'entreprise"
    )
    
    # Adresse siège social
    adresse_siege_ligne1 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Adresse siège ligne 1"
    )
    
    adresse_siege_ligne2 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Adresse siège ligne 2"
    )
    
    ville_siege = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Ville du siège"
    )
    
    code_postal_siege = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Code postal du siège"
    )
    
    # Contact entreprise
    telephone_entreprise = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Téléphone entreprise"
    )
    
    email_entreprise = models.EmailField(
        blank=True,
        verbose_name="Email entreprise",
        help_text="Email de contact général de l'entreprise"
    )
    
    # Informations légales

    forme_juridique = models.CharField(
        max_length=100,
        choices=[
            ('SARL', 'SARL'),
            ('SAS', 'SAS'),
            ('SA', 'SA'),
            ('SNC', 'SNC'),
            ('EURL', 'EURL'),
            ('SASU', 'SASU'),
            ('EI', 'Entreprise individuelle'),
            ('MICRO', 'Micro-entreprise'),
            ('AUTRE', 'Autre'),
        ],
        blank=True,
        verbose_name="Forme juridique"
    )
    
    capital_social = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Capital social (€)"
    )
    
    # Métadonnées pour informations supplémentaires
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées entreprise"
    )
    
    class Meta:
        verbose_name = "Entreprise"
        verbose_name_plural = "Entreprises"
        db_table = 'foundation_entreprise'
    
    def __str__(self):
        return self.nom_entreprise
    
    def save(self, *args, **kwargs):
        """Override save pour nettoyer le SIRET."""
        if self.numero_siret:
            # Nettoyer le SIRET (supprimer espaces et caractères non numériques)
            self.numero_siret = ''.join(filter(str.isdigit, self.numero_siret))
        super().save(*args, **kwargs)
    
    @property
    def siret_formate(self):
        """Retourne le SIRET formaté avec espaces."""
        if self.numero_siret and len(self.numero_siret) == 14:
            return f"{self.numero_siret[:3]} {self.numero_siret[3:6]} {self.numero_siret[6:9]} {self.numero_siret[9:]}"
        return self.numero_siret
    
    @property
    def adresse_complete_siege(self):
        """Retourne l'adresse complète du siège."""
        adresse_parts = []
        if self.adresse_siege_ligne1:
            adresse_parts.append(self.adresse_siege_ligne1)
        if self.adresse_siege_ligne2:
            adresse_parts.append(self.adresse_siege_ligne2)
        if self.code_postal_siege and self.ville_siege:
            adresse_parts.append(f"{self.code_postal_siege} {self.ville_siege}")
        return ", ".join(adresse_parts)
    
    def peut_souscrire_abonnement_entreprise(self):
        """Vérifie si l'entreprise peut souscrire à un abonnement entreprise."""
        return self.est_verifiee
    
    def initier_verification(self):
        """Initie le processus de vérification de l'entreprise."""
        if not self.est_verifiee:
            # Créer une demande de vérification
            from .verification import DocumentVerification
            verification, created = DocumentVerification.objects.get_or_create(
                entreprise=self,
                defaults={
                    'status': 'PENDING',
                    'documents_requis': ['kbis', 'statuts', 'id_dirigeant']
                }
            )
            return verification
        return None
