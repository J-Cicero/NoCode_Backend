
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from .base import BaseModel
from decimal import Decimal
import uuid

User = get_user_model()

class TypeAbonnement(BaseModel):

    tracking_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Tracking ID",
        help_text="Identifiant public unique utilisé dans les URLs et APIs"
    )

    NOM_CHOICES = [
        ('FREE', 'Gratuit'),
        ('MENSUEL', 'Mensuel'),
        ('ANNUEL', 'Annuel'),
    ]
    
    CATEGORIE_CHOICES = [
        ('CLIENT', 'Client'),
        ('ORGANIZATION', 'Organisation'),
    ]
    
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
    
    tarif = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Tarif (FCFA)"
    )
    
    duree_en_jours = models.PositiveIntegerField(
        verbose_name="Durée en jours"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Plan actif",
        help_text="Indique si ce plan peut être souscrit"
    )
    
    class Meta:
        verbose_name = "Type d'abonnement"
        verbose_name_plural = "Types d'abonnement"
        db_table = 'foundation_type_abonnement'
        unique_together = ['nom', 'categorie_utilisateur']
        ordering = ['tarif']
    
    def __str__(self):
        return f"{self.get_nom_display()} - {self.get_categorie_utilisateur_display()}"
    
    @property
    def is_free(self):
        return self.nom == 'FREE' or self.tarif == 0


class Abonnement(BaseModel):

    tracking_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Tracking ID",
        help_text="Identifiant public unique utilisé dans les URLs et APIs"
    )

    STATUS_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('ACTIF', 'Actif'),
        ('EXPIRE', 'Expiré'),
        ('ANNULE', 'Annulé'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='abonnements',
        verbose_name="Utilisateur",
        help_text="Utilisateur souscripteur (propriétaire de l'organisation)"
    )
    
    type_abonnement = models.ForeignKey(
        TypeAbonnement,
        on_delete=models.PROTECT,
        related_name='abonnements',
        verbose_name="Type d'abonnement"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='EN_ATTENTE',
        verbose_name="Statut"
    )

    date_debut = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de début"
    )
    
    date_fin = models.DateTimeField(
        verbose_name="Date de fin"
    )
    
    transaction_reference = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Référence de transaction",
        help_text="Référence de la transaction de paiement (API bancaire)"
    )
    
    montant_paye = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant payé",
        help_text="Montant réellement payé pour cet abonnement"
    )
    
    date_annulation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'annulation"
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
        if self.organization:
            return f"Organisation: {self.organization.name} - {self.type_abonnement} ({self.status})"
        return f"User: {self.user.email} - {self.type_abonnement} ({self.status})"
    
    def save(self, *args, **kwargs):
        if not self.date_fin and self.type_abonnement:
            from datetime import timedelta
            self.date_fin = self.date_debut + timedelta(
                days=self.type_abonnement.duree_en_jours
            )
        if not self.montant_paye and self.type_abonnement:
            self.montant_paye = self.type_abonnement.tarif
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        return (self.status == 'ACTIF' and
                timezone.now() <= self.date_fin)
    
    @property
    def is_expired(self):
        return timezone.now() > self.date_fin
    
    @property
    def days_remaining(self):
        if self.is_expired:
            return 0
        return (self.date_fin - timezone.now()).days
    
    @property
    def usage_percentage(self):
        if self.status != 'ACTIF':
            return 0
        total = (self.date_fin - self.date_debut).total_seconds()
        if total <= 0:
            return 100
        elapsed = (timezone.now() - self.date_debut).total_seconds()
        return min(100, (elapsed / total) * 100)
    
    def cancel(self, reason='', cancelled_by=None):
        """Annule l'abonnement"""
        self.status = 'ANNULE'
        self.date_annulation = timezone.now()
        if cancelled_by:
            self.cancelled_by = cancelled_by
        self.save(update_fields=['status', 'date_annulation', 'cancelled_by'])
    
    def check_limit(self, limit_type, current_usage):
        """Vérifie si une limite est respectée"""
        # Pour l'instant, retourne toujours True (pas de limites strictes)
        # À implémenter selon les besoins réels
        return True
    
    def get_limits(self):
        """Retourne les limites de l'abonnement"""
        # Retourne un dict vide pour l'instant
        # À implémenter selon les besoins réels
        return {}
