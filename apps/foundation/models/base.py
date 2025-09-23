"""
Modèles abstraits et classes de base pour le module Foundation.
Ces classes servent de fondation pour tous les autres modèles de la plateforme.
"""
from django.db import models
from django.utils import timezone
import uuid


class BaseModel(models.Model):
    """
    Modèle abstrait de base avec timestamps et soft delete.
    Tous les modèles de la plateforme héritent de cette classe.
    """
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    is_deleted = models.BooleanField(default=False, verbose_name="Supprimé")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Supprimé le")

    class Meta:
        abstract = True
        ordering = ['-created_at']

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

    def __str__(self):
        return f"{self.__class__.__name__} #{self.id}"


class TimestampedModel(models.Model):
    """
    Modèle abstrait avec uniquement les timestamps.
    Utilisé pour les modèles qui n'ont pas besoin du soft delete.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        abstract = True
        ordering = ['-created_at']


class SoftDeleteModel(models.Model):
    """
    Modèle abstrait avec uniquement le soft delete.
    Utilisé pour les modèles qui n'ont pas besoin des timestamps automatiques.
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


class UUIDModel(models.Model):
    """
    Modèle abstrait avec UUID comme clé primaire.
    Utilisé pour les modèles nécessitant des identifiants non séquentiels.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class ActiveManager(models.Manager):
    """
    Manager personnalisé qui exclut automatiquement les objets supprimés logiquement.
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    """
    Manager qui inclut tous les objets, même ceux supprimés logiquement.
    """
    def get_queryset(self):
        return super().get_queryset()


class SoftDeleteQuerySet(models.QuerySet):
    """
    QuerySet personnalisé avec méthodes pour la gestion du soft delete.
    """
    def active(self):
        """Retourne uniquement les objets non supprimés."""
        return self.filter(is_deleted=False)

    def deleted(self):
        """Retourne uniquement les objets supprimés."""
        return self.filter(is_deleted=True)

    def soft_delete(self):
        """Suppression logique en masse."""
        return self.update(is_deleted=True, deleted_at=timezone.now())

    def restore(self):
        """Restauration en masse."""
        return self.update(is_deleted=False, deleted_at=None)
