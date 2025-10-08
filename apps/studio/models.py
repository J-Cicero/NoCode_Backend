from django.db import models
from django.db import connection
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import transaction
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.foundation.models import Organization
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class Project(models.Model):
    """
    Modèle représentant un projet NoCode
    """
    name = models.CharField(max_length=255)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='projects')
    schema_name = models.CharField(max_length=63, unique=True)  # PostgreSQL a une limite de 63 caractères
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Projet'
        verbose_name_plural = 'Projets'

    def __str__(self):
        return f"{self.name} ({self.schema_name})"


class DataSchema(models.Model):
    """
    Modèle pour stocker la structure des tables de données
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='schemas')
    table_name = models.SlugField(max_length=63)  # Nom technique de la table
    display_name = models.CharField(max_length=255)  # Nom d'affichage
    fields_config = JSONField()  # Configuration des champs
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('project', 'table_name')
        ordering = ['created_at']
        verbose_name = 'Schéma de données'
        verbose_name_plural = 'Schémas de données'

    def __str__(self):
        return f"{self.display_name} ({self.table_name})"


class Page(models.Model):
    """
    Modèle pour les pages du builder
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='pages')
    name = models.CharField(max_length=255)
    route = models.CharField(max_length=255, help_text="Chemin de l'URL (ex: 'home', 'about')")
    config = JSONField(default=dict)  # Configuration de la page (composants, mise en page, etc.)
    is_home = models.BooleanField(default=False, help_text="Page d'accueil du projet")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('project', 'route')
        ordering = ['created_at']
        verbose_name = 'Page'
        verbose_name_plural = 'Pages'

    def save(self, *args, **kwargs):
        # S'assurer qu'une seule page est marquée comme page d'accueil par projet
        if self.is_home:
            Page.objects.filter(project=self.project, is_home=True).exclude(pk=self.pk).update(is_home=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.route})"
