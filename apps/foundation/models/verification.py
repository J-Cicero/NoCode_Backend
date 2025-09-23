"""
Système de vérification des entreprises.
Gère l'upload et la validation des documents officiels pour les entreprises.
"""
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from .base import BaseModel
from .mixins import StatusMixin, MetadataMixin
import os


User = get_user_model()


class DocumentVerification(BaseModel, StatusMixin, MetadataMixin):
    """
    Processus de vérification d'une entreprise.
    Gère l'ensemble du workflow de vérification.
    """
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('IN_REVIEW', 'En cours de révision'),
        ('VERIFIED', 'Vérifiée'),
        ('REJECTED', 'Rejetée'),
        ('INCOMPLETE', 'Incomplète'),
    ]
    
    # Lien vers l'entreprise
    entreprise = models.OneToOneField(
        'foundation.Entreprise',
        on_delete=models.CASCADE,
        related_name='verification',
        verbose_name="Entreprise"
    )
    
    # Documents requis pour la vérification
    documents_requis = models.JSONField(
        default=list,
        verbose_name="Documents requis",
        help_text="Liste des types de documents requis: ['kbis', 'statuts', 'id_dirigeant']"
    )
    
    # Documents uploadés (mapping type -> path)
    documents_uploaded = models.JSONField(
        default=dict,
        verbose_name="Documents uploadés",
        help_text="Mapping des documents uploadés: {'kbis': 'path/file.pdf'}"
    )
    
    # Statut de la vérification
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Statut"
    )
    
    # Informations de révision
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_verifications',
        verbose_name="Révisé par"
    )
    
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Révisé le"
    )
    
    # Raison du rejet
    rejection_reason = models.TextField(
        blank=True,
        verbose_name="Raison du rejet"
    )
    
    # Notes administratives
    notes_admin = models.TextField(
        blank=True,
        verbose_name="Notes administratives"
    )
    
    # Dates importantes
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Soumis le"
    )
    
    deadline = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date limite",
        help_text="Date limite pour compléter la vérification"
    )
    
    # Tentatives de vérification
    attempt_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de tentatives"
    )
    
    max_attempts = models.PositiveIntegerField(
        default=3,
        verbose_name="Nombre maximum de tentatives"
    )
    
    class Meta:
        verbose_name = "Vérification de document"
        verbose_name_plural = "Vérifications de documents"
        db_table = 'foundation_document_verification'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Vérification {self.entreprise.nom_entreprise} ({self.status})"
    
    def save(self, *args, **kwargs):
        """Override save pour définir la deadline."""
        if not self.deadline and self.status == 'PENDING':
            # 30 jours pour compléter la vérification
            self.deadline = timezone.now() + timezone.timedelta(days=30)
        
        super().save(*args, **kwargs)
    
    @property
    def is_complete(self):
        """Vérifie si tous les documents requis sont uploadés."""
        return all(
            doc_type in self.documents_uploaded 
            for doc_type in self.documents_requis
        )
    
    @property
    def completion_percentage(self):
        """Retourne le pourcentage de completion."""
        if not self.documents_requis:
            return 100
        
        uploaded_count = sum(
            1 for doc_type in self.documents_requis 
            if doc_type in self.documents_uploaded
        )
        return (uploaded_count / len(self.documents_requis)) * 100
    
    @property
    def missing_documents(self):
        """Retourne la liste des documents manquants."""
        return [
            doc_type for doc_type in self.documents_requis
            if doc_type not in self.documents_uploaded
        ]
    
    @property
    def is_expired(self):
        """Vérifie si la deadline est dépassée."""
        return self.deadline and timezone.now() > self.deadline
    
    @property
    def can_be_submitted(self):
        """Vérifie si la vérification peut être soumise."""
        return (self.status == 'PENDING' and 
                self.is_complete and 
                not self.is_expired)
    
    @property
    def can_retry(self):
        """Vérifie si une nouvelle tentative est possible."""
        return (self.status == 'REJECTED' and 
                self.attempt_count < self.max_attempts)
    
    def submit_for_review(self):
        """Soumet la vérification pour révision."""
        if not self.can_be_submitted:
            raise ValueError("La vérification ne peut pas être soumise")
        
        self.status = 'IN_REVIEW'
        self.submitted_at = timezone.now()
        self.attempt_count += 1
        self.save(update_fields=['status', 'submitted_at', 'attempt_count'])
    
    def approve(self, admin_user, notes=None):
        """Approuve la vérification."""
        if self.status != 'IN_REVIEW':
            raise ValueError("Seules les vérifications en cours de révision peuvent être approuvées")
        
        self.status = 'VERIFIED'
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        if notes:
            self.notes_admin = notes
        
        # Marquer l'entreprise comme vérifiée
        self.entreprise.est_verifiee = True
        self.entreprise.date_verification = timezone.now()
        self.entreprise.save(update_fields=['est_verifiee', 'date_verification'])
        
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'notes_admin'])
    
    def reject(self, admin_user, reason, notes=None):
        """Rejette la vérification."""
        if self.status != 'IN_REVIEW':
            raise ValueError("Seules les vérifications en cours de révision peuvent être rejetées")
        
        self.status = 'REJECTED'
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        if notes:
            self.notes_admin = notes
        
        self.save(update_fields=[
            'status', 'reviewed_by', 'reviewed_at', 
            'rejection_reason', 'notes_admin'
        ])
    
    def reset_for_retry(self):
        """Remet la vérification en état pour une nouvelle tentative."""
        if not self.can_retry:
            raise ValueError("Aucune nouvelle tentative n'est possible")
        
        self.status = 'PENDING'
        self.rejection_reason = ''
        self.reviewed_by = None
        self.reviewed_at = None
        self.submitted_at = None
        # Étendre la deadline de 15 jours
        self.deadline = timezone.now() + timezone.timedelta(days=15)
        
        self.save(update_fields=[
            'status', 'rejection_reason', 'reviewed_by', 
            'reviewed_at', 'submitted_at', 'deadline'
        ])


def verification_upload_path(instance, filename):
    """Génère le chemin d'upload pour les documents de vérification."""
    # Organiser par entreprise et type de document
    entreprise_id = instance.verification.entreprise.user.id
    doc_type = instance.document_type
    
    # Garder l'extension originale
    name, ext = os.path.splitext(filename)
    
    return f'verifications/{entreprise_id}/{doc_type}/{timezone.now().strftime("%Y%m%d_%H%M%S")}{ext}'


class DocumentUpload(BaseModel, MetadataMixin):
    """
    Document uploadé pour la vérification d'une entreprise.
    """
    DOCUMENT_TYPES = [
        ('kbis', 'Extrait Kbis'),
        ('statuts', 'Statuts de la société'),
        ('id_dirigeant', 'Pièce d\'identité du dirigeant'),
        ('justificatif_domicile', 'Justificatif de domicile'),
        ('rib', 'RIB de l\'entreprise'),
        ('attestation_assurance', 'Attestation d\'assurance'),
        ('autre', 'Autre document'),
    ]
    
    STATUS_CHOICES = [
        ('UPLOADED', 'Uploadé'),
        ('VALID', 'Valide'),
        ('INVALID', 'Invalide'),
        ('EXPIRED', 'Expiré'),
    ]
    
    # Lien vers la vérification
    verification = models.ForeignKey(
        DocumentVerification,
        on_delete=models.CASCADE,
        related_name='uploads',
        verbose_name="Vérification"
    )
    
    # Type de document
    document_type = models.CharField(
        max_length=50,
        choices=DOCUMENT_TYPES,
        verbose_name="Type de document"
    )
    
    # Fichier uploadé
    file = models.FileField(
        upload_to=verification_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
            )
        ],
        verbose_name="Fichier"
    )
    
    # Nom original du fichier
    original_filename = models.CharField(
        max_length=255,
        verbose_name="Nom original du fichier"
    )
    
    # Taille du fichier en bytes
    file_size = models.PositiveIntegerField(
        verbose_name="Taille du fichier (bytes)"
    )
    
    # Type MIME
    mime_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Type MIME"
    )
    
    # Statut de validation
    is_valid = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Document valide",
        help_text="Null = pas encore vérifié, True = valide, False = invalide"
    )
    
    # Notes de validation
    validation_notes = models.TextField(
        blank=True,
        verbose_name="Notes de validation"
    )
    
    # Qui a validé le document
    validated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validated_documents',
        verbose_name="Validé par"
    )
    
    validated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Validé le"
    )
    
    # Date d'expiration du document (si applicable)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Expire le"
    )
    
    class Meta:
        verbose_name = "Document uploadé"
        verbose_name_plural = "Documents uploadés"
        db_table = 'foundation_document_upload'
        unique_together = ['verification', 'document_type']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.verification.entreprise.nom_entreprise}"
    
    def save(self, *args, **kwargs):
        """Override save pour extraire les métadonnées du fichier."""
        if self.file and not self.file_size:
            self.file_size = self.file.size
        
        if self.file and not self.original_filename:
            self.original_filename = self.file.name
        
        super().save(*args, **kwargs)
        
        # Mettre à jour la liste des documents uploadés dans la vérification
        self.update_verification_documents()
    
    def update_verification_documents(self):
        """Met à jour la liste des documents dans la vérification."""
        self.verification.documents_uploaded[self.document_type] = self.file.url
        self.verification.save(update_fields=['documents_uploaded'])
    
    @property
    def is_expired(self):
        """Vérifie si le document a expiré."""
        return self.expires_at and timezone.now() > self.expires_at
    
    @property
    def file_extension(self):
        """Retourne l'extension du fichier."""
        return os.path.splitext(self.original_filename)[1].lower()
    
    @property
    def is_image(self):
        """Vérifie si le fichier est une image."""
        return self.file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    
    @property
    def is_pdf(self):
        """Vérifie si le fichier est un PDF."""
        return self.file_extension == '.pdf'
    
    @property
    def human_readable_size(self):
        """Retourne la taille du fichier dans un format lisible."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def validate_document(self, admin_user, is_valid, notes=None):
        """Valide ou invalide le document."""
        self.is_valid = is_valid
        self.validation_notes = notes or ''
        self.validated_by = admin_user
        self.validated_at = timezone.now()
        
        self.save(update_fields=[
            'is_valid', 'validation_notes', 'validated_by', 'validated_at'
        ])
        
        # Si le document est invalide, marquer la vérification comme incomplète
        if not is_valid and self.verification.status == 'IN_REVIEW':
            self.verification.status = 'INCOMPLETE'
            self.verification.save(update_fields=['status'])
    
    def delete(self, *args, **kwargs):
        """Override delete pour nettoyer les références."""
        # Supprimer le fichier physique
        if self.file:
            try:
                self.file.delete(save=False)
            except:
                pass
        
        # Supprimer la référence dans la vérification
        if self.document_type in self.verification.documents_uploaded:
            del self.verification.documents_uploaded[self.document_type]
            self.verification.save(update_fields=['documents_uploaded'])
        
        super().delete(*args, **kwargs)
