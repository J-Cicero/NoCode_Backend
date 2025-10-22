"""
Générateur de code pour les applications créées avec le Studio.

Ce module gère la génération du code source des applications à partir des modèles
définis dans le Studio.
"""
import os
import logging
from django.conf import settings
from django.core.management import call_command
from django.db import connection

logger = logging.getLogger(__name__)

class ModelGenerator:
    """Générateur de modèles Django à partir des schémas de données."""
    
    def __init__(self, project):
        self.project = project
        self.app_name = f"app_{project.id}"
        
    def generate_models(self):
        """Génère le code des modèles à partir des schémas de données."""
        models_code = []
        
        # En-tête du fichier models.py
        models_code.append('"""\nModèles générés automatiquement pour l\'application {}\n"""'.format(self.app_name))
        models_code.append('from django.db import models\n')
        models_code.append('class BaseModel(models.Model):\n    """Modèle de base avec des champs communs."""\n    created_at = models.DateTimeField(auto_now_add=True)\n    updated_at = models.DateTimeField(auto_now=True)\n    is_active = models.BooleanField(default=True)\n    \n    class Meta:\n        abstract = True\n\n')
        
        # Génération des modèles pour chaque schéma
        for schema in self.project.schemas.all():
            model_code = self._generate_model_code(schema)
            models_code.append(model_code)
        
        return '\n\n'.join(models_code)
    
    def _generate_model_code(self, schema):
        """Génère le code pour un modèle spécifique."""
        fields = []
        
        # Ajout des champs du schéma
        for field_name, field_config in schema.fields_config.items():
            field_type = field_config.get('type', 'CharField')
            field_params = field_config.get('params', {})
            
            # Mapping des types de champs
            field_mapping = {
                'string': 'CharField',
                'text': 'TextField',
                'number': 'IntegerField',
                'float': 'FloatField',
                'boolean': 'BooleanField',
                'date': 'DateField',
                'datetime': 'DateTimeField',
                'email': 'EmailField',
                'url': 'URLField',
                'foreign_key': 'ForeignKey',
                'many_to_many': 'ManyToManyField',
                'one_to_one': 'OneToOneField',
            }
            
            field_class = field_mapping.get(field_type, 'CharField')
            
            # Construction des paramètres du champ
            params = []
            
            # Paramètres communs
            if 'verbose_name' in field_params:
                params.append(f"verbose_name='{field_params['verbose_name']}'")
            
            if field_class in ['CharField', 'TextField', 'EmailField', 'URLField']:
                if 'max_length' in field_params:
                    params.append(f"max_length={field_params['max_length']}")
                else:
                    params.append("max_length=255")
                
                if field_class == 'CharField' and 'choices' in field_params:
                    choices = ', '.join([f"('{c[0]}', '{c[1]}')" for c in field_params['choices']])
                    params.append(f"choices=[{choices}]")
            
            # Gestion des clés étrangères
            if field_class in ['ForeignKey', 'ManyToManyField', 'OneToOneField']:
                related_model = field_params.get('related_model')
                if related_model:
                    params.append(f"'{related_model}'")
                    params.append("on_delete=models.CASCADE")
            
            # Paramètres par défaut
            if 'default' in field_params:
                default = field_params['default']
                if isinstance(default, str):
                    params.append(f"default='{default}'")
                else:
                    params.append(f"default={default}")
            
            # Ajout du champ au modèle
            field_str = f"    {field_name} = models.{field_class}("
            field_str += ", ".join(params)
            field_str += ")"
            fields.append(field_str)
        
        # Construction du code du modèle
        model_code = [
            f"class {schema.table_name.capitalize()}(BaseModel):",
            f'    """{schema.display_name}"""',
        ]
        
        if not fields:
            model_code.append("    pass")
        else:
            model_code.extend(fields)
        
        # Ajout de la méthode __str__
        display_field = next((f for f in schema.fields_config if f == 'name' or f == 'title'), 
                           next(iter(schema.fields_config.keys()), 'id'))
        model_code.extend([
            "",
            "    def __str__(self):",
            f"        return str(self.{display_field} if hasattr(self, '{display_field}') else self.id)",
        ])
        
        # Ajout de la classe Meta
        model_code.extend([
            "",
            "    class Meta:",
            f"        verbose_name = '{schema.display_name}'",
            f"        verbose_name_plural = '{schema.display_name}s'",
        ])
        
        return '\n'.join(model_code)


class APIGenerator:
    """Générateur d'API REST pour les modèles."""
    
    def __init__(self, project):
        self.project = project
        self.app_name = f"app_{project.id}"
    
    def generate_serializers(self):
        """Génère les sérialiseurs pour les modèles."""
        serializers = []
        
        # En-tête du fichier serializers.py
        serializers.append('"""\nSérialiseurs générés automatiquement pour l\'application {}\n"""'.format(self.app_name))
        serializers.append('from rest_framework import serializers')
        serializers.append(f'from . import models\n')
        
        # Génération des sérialiseurs pour chaque modèle
        for schema in self.project.schemas.all():
            serializer = self._generate_serializer(schema)
            serializers.append(serializer)
        
        return '\n\n'.join(serializers)
    
    def _generate_serializer(self, schema):
        """Génère un sérialiseur pour un modèle spécifique."""
        model_name = schema.table_name.capitalize()
        fields = [f"'{f}'" for f in schema.fields_config.keys()]
        fields.extend(["'id', 'created_at', 'updated_at"])
        
        return f'''class {model_name}Serializer(serializers.ModelSerializer):
    """Sérialiseur pour le modèle {model_name}"""
    
    class Meta:
        model = models.{model_name}
        fields = [{', '.join(fields)}]
'''


class ViewGenerator:
    """Générateur de vues et d'URLs pour l'API."""
    
    def __init__(self, project):
        self.project = project
        self.app_name = f"app_{project.id}"
    
    def generate_views(self):
        """Génère les vues pour l'API."""
        views = []
        
        # En-tête du fichier views.py
        views.append('"""\nVues générées automatiquement pour l\'application {}\n"""'.format(self.app_name))
        views.append('from rest_framework import viewsets, permissions')
        views.append('from rest_framework.decorators import action')
        views.append('from rest_framework.response import Response')
        views.append('from . import models, serializers\n')
        
        # Génération des vues pour chaque modèle
        for schema in self.project.schemas.all():
            view = self._generate_view(schema)
            views.append(view)
        
        return '\n\n'.join(views)
    
    def _generate_view(self, schema):
        """Génère une vue pour un modèle spécifique."""
        model_name = schema.table_name.capitalize()
        
        return f'''class {model_name}ViewSet(viewsets.ModelViewSet):
    """
    API endpoint qui permet de gérer les {schema.display_name.lower()}.
    """
    queryset = models.{model_name}.objects.all()
    serializer_class = serializers.{model_name}Serializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtre les résultats en fonction des permissions."""
        queryset = super().get_queryset()
        # Ajouter des filtres personnalisés ici si nécessaire
        return queryset
'''

    def generate_urls(self):
        """Génère le fichier urls.py pour l'API."""
        urlpatterns = []
        
        # En-tête du fichier urls.py
        urls = [
            '"""\nURLs générées automatiquement pour l\'application {}\n"""'.format(self.app_name),
            'from django.urls import path, include',
            'from rest_framework.routers import DefaultRouter',
            'from . import views',
            '',
            'router = DefaultRouter()',
        ]
        
        # Ajout des URLs pour chaque vue
        for schema in self.project.schemas.all():
            model_name = schema.table_name.lower()
            view_name = f"{schema.table_name.capitalize()}ViewSet"
            urls.append(f"router.register(r'{model_name}', views.{view_name}, basename='{model_name}')")
        
        urls.extend([
            '',
            'urlpatterns = [',
            "    path('', include(router.urls)),",
            ']',
        ])
        
        return '\n'.join(urls)


class AppGenerator:
    """Générateur d'application complète."""
    
    def __init__(self, project):
        self.project = project
        self.app_name = f"app_{project.id}"
        self.app_dir = os.path.join(settings.BASE_DIR, 'generated_apps', self.app_name)
        
    def generate(self):
        """Génère l'application complète."""
        try:
            # Création du répertoire de l'application
            os.makedirs(self.app_dir, exist_ok=True)
            
            # Génération des modèles
            self._generate_file('models.py', ModelGenerator(self.project).generate_models())
            
            # Génération des sérialiseurs
            self._generate_file('serializers.py', APIGenerator(self.project).generate_serializers())
            
            # Génération des vues
            view_generator = ViewGenerator(self.project)
            self._generate_file('views.py', view_generator.generate_views())
            
            # Génération des URLs
            self._generate_file('urls.py', view_generator.generate_urls())
            
            # Génération du fichier apps.py
            self._generate_file('apps.py', self._generate_apps_config())
            
            # Génération du fichier __init__.py
            self._generate_file('__init__.py', '')
            
            # Génération du fichier admin.py
            self._generate_file('admin.py', self._generate_admin_config())
            
            # Création des migrations
            self._create_migrations()
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de l'application: {str(e)}")
            raise
    
    def _generate_file(self, filename, content):
        """Génère un fichier dans le répertoire de l'application."""
        filepath = os.path.join(self.app_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_apps_config(self):
        """Génère le fichier apps.py pour l'application."""
        app_config = f"""
from django.apps import AppConfig


class {self.app_name.capitalize()}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'generated_apps.{self.app_name}'
    verbose_name = '{self.project.name}'
"""
        return app_config
    
    def _generate_admin_config(self):
        """Génère le fichier admin.py pour l'application."""
        admin_imports = []
        admin_registrations = []
        
        for schema in self.project.schemas.all():
            model_name = schema.table_name.capitalize()
            admin_imports.append(f'from .models import {model_name}')
            admin_registrations.append(f'admin.site.register({model_name})')
        
        admin_code = [
            'from django.contrib import admin',
            'from . import models',
            "",
            "# Modèles générés automatiquement"
        ]
        
        admin_code.extend(admin_imports)
        admin_code.append('')
        admin_code.extend(admin_registrations)
        
        return '\n'.join(admin_code)
    
    def _create_migrations(self):
        """Crée et applique les migrations pour l'application générée."""
        # Ajout de l'application à INSTALLED_APPS si nécessaire
        app_config = f'generated_apps.{self.app_name}.apps.{self.app_name.capitalize()}Config'
        
        if app_config not in settings.INSTALLED_APPS:
            settings.INSTALLED_APPS += (app_config,)
        
        # Création des migrations
        with connection.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS %s", [self.app_name])
        
        # Création des migrations
        call_command('makemigrations', self.app_name, interactive=False)
        call_command('migrate', self.app_name, interactive=False)
