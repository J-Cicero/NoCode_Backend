"""
Model Builder Service
Convertit les DataSchema et FieldSchema en modèles Django fonctionnels.
Utilise du SQL brut pour créer les tables directement (approche NoCode).
"""

import os
from django.conf import settings
from django.db import connection
from django.template import Template, Context
import logging

logger = logging.getLogger(__name__)


class ModelBuilder:
    """
    Service qui génère des modèles Django à partir des DataSchema utilisateur.
    Utilise du SQL brut pour éviter les problèmes de migrations dynamiques.
    """
    
    def __init__(self, project):
        self.project = project
        self.app_name = f"project_{project.id}"
        self.app_path = os.path.join(settings.BASE_DIR, 'generated_apps', self.app_name)
        self.table_prefix = self.app_name  # Préfixe pour les tables PostgreSQL
    
    def generate_model_from_schema(self, data_schema):
        """
        Génère un modèle Django complet et crée la table PostgreSQL directement.
        
        Args:
            data_schema: Instance de DataSchema
            
        Returns:
            str: Chemin du fichier models.py généré
        """
        try:
            # Créer le dossier de l'application si nécessaire
            self._ensure_app_structure()
            
            # Générer le code du modèle
            model_code = self._generate_model_code(data_schema)
            
            # Écrire le fichier models.py
            models_file = os.path.join(self.app_path, 'models.py')
            with open(models_file, 'w', encoding='utf-8') as f:
                f.write(model_code)
            
            logger.info(f"Modèle généré pour {data_schema.display_name}: {models_file}")
            
            # Créer la table PostgreSQL directement avec SQL
            self._create_table_with_sql(data_schema)
            
            return models_file
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du modèle pour {data_schema.display_name}: {e}")
            raise
    
    def _ensure_app_structure(self):
        """
        S'assure que la structure de l'application Django existe.
        """
        if not os.path.exists(self.app_path):
            os.makedirs(self.app_path, exist_ok=True)
            
            # Créer __init__.py
            init_file = os.path.join(self.app_path, '__init__.py')
            with open(init_file, 'w') as f:
                f.write('')
            
            # Créer apps.py
            apps_file = os.path.join(self.app_path, 'apps.py')
            apps_config = f'''from django.apps import AppConfig

class {self.app_name.title()}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'generated_apps.{self.app_name}'
'''
            with open(apps_file, 'w') as f:
                f.write(apps_config)
    
    def _generate_model_code(self, data_schema):
        """
        Génère le code Python pour un modèle Django.
        
        Args:
            data_schema: Instance de DataSchema
            
        Returns:
            str: Code Python du modèle
        """
        # Récupérer les champs (structurés ou JSON)
        fields = data_schema.structured_fields
        
        # Importations nécessaires
        imports = ['from django.db import models']
        
        # Vérifier s'il y a des relations vers d'autres schémas
        has_relations = any(
            field.get('field_type') in ['RELATION_ONE_TO_ONE', 'RELATION_ONE_TO_MANY', 'RELATION_MANY_TO_MANY']
            for field in fields
        )
        
        if has_relations:
            imports.append('from django.contrib.auth import get_user_model')
            imports.append('User = get_user_model()')
        
        # Générer les champs
        model_fields = []
        
        for field in fields:
            if isinstance(field, dict):  # Champ depuis JSON
                field_code = self._generate_field_from_dict(field)
            else:  # Champ depuis FieldSchema
                field_code = field.get_django_field()
            
            model_fields.append(f"    {field['name']} = {field_code}")
        
        # Joindre les champs
        fields_code = '\n'.join(model_fields)
        
        # Template du modèle
        model_template = f'''{chr(10).join(imports)}

class {data_schema.table_name.title()}(models.Model):
    """
    Table générée automatiquement par NoCode
    Projet: {self.project.name}
    Créée le: {data_schema.created_at.strftime('%Y-%m-%d %H:%M:%S')}
    """
    
{fields_code}
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = '{self.table_prefix}_{data_schema.table_name}'
        verbose_name = '{data_schema.display_name}'
        verbose_name_plural = '{data_schema.display_name}s'
        ordering = ['-created_at']
    
    def __str__(self):
        return str(self.{fields[0]['name'] if fields else 'id'})
'''
        
        return model_template
    
    def _generate_field_from_dict(self, field_dict):
       
        field_type = field_dict.get('field_type', 'TEXT_SHORT')
        
        django_mapping = {
            'TEXT_SHORT': 'models.CharField(max_length=255',
            'TEXT_LONG': 'models.TextField(',
            'NUMBER_INT': 'models.IntegerField(',
            'NUMBER_DECIMAL': 'models.DecimalField(max_digits=10, decimal_places=2',
            'DATE': 'models.DateField(',
            'DATETIME': 'models.DateTimeField(',
            'TIME': 'models.TimeField(',
            'BOOLEAN': 'models.BooleanField(default=False',
            'EMAIL': 'models.EmailField(',
            'URL': 'models.URLField(',
            'PHONE': 'models.CharField(max_length=20',
            'COLOR': 'models.CharField(max_length=7',
            'FILE': 'models.FileField(upload_to="user_files/"',
            'IMAGE': 'models.ImageField(upload_to="user_images/"',
        }
        
        base_field = django_mapping.get(field_type, 'models.CharField(max_length=255')
        constraints = []
        
        if field_dict.get('is_required', False):
            constraints.append('null=False')
        else:
            constraints.append('null=True, blank=True')
        
        if field_dict.get('is_unique', False):
            constraints.append('unique=True')
        
        if field_dict.get('default_value') is not None:
            constraints.append(f"default={repr(field_dict['default_value'])}")
        
        constraint_str = ', '.join(constraints)
        
        return f"{base_field}, {constraint_str})"
    
    def _create_table_with_sql(self, data_schema):
        """
        Crée la table PostgreSQL directement avec du SQL.
        Approche NoCode : pas de migrations, création directe.
        """
        try:
            table_name = f"{self.table_prefix}_{data_schema.table_name}"
            
            # Récupérer les champs
            fields = data_schema.structured_fields
            
            # Générer le SQL CREATE TABLE
            sql_columns = []
            
            for field in fields:
                if isinstance(field, dict):
                    column_sql = self._get_sql_column_from_dict(field)
                else:
                    column_sql = self._get_sql_column_from_field_schema(field)
                
                sql_columns.append(column_sql)
            
            # Ajouter les colonnes de timestamp
            sql_columns.extend([
                "created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()",
                "updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()"
            ])
            
            # Créer la table SQL
            create_table_sql = f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id SERIAL PRIMARY KEY,
                    {', '.join(sql_columns)}
                );
                
                CREATE INDEX IF NOT EXISTS idx_{table_name}_created_at ON {table_name} (created_at);
            '''
            
            # Exécuter le SQL
            with connection.cursor() as cursor:
                cursor.execute(create_table_sql)
            
            logger.info(f"✅ Table PostgreSQL créée: {table_name}")
            print(f"✅ Table PostgreSQL créée: {table_name}")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création de la table SQL: {e}")
            print(f"❌ Erreur lors de la création de la table SQL: {e}")
            raise
    
    def _get_sql_column_from_dict(self, field_dict):
        """Génère une colonne SQL depuis un dictionnaire JSON"""
        field_name = field_dict['name']
        field_type = field_dict.get('field_type', 'TEXT_SHORT')
        
        # Mapping vers types PostgreSQL
        sql_mapping = {
            'TEXT_SHORT': 'VARCHAR(255)',
            'TEXT_LONG': 'TEXT',
            'NUMBER_INT': 'INTEGER',
            'NUMBER_DECIMAL': 'DECIMAL(10,2)',
            'DATE': 'DATE',
            'DATETIME': 'TIMESTAMP WITH TIME ZONE',
            'TIME': 'TIME',
            'BOOLEAN': 'BOOLEAN',
            'EMAIL': 'VARCHAR(255)',
            'URL': 'VARCHAR(500)',
            'PHONE': 'VARCHAR(20)',
            'COLOR': 'VARCHAR(7)',
            'FILE': 'VARCHAR(255)',
            'IMAGE': 'VARCHAR(255)',
        }
        
        sql_type = sql_mapping.get(field_type, 'VARCHAR(255)')
        
        # Contraintes
        constraints = []
        if not field_dict.get('is_required', False):
            constraints.append('NULL')
        else:
            constraints.append('NOT NULL')
        
        if field_dict.get('is_unique', False):
            constraints.append('UNIQUE')
        
        return f"{field_name} {sql_type} {' '.join(constraints)}"
    
    def _get_sql_column_from_field_schema(self, field_schema):
        """Génère une colonne SQL depuis un FieldSchema"""
        field_name = field_schema.name
        field_type = field_schema.field_type
        
        # Mapping vers types PostgreSQL
        sql_mapping = {
            'TEXT_SHORT': 'VARCHAR(255)',
            'TEXT_LONG': 'TEXT',
            'NUMBER_INT': 'INTEGER',
            'NUMBER_DECIMAL': 'DECIMAL(10,2)',
            'DATE': 'DATE',
            'DATETIME': 'TIMESTAMP WITH TIME ZONE',
            'TIME': 'TIME',
            'BOOLEAN': 'BOOLEAN',
            'EMAIL': 'VARCHAR(255)',
            'URL': 'VARCHAR(500)',
            'PHONE': 'VARCHAR(20)',
            'COLOR': 'VARCHAR(7)',
            'FILE': 'VARCHAR(255)',
            'IMAGE': 'VARCHAR(255)',
        }
        
        sql_type = sql_mapping.get(field_type, 'VARCHAR(255)')
        
        # Contraintes
        constraints = []
        if not field_schema.is_required:
            constraints.append('NULL')
        else:
            constraints.append('NOT NULL')
        
        if field_schema.is_unique:
            constraints.append('UNIQUE')
        
        return f"{field_name} {sql_type} {' '.join(constraints)}"
    
    def add_field_to_existing_model(self, data_schema, field_schema):
        """
        Ajoute un champ à une table existante avec ALTER TABLE.
        
        Args:
            data_schema: Instance de DataSchema
            field_schema: Instance de FieldSchema à ajouter
        """
        try:
            table_name = f"{self.table_prefix}_{data_schema.table_name}"
            column_sql = self._get_sql_column_from_field_schema(field_schema)
            
            # ALTER TABLE pour ajouter la colonne
            alter_table_sql = f'''
                ALTER TABLE {table_name} 
                ADD COLUMN IF NOT EXISTS {column_sql};
            '''
            
            with connection.cursor() as cursor:
                cursor.execute(alter_table_sql)
            
            logger.info(f"✅ Champ '{field_schema.name}' ajouté à la table {table_name}")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'ajout du champ '{field_schema.name}': {e}")
            raise
    
    def generate_all_models(self):
        """
        Génère tous les modèles pour un projet.
        
        Returns:
            list: Liste des chemins des fichiers générés
        """
        generated_files = []
        
        for data_schema in self.project.schemas.all():
            try:
                model_file = self.generate_model_from_schema(data_schema)
                generated_files.append(model_file)
            except Exception as e:
                logger.error(f"Erreur lors de la génération du modèle {data_schema.table_name}: {e}")
        
        return generated_files
