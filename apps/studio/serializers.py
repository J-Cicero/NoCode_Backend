from rest_framework import serializers
from .models import Project, DataSchema, Page, Component
from apps.foundation.serializers import OrganizationBaseSerializer


class ProjectSerializer(serializers.ModelSerializer):
    tracking_id = serializers.UUIDField(read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    organization_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'tracking_id', 'name',
            'organization_id', 'organization_name',
            'schema_name', 'created_by_username',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['tracking_id', 'schema_name', 'created_at', 'updated_at', 'created_by_username']
    
    def validate_name(self, value):
        # Vérifie que le nom du projet est unique pour cette organisation (ou pour les projets personnels)
        org_id = self.initial_data.get('organization_id')
        qs = Project.objects.all()
        if org_id:
            qs = qs.filter(organization__tracking_id=org_id)
        else:
            qs = qs.filter(organization__isnull=True)

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Un projet avec ce nom existe déjà pour cette portée.")
        return value

    def create(self, validated_data):
        # Lier éventuellement à une organisation via organization_id, laissé à la vue/service pour valider les droits
        organization_id = validated_data.pop('organization_id', None)
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        project = Project(
            name=validated_data['name'],
            created_by=user,
        )

        if organization_id:
            try:
                from apps.foundation.models import Organization
                org = Organization.objects.get(tracking_id=organization_id)
                project.organization = org
            except Organization.DoesNotExist:
                raise serializers.ValidationError({'organization_id': "Organisation introuvable."})

        project.save()
        return project


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
        """Valide la configuration des champs (fields_config).

        Format attendu : liste de dicts
        [
            {
                "name": "field_name",          # obligatoire
                "type": "string|integer|...",  # obligatoire
                "label": "Libellé",           # optionnel
                "required": true/false,         # optionnel
                "unique": true/false,           # optionnel
                "default": any                  # optionnel
            },
            ...
        ]
        """
        if not isinstance(value, list):
            raise serializers.ValidationError("La configuration des champs doit être une liste.")

        allowed_types = {"string", "text", "integer", "float", "boolean", "date", "datetime", "json"}
        required_fields = {"name", "type"}

        for field in value:
            if not isinstance(field, dict):
                raise serializers.ValidationError("Chaque champ doit être un objet.")

            missing_fields = required_fields - set(field.keys())
            if missing_fields:
                raise serializers.ValidationError(
                    f"Les champs suivants sont obligatoires : {', '.join(sorted(missing_fields))}"
                )

            field_type = field.get("type")
            if field_type not in allowed_types:
                raise serializers.ValidationError(
                    f"Type de champ invalide pour '{field.get('name')}': '{field_type}'. "
                    f"Types autorisés: {', '.join(sorted(allowed_types))}."
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
class ComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Component
        fields = [
            'id', 'name', 'display_name', 'description', 'category', 'icon',
            'properties', 'validation_rules', 'default_config',
            'is_active', 'version', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_name(self, value):
        """Vérifie que le nom du composant est unique"""
        if Component.objects.filter(name=value).exists():
            if self.instance and self.instance.name == value:
                return value  # Même nom pour update
            raise serializers.ValidationError("Un composant avec ce nom existe déjà.")
        return value

    def validate_properties(self, value):
        """Valide la structure des propriétés"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Les propriétés doivent être un objet.")

        # Validation basique de la structure des propriétés
        for prop_name, prop_config in value.items():
            if not isinstance(prop_config, dict):
                raise serializers.ValidationError(f"La propriété '{prop_name}' doit être un objet.")

            required_fields = ['type', 'label']
            missing_fields = [field for field in required_fields if field not in prop_config]
            if missing_fields:
                raise serializers.ValidationError(
                    f"Les champs suivants sont requis pour '{prop_name}': {', '.join(missing_fields)}"
                )

        return value
