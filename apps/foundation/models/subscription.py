"""
Système d'abonnements pour la plateforme NoCode.
Gère les types d'abonnements et les souscriptions actives.
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from .base import BaseModel
from decimal import Decimal


User = get_user_model()


class TypeAbonnement(BaseModel):

    NOM_CHOICES = [
        ('FREE', 'Gratuit'),
        ('MENSUEL', 'Mensuel'),
        ('ANNUEL', 'Annuel'),
    ]
    
    CATEGORIE_CHOICES = [
        ('CLIENT', 'Client '),
        ('ORGANIZATION', 'Organisation '),
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
        verbose_name="Tarif (fcfa)"
    )
    
    duree_en_jours = models.PositiveIntegerField(
        verbose_name="Durée en jours"
    )
    
    # Description optionnelle
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    # Paramètre du plan
    is_active = models.BooleanField(
        default=True,
        verbose_name="Plan actif",
        help_text="Indique si ce plan peut être souscrit"
    )
    
    
    class Meta:
        verbose_name = "Type d'abonnement"
        verbose_name_plural = "Types d'abonnement"
        db_table = 'type_abonnement'
        unique_together = ['nom', 'categorie_utilisateur']
        ordering = ['tarif']
    
    def __str__(self):
        return f"{self.get_nom_display()} - {self.get_categorie_utilisateur_display()}"
    
    @property
    def is_free(self):
        return self.nom == 'FREE' or self.tarif == 0


class Abonnement(BaseModel):

    STATUS_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('ACTIF', 'Actif'),
        ('EXPIRE', 'Expiré'),
        ('ANNULE', 'Annulé'),
    ]
    
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='abonnements',
        verbose_name="Client"
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
    
    class Meta:
        verbose_name = "Abonnement"
        verbose_name_plural = "Abonnements"
        db_table = 'foundation_abonnement'
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"{self.client.email} - {self.type_abonnement} ({self.status})"
    
    def save(self, *args, **kwargs):
        if not self.date_fin and self.type_abonnement:
            self.date_fin = self.date_debut + timezone.timedelta(
                days=self.type_abonnement.duree_en_jours
            )
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
