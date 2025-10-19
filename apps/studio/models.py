from django.db import models

from django.contrib.postgres.fields import JSONField
from django.contrib.auth import get_user_model
from apps.foundation.models import Organization
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class Project(models.Model):

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
        if self.is_home:
            Page.objects.filter(project=self.project, is_home=True).exclude(pk=self.pk).update(is_home=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.route})"


class Component(models.Model):
    """
    Catalogue de composants disponibles pour la construction d'interfaces.
    Définit les métadonnées des composants utilisables dans les pages.
    """

    COMPONENT_CATEGORIES = [
        ('layout', 'Layout'),
        ('forms', 'Formulaires'),
        ('content', 'Contenu'),
        ('navigation', 'Navigation'),
        ('data', 'Données'),
        ('media', 'Médias'),
        ('feedback', 'Feedback'),
        ('overlay', 'Overlay'),
    ]

    name = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=COMPONENT_CATEGORIES, default='content')
    icon = models.CharField(max_length=100, blank=True, help_text="Nom de l'icône (ex: 'button', 'input')")

    # Configuration des propriétés du composant
    properties = JSONField(default=dict, help_text="""
        Définition des propriétés configurables du composant.
        Format: {
            'prop_name': {
                'type': 'string|number|boolean|select|color|action',
                'label': 'Label affiché',
                'default': 'valeur par défaut',
                'required': true/false,
                'options': ['option1', 'option2'] // pour type select
            }
        }
    """)

    # Règles de validation
    validation_rules = JSONField(default=dict, help_text="""
        Règles de validation pour les propriétés.
        Format: {
            'prop_name': {
                'min_length': 1,
                'max_length': 100,
                'pattern': 'regex',
                'custom_validation': 'function_name'
            }
        }
    """)

    # Configuration par défaut du composant
    default_config = JSONField(default=dict, help_text="""
        Configuration par défaut quand le composant est ajouté à une page.
    """)

    # Métadonnées techniques
    is_active = models.BooleanField(default=True)
    version = models.CharField(max_length=20, default='1.0.0')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Composant'
        verbose_name_plural = 'Composants'

    def __str__(self):
        return f"{self.display_name} ({self.category})"
