"""
Modèles abstraits et classes de base pour le module Foundation.
Ces classes servent de fondation pour tous les autres modèles de la plateforme.
"""
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
import uuid


class BaseModel(models.Model):

    id = models.BigAutoField(primary_key=True)
    tracking_id = models.UUIDField(
        default=uuid.uuid4, 
        unique=True, 
        editable=False,
        verbose_name="ID de suivi",
        help_text="Identifiant public unique pour les requêtes API"
    )
    created_by = models.ForeignKey(
        'foundation.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name="Créé par"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.__class__.__name__} #{self.id}"


class TimestampedModel(models.Model):

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        abstract = True
        ordering = ['-created_at']




class UUIDModel(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


