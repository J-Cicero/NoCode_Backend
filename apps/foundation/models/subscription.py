"""
Système d'abonnements pour la plateforme NoCode.
Gère les types d'abonnements et les souscriptions actives.
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from .base import BaseModel
from .mixins import StatusMixin, MetadataMixin
from decimal import Decimal


User = get_user_model()


class TypeAbonnement(BaseModel, MetadataMixin):
    """
    Types d'abonnements disponibles sur la plateforme.
    Définit les plans tarifaires pour clients individuels et entreprises.
    """
    NOM_CHOICES = [
        ('FREE', 'Gratuit'),
        ('MENSUEL', 'Mensuel'),
        ('ANNUEL', 'Annuel'),
    ]
    
    CATEGORIE_CHOICES = [
        ('CLIENT_INDIVIDUEL', 'Client individuel'),
        ('CLIENT_ENTREPRISE', 'Client entreprise'),
    ]
    
    # Identification du plan
    nom = models.CharField(
        max_length=50,
        choices=NOM_CHOICES,
        verbose_name="Nom du plan"
    )
    
    categorie_utilisateur = models.CharField(
        max_length=50,
        choices=CATEGORIE_CHOICES,
        verbose_name="Catégorie d'utilisateur"
    )
    
    # Informations tarifaires
    tarif = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Tarif (€)",
        help_text="Prix en euros"
    )
    
    duree_en_jours = models.PositiveIntegerField(
        verbose_name="Durée en jours",
        help_text="Durée de validité de l'abonnement"
    )
    
    # Informations descriptives
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    features = models.JSONField(
        default=list,
        verbose_name="Fonctionnalités incluses",
        help_text="Liste des fonctionnalités incluses dans ce plan"
    )
    
    # Limites du plan
    max_projects = models.PositiveIntegerField(
        default=1,
        verbose_name="Nombre maximum de projets"
    )
    
    max_tables_per_project = models.PositiveIntegerField(
        default=5,
        verbose_name="Nombre maximum de tables par projet"
    )
    
    max_records_per_table = models.PositiveIntegerField(
        default=1000,
        verbose_name="Nombre maximum d'enregistrements par table"
    )
    
    max_api_calls_per_month = models.PositiveIntegerField(
        default=10000,
        verbose_name="Nombre maximum d'appels API par mois"
    )
    
    max_storage_mb = models.PositiveIntegerField(
        default=100,
        verbose_name="Stockage maximum (MB)"
    )
    
    # Paramètres du plan
    is_active = models.BooleanField(
        default=True,
        verbose_name="Plan actif",
        help_text="Indique si ce plan peut être souscrit"
    )
    
    is_popular = models.BooleanField(
        default=False,
        verbose_name="Plan populaire",
        help_text="Marque ce plan comme populaire dans l'interface"
    )
    
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre d'affichage"
    )
    
    # Intégration Stripe
    stripe_price_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="ID Prix Stripe",
        help_text="Identifiant du prix dans Stripe"
    )
    
    stripe_product_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="ID Produit Stripe",
        help_text="Identifiant du produit dans Stripe"
    )
    
    class Meta:
        verbose_name = "Type d'abonnement"
        verbose_name_plural = "Types d'abonnement"
        db_table = 'foundation_type_abonnement'
        unique_together = ['nom', 'categorie_utilisateur']
        ordering = ['sort_order', 'tarif']
    
    def __str__(self):
        return f"{self.get_nom_display()} - {self.get_categorie_utilisateur_display()}"
    
    @property
    def is_free(self):
        """Vérifie si le plan est gratuit."""
        return self.nom == 'FREE' or self.tarif == 0
    
    @property
    def tarif_mensuel_equivalent(self):
        """Calcule le tarif mensuel équivalent."""
        if self.duree_en_jours == 0:
            return Decimal('0.00')
        return (self.tarif * 30) / self.duree_en_jours
    
    @property
    def discount_percentage(self):
        """Calcule le pourcentage de réduction par rapport au plan mensuel."""
        if self.nom == 'ANNUEL':
            try:
                monthly_plan = TypeAbonnement.objects.get(
                    nom='MENSUEL',
                    categorie_utilisateur=self.categorie_utilisateur
                )
                monthly_yearly_cost = monthly_plan.tarif * 12
                if monthly_yearly_cost > 0:
                    return round(((monthly_yearly_cost - self.tarif) / monthly_yearly_cost) * 100, 1)
            except TypeAbonnement.DoesNotExist:
                pass
        return 0
    
    def can_be_subscribed_by(self, user):
        """Vérifie si un utilisateur peut souscrire à ce plan."""
        if not self.is_active:
            return False
        
        # Vérifier la catégorie d'utilisateur
        if self.categorie_utilisateur == 'CLIENT_ENTREPRISE':
            return (hasattr(user, 'entreprise') and 
                   user.entreprise and 
                   user.entreprise.est_verifiee)
        
        return True


class Abonnement(BaseModel, StatusMixin, MetadataMixin):
    """
    Abonnements actifs des utilisateurs.
    Lie un utilisateur/organisation à un type d'abonnement.
    """
    STATUS_CHOICES = [
        ('ACTIF', 'Actif'),
        ('EXPIRE', 'Expiré'),
        ('ANNULE', 'Annulé'),
        ('EN_ATTENTE', 'En attente'),
        ('SUSPENDU', 'Suspendu'),
    ]
    
    # Lien vers l'utilisateur (Client ou Entreprise)
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='abonnements',
        verbose_name="Client"
    )
    
    # Lien vers l'organisation (nouveau champ pour multi-tenancy)
    organization = models.ForeignKey(
        'foundation.Organization',
        on_delete=models.CASCADE,
        related_name='abonnements',
        verbose_name="Organisation"
    )
    
    # Type d'abonnement souscrit
    type_abonnement = models.ForeignKey(
        TypeAbonnement,
        on_delete=models.PROTECT,
        related_name='abonnements',
        verbose_name="Type d'abonnement"
    )
    
    # Statut de l'abonnement
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='EN_ATTENTE',
        verbose_name="Statut"
    )
    
    # Dates importantes
    date_debut = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de début"
    )
    
    date_fin = models.DateTimeField(
        verbose_name="Date de fin"
    )
    
    date_activation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'activation"
    )
    
    date_annulation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'annulation"
    )
    
    # Informations de facturation
    montant_paye = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Montant payé (€)"
    )
    
    devise = models.CharField(
        max_length=3,
        default='EUR',
        verbose_name="Devise"
    )
    
    # Renouvellement automatique
    auto_renewal = models.BooleanField(
        default=True,
        verbose_name="Renouvellement automatique"
    )
    
    # Intégration Stripe
    stripe_subscription_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="ID Abonnement Stripe"
    )
    
    stripe_customer_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="ID Client Stripe"
    )
    
    # Historique des changements
    previous_subscription = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Abonnement précédent"
    )
    
    # Raison de l'annulation
    cancellation_reason = models.TextField(
        blank=True,
        verbose_name="Raison de l'annulation"
    )
    
    cancelled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_subscriptions',
        verbose_name="Annulé par"
    )
    
    class Meta:
        verbose_name = "Abonnement"
        verbose_name_plural = "Abonnements"
        db_table = 'foundation_abonnement'
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"{self.client.email} - {self.type_abonnement} ({self.status})"
    
    def save(self, *args, **kwargs):
        """Override save pour calculer la date de fin."""
        if not self.date_fin and self.type_abonnement:
            self.date_fin = self.date_debut + timezone.timedelta(
                days=self.type_abonnement.duree_en_jours
            )
        
        if not self.montant_paye and self.type_abonnement:
            self.montant_paye = self.type_abonnement.tarif
        
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        """Vérifie si l'abonnement est actif."""
        return (self.status == 'ACTIF' and 
                timezone.now() <= self.date_fin)
    
    @property
    def is_expired(self):
        """Vérifie si l'abonnement a expiré."""
        return timezone.now() > self.date_fin
    
    @property
    def days_remaining(self):
        """Retourne le nombre de jours restants."""
        if self.is_expired:
            return 0
        return (self.date_fin - timezone.now()).days
    
    @property
    def usage_percentage(self):
        """Retourne le pourcentage d'utilisation de l'abonnement."""
        if self.status != 'ACTIF':
            return 0
        
        total_duration = (self.date_fin - self.date_debut).total_seconds()
        elapsed_duration = (timezone.now() - self.date_debut).total_seconds()
        
        if total_duration <= 0:
            return 100
        
        return min(100, (elapsed_duration / total_duration) * 100)
    
    def activate(self):
        """Active l'abonnement."""
        if self.status == 'EN_ATTENTE':
            self.status = 'ACTIF'
            self.date_activation = timezone.now()
            self.save(update_fields=['status', 'date_activation'])
    
    def cancel(self, reason=None, cancelled_by=None):
        """Annule l'abonnement."""
        if self.status in ['ACTIF', 'EN_ATTENTE']:
            self.status = 'ANNULE'
            self.date_annulation = timezone.now()
            self.cancellation_reason = reason or ''
            self.cancelled_by = cancelled_by
            self.auto_renewal = False
            self.save(update_fields=[
                'status', 'date_annulation', 'cancellation_reason', 
                'cancelled_by', 'auto_renewal'
            ])
    
    def suspend(self, reason=None):
        """Suspend l'abonnement."""
        if self.status == 'ACTIF':
            self.status = 'SUSPENDU'
            if reason:
                self.cancellation_reason = reason
            self.save(update_fields=['status', 'cancellation_reason'])
    
    def reactivate(self):
        """Réactive un abonnement suspendu."""
        if self.status == 'SUSPENDU' and not self.is_expired:
            self.status = 'ACTIF'
            self.save(update_fields=['status'])
    
    def renew(self, new_type_abonnement=None):
        """Renouvelle l'abonnement."""
        if not self.auto_renewal:
            return None
        
        # Créer un nouvel abonnement
        new_subscription = Abonnement.objects.create(
            client=self.client,
            organization=self.organization,
            type_abonnement=new_type_abonnement or self.type_abonnement,
            status='EN_ATTENTE',
            date_debut=self.date_fin,
            auto_renewal=self.auto_renewal,
            previous_subscription=self
        )
        
        return new_subscription
    
    def get_limits(self):
        """Retourne les limites de l'abonnement."""
        return {
            'max_projects': self.type_abonnement.max_projects,
            'max_tables_per_project': self.type_abonnement.max_tables_per_project,
            'max_records_per_table': self.type_abonnement.max_records_per_table,
            'max_api_calls_per_month': self.type_abonnement.max_api_calls_per_month,
            'max_storage_mb': self.type_abonnement.max_storage_mb,
        }
    
    def check_limit(self, limit_type, current_usage):
        """Vérifie si une limite est atteinte."""
        limits = self.get_limits()
        limit_value = limits.get(limit_type, 0)
        
        if limit_value == 0:  # Illimité
            return True
        
        return current_usage < limit_value
    
    def get_renewal_date(self):
        """Retourne la date de renouvellement prévue."""
        if self.auto_renewal and self.status == 'ACTIF':
            return self.date_fin
        return None
