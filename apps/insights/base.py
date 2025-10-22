"""
Modèles de base pour le module Insights.
"""
from django.db import models
from django.utils import timezone

class BaseModel(models.Model):
    """
    Modèle de base pour tous les modèles du module Insights.

    Fournit les champs de suivi temporels standard.
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créé le"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Mis à jour le"
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Sauvegarde avec mise à jour automatique du timestamp."""
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
