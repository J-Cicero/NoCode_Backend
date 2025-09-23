"""
Mixins réutilisables pour fonctionnalités transversales.
Ces mixins peuvent être utilisés par tous les modèles de la plateforme.
"""
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class TimestampMixin(models.Model):
    """
    Mixin pour ajouter des timestamps automatiques.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """
    Mixin pour ajouter la fonctionnalité de suppression logique.
    """
    is_deleted = models.BooleanField(default=False, verbose_name="Supprimé")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Supprimé le")

    class Meta:
        abstract = True

    def soft_delete(self):
        """Suppression logique de l'objet."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        """Restauration d'un objet supprimé logiquement."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])

    @property
    def is_active(self):
        """Retourne True si l'objet n'est pas supprimé."""
        return not self.is_deleted


class StatusMixin(models.Model):
    """
    Mixin pour ajouter un système de statut avec historique.
    """
    STATUS_CHOICES = [
        ('ACTIVE', 'Actif'),
        ('INACTIVE', 'Inactif'),
        ('PENDING', 'En attente'),
        ('SUSPENDED', 'Suspendu'),
        ('ARCHIVED', 'Archivé'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        verbose_name="Statut"
    )
    status_changed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Statut modifié le"
    )
    status_changed_by = models.ForeignKey(
        'foundation.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_status_changes',
        verbose_name="Statut modifié par"
    )

    class Meta:
        abstract = True

    def change_status(self, new_status, changed_by=None):
        """Change le statut et enregistre l'historique."""
        if self.status != new_status:
            self.status = new_status
            self.status_changed_at = timezone.now()
            self.status_changed_by = changed_by
            self.save(update_fields=['status', 'status_changed_at', 'status_changed_by'])

    @property
    def is_active(self):
        """Retourne True si le statut est actif."""
        return self.status == 'ACTIVE'


class AuditMixin(models.Model):
    """
    Mixin pour ajouter des informations d'audit (qui a créé/modifié).
    """
    created_by = models.ForeignKey(
        'foundation.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name="Créé par"
    )
    updated_by = models.ForeignKey(
        'foundation.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        verbose_name="Modifié par"
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Override save pour automatiquement définir updated_by."""
        # Note: Dans un vrai projet, on récupérerait l'utilisateur du contexte/request
        super().save(*args, **kwargs)


class PermissionMixin(models.Model):
    """
    Mixin pour ajouter des permissions personnalisées sous forme JSON.
    """
    permissions = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Permissions personnalisées",
        help_text="Permissions spécifiques à cet objet au format JSON"
    )

    class Meta:
        abstract = True

    def has_permission(self, permission_key):
        """Vérifie si une permission spécifique est accordée."""
        return self.permissions.get(permission_key, False)

    def grant_permission(self, permission_key, value=True):
        """Accorde une permission spécifique."""
        self.permissions[permission_key] = value
        self.save(update_fields=['permissions'])

    def revoke_permission(self, permission_key):
        """Révoque une permission spécifique."""
        if permission_key in self.permissions:
            del self.permissions[permission_key]
            self.save(update_fields=['permissions'])


class MetadataMixin(models.Model):
    """
    Mixin pour ajouter des métadonnées flexibles sous forme JSON.
    """
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées",
        help_text="Données supplémentaires au format JSON"
    )

    class Meta:
        abstract = True

    def get_metadata(self, key, default=None):
        """Récupère une valeur des métadonnées."""
        return self.metadata.get(key, default)

    def set_metadata(self, key, value):
        """Définit une valeur dans les métadonnées."""
        self.metadata[key] = value
        self.save(update_fields=['metadata'])

    def update_metadata(self, data):
        """Met à jour plusieurs valeurs dans les métadonnées."""
        self.metadata.update(data)
        self.save(update_fields=['metadata'])


class SlugMixin(models.Model):
    """
    Mixin pour ajouter un slug automatique basé sur un champ name.
    """
    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name="Slug",
        help_text="Identifiant unique pour les URLs"
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Override save pour générer automatiquement le slug."""
        if not self.slug and hasattr(self, 'name'):
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            
            # Assurer l'unicité du slug
            while self.__class__.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        super().save(*args, **kwargs)


class OrderingMixin(models.Model):
    """
    Mixin pour ajouter un système d'ordre/tri.
    """
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre",
        help_text="Ordre d'affichage (plus petit = premier)"
    )

    class Meta:
        abstract = True
        ordering = ['order', 'id']

    def move_up(self):
        """Déplace l'élément vers le haut dans l'ordre."""
        previous = self.__class__.objects.filter(
            order__lt=self.order
        ).order_by('-order').first()
        
        if previous:
            self.order, previous.order = previous.order, self.order
            self.save(update_fields=['order'])
            previous.save(update_fields=['order'])

    def move_down(self):
        """Déplace l'élément vers le bas dans l'ordre."""
        next_item = self.__class__.objects.filter(
            order__gt=self.order
        ).order_by('order').first()
        
        if next_item:
            self.order, next_item.order = next_item.order, self.order
            self.save(update_fields=['order'])
            next_item.save(update_fields=['order'])


class ActivityLogMixin(models.Model):
    """
    Mixin pour enregistrer automatiquement les activités sur un modèle.
    """
    class Meta:
        abstract = True

    def log_activity(self, action, user=None, details=None):
        """Enregistre une activité sur cet objet."""
        from .activity import ActivityLog
        
        ActivityLog.objects.create(
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.pk,
            action=action,
            user=user,
            details=details or {}
        )

    def save(self, *args, **kwargs):
        """Override save pour enregistrer l'activité."""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Enregistrer l'activité
        action = 'created' if is_new else 'updated'
        self.log_activity(action)

    def delete(self, *args, **kwargs):
        """Override delete pour enregistrer l'activité."""
        self.log_activity('deleted')
        super().delete(*args, **kwargs)
