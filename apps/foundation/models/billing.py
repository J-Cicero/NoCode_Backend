"""
Système de facturation et paiements pour la plateforme NoCode.
Gère les moyens de paiement, paiements, factures et historique tarifaire.
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from .base import BaseModel
from .mixins import StatusMixin, MetadataMixin
from decimal import Decimal
import uuid


User = get_user_model()


class MoyenDePaiement(BaseModel, StatusMixin, MetadataMixin):
    """
    Moyens de paiement enregistrés par les utilisateurs.
    """
    TYPE_CHOICES = [
        ('CARTE_CREDIT', 'Carte de crédit'),
        ('PAYPAL', 'PayPal'),
        ('VIREMENT_BANCAIRE', 'Virement bancaire'),
        ('SEPA', 'Prélèvement SEPA'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Actif'),
        ('EXPIRED', 'Expiré'),
        ('INVALID', 'Invalide'),
        ('SUSPENDED', 'Suspendu'),
    ]
    
    # Propriétaire du moyen de paiement
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='moyens_paiement',
        verbose_name="Utilisateur"
    )
    
    # Type de moyen de paiement
    type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        verbose_name="Type de paiement"
    )
    
    # Statut
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        verbose_name="Statut"
    )
    
    # Token du provider (Stripe, PayPal, etc.)
    provider_token = models.CharField(
        max_length=255,
        verbose_name="Token du fournisseur",
        help_text="Token sécurisé du fournisseur de paiement"
    )
    
    # Détails du moyen de paiement (JSON)
    details = models.JSONField(
        default=dict,
        verbose_name="Détails",
        help_text="Informations sur le moyen de paiement (4 derniers chiffres, etc.)"
    )
    
    # Informations d'expiration
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Expire le"
    )
    
    # Moyen de paiement par défaut
    is_default = models.BooleanField(
        default=False,
        verbose_name="Moyen de paiement par défaut"
    )
    
    # Dernière utilisation
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Dernière utilisation"
    )
    
    class Meta:
        verbose_name = "Moyen de paiement"
        verbose_name_plural = "Moyens de paiement"
        db_table = 'foundation_moyen_paiement'
        ordering = ['-is_default', '-last_used_at']
    
    def __str__(self):
        details = self.details.get('last4', '****')
        return f"{self.get_type_display()} - ****{details}"
    
    def save(self, *args, **kwargs):
        """Override save pour gérer le moyen de paiement par défaut."""
        if self.is_default:
            # S'assurer qu'il n'y a qu'un seul moyen de paiement par défaut
            MoyenDePaiement.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Vérifie si le moyen de paiement a expiré."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    @property
    def is_valid(self):
        """Vérifie si le moyen de paiement est valide."""
        return self.status == 'ACTIVE' and not self.is_expired
    
    def mark_as_used(self):
        """Marque le moyen de paiement comme utilisé."""
        self.last_used_at = timezone.now()
        self.save(update_fields=['last_used_at'])


class Paiement(BaseModel, StatusMixin, MetadataMixin):
    """
    Transactions de paiement effectuées sur la plateforme.
    """
    STATUS_CHOICES = [
        ('SUCCES', 'Succès'),
        ('ECHEC', 'Échec'),
        ('EN_COURS', 'En cours'),
        ('REMBOURSE', 'Remboursé'),
        ('ANNULE', 'Annulé'),
        ('EN_ATTENTE', 'En attente'),
    ]
    
    TYPE_CHOICES = [
        ('SUBSCRIPTION', 'Abonnement'),
        ('UPGRADE', 'Mise à niveau'),
        ('RENEWAL', 'Renouvellement'),
        ('REFUND', 'Remboursement'),
    ]
    
    # Lien vers l'abonnement
    abonnement = models.ForeignKey(
        'foundation.Abonnement',
        on_delete=models.CASCADE,
        related_name='paiements',
        verbose_name="Abonnement"
    )
    
    # Moyen de paiement utilisé
    moyen_de_paiement_utilise = models.ForeignKey(
        MoyenDePaiement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paiements',
        verbose_name="Moyen de paiement utilisé"
    )
    
    # Informations du paiement
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Montant (€)"
    )
    
    devise = models.CharField(
        max_length=3,
        default='EUR',
        verbose_name="Devise"
    )
    
    # Type et statut
    type_paiement = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='SUBSCRIPTION',
        verbose_name="Type de paiement"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='EN_ATTENTE',
        verbose_name="Statut"
    )
    
    # Dates importantes
    date_paiement = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date du paiement"
    )
    
    date_traitement = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de traitement"
    )
    
    # Détails du paiement externe (Stripe, PayPal, etc.)
    details_paiement_externe = models.JSONField(
        default=dict,
        verbose_name="Détails du paiement externe",
        help_text="Réponse complète du fournisseur de paiement"
    )
    
    # Identifiants externes
    external_transaction_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="ID Transaction externe"
    )
    
    stripe_payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="ID Payment Intent Stripe"
    )
    
    # Informations de remboursement
    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Montant remboursé (€)"
    )
    
    refund_reason = models.TextField(
        blank=True,
        verbose_name="Raison du remboursement"
    )
    
    refunded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Remboursé le"
    )
    
    # Informations d'erreur
    error_message = models.TextField(
        blank=True,
        verbose_name="Message d'erreur"
    )
    
    error_code = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Code d'erreur"
    )
    
    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        db_table = 'foundation_paiement'
        ordering = ['-date_paiement']
    
    def __str__(self):
        return f"Paiement {self.montant}€ - {self.abonnement.client.email} ({self.status})"
    
    @property
    def is_successful(self):
        """Vérifie si le paiement a réussi."""
        return self.status == 'SUCCES'
    
    @property
    def is_refunded(self):
        """Vérifie si le paiement a été remboursé."""
        return self.status == 'REMBOURSE'
    
    @property
    def can_be_refunded(self):
        """Vérifie si le paiement peut être remboursé."""
        return (self.status == 'SUCCES' and 
                not self.is_refunded and
                self.refund_amount is None)
    
    def mark_as_successful(self, transaction_id=None, details=None):
        """Marque le paiement comme réussi."""
        self.status = 'SUCCES'
        self.date_traitement = timezone.now()
        if transaction_id:
            self.external_transaction_id = transaction_id
        if details:
            self.details_paiement_externe.update(details)
        self.save(update_fields=[
            'status', 'date_traitement', 'external_transaction_id', 
            'details_paiement_externe'
        ])
        
        # Marquer le moyen de paiement comme utilisé
        if self.moyen_de_paiement_utilise:
            self.moyen_de_paiement_utilise.mark_as_used()
    
    def mark_as_failed(self, error_message=None, error_code=None):
        """Marque le paiement comme échoué."""
        self.status = 'ECHEC'
        self.date_traitement = timezone.now()
        if error_message:
            self.error_message = error_message
        if error_code:
            self.error_code = error_code
        self.save(update_fields=[
            'status', 'date_traitement', 'error_message', 'error_code'
        ])
    
    def process_refund(self, amount=None, reason=None):
        """Traite un remboursement."""
        if not self.can_be_refunded:
            raise ValueError("Ce paiement ne peut pas être remboursé")
        
        refund_amount = amount or self.montant
        if refund_amount > self.montant:
            raise ValueError("Le montant du remboursement ne peut pas dépasser le montant du paiement")
        
        self.status = 'REMBOURSE'
        self.refund_amount = refund_amount
        self.refund_reason = reason or ''
        self.refunded_at = timezone.now()
        self.save(update_fields=[
            'status', 'refund_amount', 'refund_reason', 'refunded_at'
        ])


class Facture(BaseModel, StatusMixin, MetadataMixin):
    """
    Factures générées pour les organisations.
    """
    STATUS_CHOICES = [
        ('BROUILLON', 'Brouillon'),
        ('ENVOYEE', 'Envoyée'),
        ('PAYEE', 'Payée'),
        ('ANNULEE', 'Annulée'),
        ('EN_RETARD', 'En retard'),
    ]
    
    # Lien vers l'organisation
    organization = models.ForeignKey(
        'foundation.Organization',
        on_delete=models.CASCADE,
        related_name='factures',
        verbose_name="Organisation"
    )
    
    # Numéro de facture unique
    numero_facture = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Numéro de facture"
    )
    
    # Dates importantes
    date_emission = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'émission"
    )
    
    date_echeance = models.DateTimeField(
        verbose_name="Date d'échéance"
    )
    
    date_paiement = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de paiement"
    )
    
    # Montants
    montant_ht = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Montant HT (€)"
    )
    
    taux_tva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('20.00'),
        verbose_name="Taux TVA (%)"
    )
    
    montant_tva = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Montant TVA (€)"
    )
    
    montant_ttc = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Montant TTC (€)"
    )
    
    devise = models.CharField(
        max_length=3,
        default='EUR',
        verbose_name="Devise"
    )
    
    # Statut
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='BROUILLON',
        verbose_name="Statut"
    )
    
    # Lignes de facturation (JSON)
    lignes_facture = models.JSONField(
        default=list,
        verbose_name="Lignes de facture",
        help_text="Détail des éléments facturés"
    )
    
    # Informations client (snapshot au moment de la facturation)
    client_info = models.JSONField(
        default=dict,
        verbose_name="Informations client",
        help_text="Snapshot des informations client"
    )
    
    # Fichier PDF généré
    fichier_pdf = models.FileField(
        upload_to='factures/',
        null=True,
        blank=True,
        verbose_name="Fichier PDF"
    )
    
    # Notes et commentaires
    notes = models.TextField(
        blank=True,
        verbose_name="Notes"
    )
    
    # Intégration externe
    stripe_invoice_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="ID Facture Stripe"
    )
    
    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        db_table = 'foundation_facture'
        ordering = ['-date_emission']
    
    def __str__(self):
        return f"Facture {self.numero_facture} - {self.organization.name}"
    
    def save(self, *args, **kwargs):
        """Override save pour générer le numéro de facture et calculer les montants."""
        if not self.numero_facture:
            self.numero_facture = self.generate_numero_facture()
        
        # Calculer les montants si pas déjà fait
        if self.montant_ht and not self.montant_tva:
            self.montant_tva = (self.montant_ht * self.taux_tva) / 100
            self.montant_ttc = self.montant_ht + self.montant_tva
        
        # Définir la date d'échéance si pas définie (30 jours par défaut)
        if not self.date_echeance:
            self.date_echeance = timezone.now() + timezone.timedelta(days=30)
        
        super().save(*args, **kwargs)
    
    def generate_numero_facture(self):
        """Génère un numéro de facture unique."""
        year = timezone.now().year
        month = timezone.now().month
        
        # Compter les factures du mois
        count = Facture.objects.filter(
            date_emission__year=year,
            date_emission__month=month
        ).count() + 1
        
        return f"FAC-{year}{month:02d}-{count:04d}"
    
    @property
    def is_overdue(self):
        """Vérifie si la facture est en retard."""
        return (self.status in ['ENVOYEE'] and 
                timezone.now() > self.date_echeance)
    
    @property
    def days_until_due(self):
        """Retourne le nombre de jours avant échéance."""
        if self.status == 'PAYEE':
            return 0
        return (self.date_echeance - timezone.now()).days
    
    def mark_as_paid(self, payment_date=None):
        """Marque la facture comme payée."""
        self.status = 'PAYEE'
        self.date_paiement = payment_date or timezone.now()
        self.save(update_fields=['status', 'date_paiement'])
    
    def send_invoice(self):
        """Envoie la facture au client."""
        if self.status == 'BROUILLON':
            self.status = 'ENVOYEE'
            self.save(update_fields=['status'])
            # TODO: Implémenter l'envoi par email
    
    def cancel_invoice(self, reason=None):
        """Annule la facture."""
        if self.status in ['BROUILLON', 'ENVOYEE']:
            self.status = 'ANNULEE'
            if reason:
                self.notes = f"{self.notes}\nAnnulée: {reason}".strip()
            self.save(update_fields=['status', 'notes'])


class HistoriqueTarification(BaseModel):
    """
    Historique des changements de tarification.
    """
    # Type d'abonnement concerné
    type_abonnement = models.ForeignKey(
        'foundation.TypeAbonnement',
        on_delete=models.CASCADE,
        related_name='historique_tarification',
        verbose_name="Type d'abonnement"
    )
    
    # Anciens et nouveaux tarifs
    ancien_tarif = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Ancien tarif (€)"
    )
    
    nouveau_tarif = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Nouveau tarif (€)"
    )
    
    # Date du changement
    date_changement = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date du changement"
    )
    
    # Raison du changement
    raison = models.TextField(
        verbose_name="Raison du changement"
    )
    
    # Qui a effectué le changement
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Modifié par"
    )
    
    class Meta:
        verbose_name = "Historique de tarification"
        verbose_name_plural = "Historiques de tarification"
        db_table = 'foundation_historique_tarification'
        ordering = ['-date_changement']
    
    def __str__(self):
        return f"{self.type_abonnement} - {self.ancien_tarif}€ → {self.nouveau_tarif}€"
    
    @property
    def variation_percentage(self):
        """Calcule le pourcentage de variation."""
        if self.ancien_tarif == 0:
            return 0
        return round(((self.nouveau_tarif - self.ancien_tarif) / self.ancien_tarif) * 100, 2)
    
    @property
    def is_increase(self):
        """Vérifie si c'est une augmentation."""
        return self.nouveau_tarif > self.ancien_tarif
    
    @property
    def is_decrease(self):
        """Vérifie si c'est une diminution."""
        return self.nouveau_tarif < self.ancien_tarif
