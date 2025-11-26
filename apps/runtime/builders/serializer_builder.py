"""
Serializer Builder Service
Génère dynamiquement des DRF serializers depuis les DataSchema/FieldSchema.
Approche NoCode : pas de fichiers générés, création à la volée.
"""

from rest_framework import serializers
from django.db import models
from django.apps import apps
import logging

logger = logging.getLogger(__name__)


class SerializerBuilder:
    """
    Service qui génère des DRF serializers dynamiquement à partir des DataSchema.
    Utilisé pour les APIs CRUD automatiques.
    """
    
    def __init__(self, project):
        self.project = project
        self.app_name = f"project_{project.id}"
        self.table_prefix = self.app_name
    
    def create_serializer_class(self, data_schema):
        """
        Crée une classe serializer DRF dynamiquement depuis un DataSchema.
        
        Args:
            data_schema: Instance de DataSchema
            
        Returns:
            class: Classe serializer DRF prête à l'emploi
        """
        try:
            # Récupérer les champs du schéma
            fields = data_schema.structured_fields
            
            # Créer les champs du serializer
            serializer_fields = {}
            
            for field in fields:
                if isinstance(field, dict):
                    # Champ depuis JSON (fallback)
                    serializer_field = self._get_serializer_field_from_dict(field)
                    field_name = field['name']
                else:
                    # Champ depuis FieldSchema
                    serializer_field = self._get_serializer_field_from_schema(field)
                    field_name = field.name
                
                serializer_fields[field_name] = serializer_field
            
            # Ajouter les champs système
            serializer_fields.update({
                'id': serializers.UUIDField(read_only=True),
                'created_at': serializers.DateTimeField(read_only=True),
                'updated_at': serializers.DateTimeField(read_only=True),
            })
            
            # Créer la classe Meta (pas nécessaire pour Serializer de base)
            # Pour Serializer, on n'a pas besoin de Meta class
            
            # Créer la classe serializer
            serializer_class_name = f"{data_schema.table_name.title()}Serializer"
            serializer_class = type(serializer_class_name, (serializers.Serializer,), {
                **serializer_fields
            })
            
            logger.info(f"Serializer dynamique créé: {serializer_class_name}")
            return serializer_class
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du serializer pour {data_schema.table_name}: {e}")
            raise
    
    def _get_dynamic_model(self, data_schema):
        """
        Récupère ou crée le modèle Django dynamique pour un DataSchema.
        Pour l'instant, retourne None car nous utiliserons une approche différente.
        """
        # TODO: Implémenter la récupération des modèles dynamiques
        # Pour l'instant, nous utiliserons une approche basée sur les tables SQL directes
        return None
    
    def _get_serializer_field_from_schema(self, field_schema):
        """
        Génère un champ serializer DRF depuis un FieldSchema.
        
        Args:
            field_schema: Instance de FieldSchema
            
        Returns:
            Field: Champ serializer DRF
        """
        field_type = field_schema.field_type
        field_name = field_schema.name
        
        # Mapping des types FieldSchema vers DRF fields
        field_mapping = {
            'TEXT_SHORT': serializers.CharField(max_length=255),
            'TEXT_LONG': serializers.CharField(),
            'NUMBER_INT': serializers.IntegerField(),
            'NUMBER_DECIMAL': serializers.DecimalField(max_digits=10, decimal_places=2),
            'DATE': serializers.DateField(),
            'DATETIME': serializers.DateTimeField(),
            'TIME': serializers.TimeField(),
            'BOOLEAN': serializers.BooleanField(),
            'EMAIL': serializers.EmailField(),
            'URL': serializers.URLField(),
            'PHONE': serializers.CharField(max_length=20),
            'COLOR': serializers.CharField(max_length=7),
            'FILE': serializers.FileField(),
            'IMAGE': serializers.ImageField(),
            'CHOICE_SINGLE': serializers.ChoiceField(choices=[]),
            'CHOICE_MULTIPLE': serializers.ListField(child=serializers.CharField()),
        }
        
        # Champ de base
        base_field = field_mapping.get(field_type, serializers.CharField(max_length=255))
        
        # Appliquer les contraintes
        if field_schema.is_required:
            base_field.required = True
        else:
            base_field.required = False
            base_field.allow_null = True
        
        # Valeur par défaut
        if field_schema.default_value is not None:
            base_field.default = field_schema.default_value
        
        # Choices pour CHOICE_SINGLE
        if field_type == 'CHOICE_SINGLE' and field_schema.choices:
            choices = [(choice, choice) for choice in field_schema.choices]
            base_field = serializers.ChoiceField(choices=choices)
            base_field.required = field_schema.is_required
        
        return base_field
    
    def _get_serializer_field_from_dict(self, field_dict):
        """
        Génère un champ serializer DRF depuis un dictionnaire JSON.
        
        Args:
            field_dict: Dictionnaire contenant les infos du champ
            
        Returns:
            Field: Champ serializer DRF
        """
        field_type = field_dict.get('field_type', 'TEXT_SHORT')
        field_name = field_dict['name']
        
        # Mapping des types JSON vers DRF fields
        field_mapping = {
            'TEXT_SHORT': serializers.CharField(max_length=255),
            'TEXT_LONG': serializers.CharField(),
            'NUMBER_INT': serializers.IntegerField(),
            'NUMBER_DECIMAL': serializers.DecimalField(max_digits=10, decimal_places=2),
            'DATE': serializers.DateField(),
            'DATETIME': serializers.DateTimeField(),
            'TIME': serializers.TimeField(),
            'BOOLEAN': serializers.BooleanField(),
            'EMAIL': serializers.EmailField(),
            'URL': serializers.URLField(),
            'PHONE': serializers.CharField(max_length=20),
            'COLOR': serializers.CharField(max_length=7),
            'FILE': serializers.FileField(),
            'IMAGE': serializers.ImageField(),
            'CHOICE_SINGLE': serializers.ChoiceField(choices=[]),
            'CHOICE_MULTIPLE': serializers.ListField(child=serializers.CharField()),
        }
        
        # Champ de base
        base_field = field_mapping.get(field_type, serializers.CharField(max_length=255))
        
        # Appliquer les contraintes
        if field_dict.get('is_required', False):
            base_field.required = True
        else:
            base_field.required = False
            base_field.allow_null = True
        
        # Valeur par défaut
        if field_dict.get('default_value') is not None:
            base_field.default = field_dict['default_value']
        
        # Choices pour CHOICE_SINGLE
        if field_type == 'CHOICE_SINGLE' and field_dict.get('choices'):
            choices = [(choice, choice) for choice in field_dict['choices']]
            base_field = serializers.ChoiceField(choices=choices)
            base_field.required = field_dict.get('is_required', False)
        
        return base_field
    
    def create_metadata_serializer(self, data_schema):
        """
        Crée un serializer pour les métadonnées du schéma (utilisé par le frontend).
        
        Args:
            data_schema: Instance de DataSchema
            
        Returns:
            dict: Métadonnées du schéma pour le frontend
        """
        fields = data_schema.structured_fields
        
        metadata = {
            'table_name': data_schema.table_name,
            'display_name': data_schema.display_name,
            'icon': data_schema.icon,
            'description': data_schema.description,
            'fields': []
        }
        
        for field in fields:
            if isinstance(field, dict):
                field_meta = self._get_field_metadata_from_dict(field)
            else:
                field_meta = self._get_field_metadata_from_schema(field)
            
            metadata['fields'].append(field_meta)
        
        return metadata
    
    def _get_field_metadata_from_schema(self, field_schema):
        """
        Génère les métadonnées d'un champ pour le frontend depuis un FieldSchema.
        """
        # Mapping field_type vers composant React
        FIELD_TYPE_TO_COMPONENT = {
            'TEXT_SHORT': 'Input',
            'TEXT_LONG': 'Textarea',
            'DECIMAL': 'NumberInput',
            'BOOLEAN': 'Checkbox',
            'DATE': 'DatePicker',
            'DATETIME': 'DateTimePicker',
            'EMAIL': 'EmailInput',
            'URL': 'UrlInput',
            'INTEGER': 'NumberInput',
            'FLOAT': 'NumberInput',
            'JSON': 'JsonEditor',
            'CHOICE_SINGLE': 'Select',
            'CHOICE_MULTIPLE': 'MultiSelect'
        }
        
        # Validation props pour React
        validation_props = {}
        if field_schema.min_value is not None:
            validation_props['min'] = field_schema.min_value
        if field_schema.max_value is not None:
            validation_props['max'] = field_schema.max_value
        if field_schema.min_length is not None:
            validation_props['minLength'] = field_schema.min_length
        if field_schema.max_length is not None:
            validation_props['maxLength'] = field_schema.max_length
        if field_schema.regex_pattern:
            validation_props['pattern'] = field_schema.regex_pattern
        
        return {
            'name': field_schema.name,
            'display_name': field_schema.display_name,
            'field_type': field_schema.field_type,
            'component': FIELD_TYPE_TO_COMPONENT.get(field_schema.field_type, 'Input'),
            'is_required': field_schema.is_required,
            'is_unique': field_schema.is_unique,
            'default_value': field_schema.default_value,
            'choices': field_schema.choices,
            'order': field_schema.order,
            'min_value': field_schema.min_value,
            'max_value': field_schema.max_value,
            'min_length': field_schema.min_length,
            'max_length': field_schema.max_length,
            'regex_pattern': field_schema.regex_pattern,
            'validation_props': validation_props
        }
    
    def _get_field_metadata_from_dict(self, field_dict):
        """
        Génère les métadonnées d'un champ pour le frontend depuis un dictionnaire JSON.
        """
        # Mapping field_type vers composant React
        FIELD_TYPE_TO_COMPONENT = {
            'TEXT_SHORT': 'Input',
            'TEXT_LONG': 'Textarea',
            'DECIMAL': 'NumberInput',
            'BOOLEAN': 'Checkbox',
            'DATE': 'DatePicker',
            'DATETIME': 'DateTimePicker',
            'EMAIL': 'EmailInput',
            'URL': 'UrlInput',
            'INTEGER': 'NumberInput',
            'FLOAT': 'NumberInput',
            'JSON': 'JsonEditor',
            'CHOICE_SINGLE': 'Select',
            'CHOICE_MULTIPLE': 'MultiSelect'
        }
        
        # Validation props pour React
        validation_props = {}
        if field_dict.get('min_value') is not None:
            validation_props['min'] = field_dict['min_value']
        if field_dict.get('max_value') is not None:
            validation_props['max'] = field_dict['max_value']
        if field_dict.get('min_length') is not None:
            validation_props['minLength'] = field_dict['min_length']
        if field_dict.get('max_length') is not None:
            validation_props['maxLength'] = field_dict['max_length']
        if field_dict.get('regex_pattern'):
            validation_props['pattern'] = field_dict['regex_pattern']
        
        field_type = field_dict.get('field_type', 'TEXT_SHORT')
        
        return {
            'name': field_dict['name'],
            'display_name': field_dict.get('display_name', field_dict['name'].capitalize()),
            'field_type': field_type,
            'component': FIELD_TYPE_TO_COMPONENT.get(field_type, 'Input'),
            'is_required': field_dict.get('is_required', False),
            'is_unique': field_dict.get('is_unique', False),
            'default_value': field_dict.get('default_value'),
            'choices': field_dict.get('choices'),
            'order': field_dict.get('order', 1),
            'min_value': field_dict.get('min_value'),
            'max_value': field_dict.get('max_value'),
            'min_length': field_dict.get('min_length'),
            'max_length': field_dict.get('max_length'),
            'regex_pattern': field_dict.get('regex_pattern', ''),
            'validation_props': validation_props
        }
    
    def get_all_serializers(self):
        """
        Génère tous les serializers pour un projet.
        
        Returns:
            dict: Mapping table_name -> serializer_class
        """
        serializers = {}
        
        for data_schema in self.project.schemas.all():
            try:
                serializer_class = self.create_serializer_class(data_schema)
                serializers[data_schema.table_name] = serializer_class
            except Exception as e:
                logger.error(f"Erreur lors de la création du serializer {data_schema.table_name}: {e}")
        
        return serializers
    
    def get_all_metadata(self):
        """
        Génère toutes les métadonnées pour un projet.
        
        Returns:
            dict: Mapping table_name -> metadata
        """
        metadata = {}
        
        for data_schema in self.project.schemas.all():
            try:
                schema_metadata = self.create_metadata_serializer(data_schema)
                metadata[data_schema.table_name] = schema_metadata
            except Exception as e:
                logger.error(f"Erreur lors de la création des métadonnées {data_schema.table_name}: {e}")
        
        return metadata
