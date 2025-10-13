"""
Modèles abstraits et classes de base pour le module Foundation.
Ces classes servent de fondation pour tous les autres modèles de la plateforme.
"""
from django.db import models
from django.utils import timezone
import uuid


class BaseModel(models.Model):

    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    is_deleted = models.BooleanField(default=False, verbose_name="Supprimé")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Supprimé le")

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def soft_delete(self):
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

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        abstract = True
        ordering = ['-created_at']


class SoftDeleteModel(models.Model):

    is_deleted = models.BooleanField(default=False, verbose_name="Supprimé")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Supprimé le")

    class Meta:
        abstract = True

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])


class UUIDModel(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class ActiveManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AllObjectsManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset()


class SoftDeleteQuerySet(models.QuerySet):

    def active(self):
        return self.filter(is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)

    def soft_delete(self):
        return self.update(is_deleted=True, deleted_at=timezone.now())

    def restore(self):
        return self.update(is_deleted=False, deleted_at=None)
