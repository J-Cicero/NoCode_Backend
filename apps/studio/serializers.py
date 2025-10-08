from rest_framework import serializers
from .models import Project, DataSchema, Page
from apps.foundation.serializers import OrganizationSerializer

class ProjectSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'organization', 'organization_name',
            'schema_name', 'created_by', 'created_by_username',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['schema_name', 'created_by', 'created_at', 'updated_at']
        extra_kwargs = {
            'organization': {'required': True}
        }
    
    def validate_name(self, value):
        # Vérifie que le nom du projet est unique pour cette organisation
        user = self.context['request'].user
        org = self.initial_data.get('organization')
        
        if Project.objects.filter(
            organization=org,
            name__iexact=value
        ).exists():
            raise serializers.ValidationError("Un projet avec ce nom existe déjà dans cette organisation.")
        return value


class DataSchemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSchema
        fields = ['id', 'project', 'table_name', 'display_name', 'fields_config', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_table_name(self, value):
        # S'assure que le nom de la table est valide pour PostgreSQL
        import re
        if not re.match(r'^[a-z][a-z0-9_]*$', value):
            raise serializers.ValidationError(
                "Le nom de la table ne peut contenir que des lettres minuscules, des chiffres et des tirets bas, et doit commencer par une lettre."
            )
        return value
    
    def validate_fields_config(self, value):
        # Validation de base de la configuration des champs
        if not isinstance(value, list):
            raise serializers.ValidationError("La configuration des champs doit être une liste.")
        
        required_fields = {'name', 'type'}
        for field in value:
            if not isinstance(field, dict):
                raise serializers.ValidationError("Chaque champ doit être un objet.")
            
            missing_fields = required_fields - set(field.keys())
            if missing_fields:
                raise serializers.ValidationError(
                    f"Les champs suivants sont obligatoires : {', '.join(missing_fields)}"
                )
        return value


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ['id', 'project', 'name', 'route', 'config', 'is_home', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_route(self, value):
        # Nettoie le chemin de la route
        if not value.startswith('/'):
            value = '/' + value
        return value.strip('/')
    
    def validate(self, data):
        # Vérifie qu'une seule page peut être la page d'accueil
        if data.get('is_home', False):
            project = data.get('project') or self.instance and self.instance.project
            if Page.objects.filter(project=project, is_home=True).exclude(pk=getattr(self.instance, 'pk', None)).exists():
                raise serializers.ValidationError({
                    'is_home': "Une page est déjà définie comme page d'accueil pour ce projet."
                })
        return data
