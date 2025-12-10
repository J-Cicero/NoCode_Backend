"""
Serializers user-friendly pour la création de tables et champs sans manipulation JSON.
Permet aux utilisateurs de créer des schémas de données via des formulaires intuitifs.
"""
from rest_framework import serializers
from .models import DataSchema, FieldSchema, Project
from apps.foundation.models import Organization


class FieldDefinitionSerializer(serializers.Serializer):
    """
    Serializer pour la définition individuelle d'un champ.
    Remplace la manipulation manuelle du JSON fields_config.
    """
    name = serializers.CharField(
        max_length=100,
        help_text="Nom technique du champ (ex: nom_produit, prix)"
    )
    display_name = serializers.CharField(
        max_length=100,
        help_text="Nom d'affichage du champ (ex: Nom du produit, Prix)"
    )
    field_type = serializers.ChoiceField(
        choices=FieldSchema.FieldType.choices,
        help_text="Type de données du champ"
    )
    is_required = serializers.BooleanField(
        default=False,
        help_text="Ce champ est-il obligatoire ?"
    )
    is_unique = serializers.BooleanField(
        default=False,
        help_text="Les valeurs doivent-elles être uniques ?"
    )
    default_value = serializers.JSONField(
        required=False,
        allow_null=True,
        help_text="Valeur par défaut (optionnel)"
    )
    
    # Validation spécifique par type
    min_value = serializers.FloatField(
        required=False,
        allow_null=True,
        help_text="Valeur minimale (pour nombres)"
    )
    max_value = serializers.FloatField(
        required=False,
        allow_null=True,
        help_text="Valeur maximale (pour nombres)"
    )
    min_length = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Longueur minimale (pour textes)"
    )
    max_length = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Longueur maximale (pour textes)"
    )
    regex_pattern = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Pattern de validation (regex)"
    )
    
    # Pour les champs de type CHOICE
    choices = serializers.JSONField(
        required=False,
        allow_null=True,
        help_text="Liste de choix pour les champs SELECT (ex: ['Option 1', 'Option 2'])"
    )
    
    # Pour les relations
    related_schema_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID du schéma lié (pour les relations)"
    )

    def validate_name(self, value):
        """Valide que le nom du champ est valide pour PostgreSQL."""
        import re
        if not re.match(r'^[a-z][a-z0-9_]*$', value):
            raise serializers.ValidationError(
                "Le nom du champ ne peut contenir que des lettres minuscules, des chiffres et des tirets bas, et doit commencer par une lettre."
            )
        return value

    def validate(self, attrs):
        """Validation croisée des attributs."""
        field_type = attrs.get('field_type')
        
        # Validation pour les champs numériques
        if field_type in ['NUMBER_INT', 'NUMBER_DECIMAL']:
            if attrs.get('min_value') and attrs.get('max_value'):
                if attrs['min_value'] >= attrs['max_value']:
                    raise serializers.ValidationError({
                        'min_value': 'La valeur minimale doit être inférieure à la valeur maximale.'
                    })
        
        # Validation pour les champs texte
        if field_type in ['TEXT_SHORT', 'TEXT_LONG']:
            if attrs.get('min_length') and attrs.get('max_length'):
                if attrs['min_length'] >= attrs['max_length']:
                    raise serializers.ValidationError({
                        'min_length': 'La longueur minimale doit être inférieure à la longueur maximale.'
                    })
        
        # Validation pour les champs de type CHOICE
        if field_type in ['CHOICE_SINGLE', 'CHOICE_MULTIPLE']:
            if not attrs.get('choices'):
                raise serializers.ValidationError({
                    'choices': 'Les champs de type choix doivent avoir une liste de choix.'
                })
        
        # Validation pour les relations
        if 'RELATION' in field_type:
            if not attrs.get('related_schema_id'):
                raise serializers.ValidationError({
                    'related_schema_id': 'Les champs de relation doivent spécifier un schéma lié.'
                })
        
        return attrs


class TableCreationSerializer(serializers.Serializer):
    """
    Serializer pour la création intuitive de tables avec champs.
    Interface utilisateur sans manipulation JSON.
    """
    project_id = serializers.IntegerField(
        help_text="ID du projet dans lequel créer la table"
    )
    table_name = serializers.CharField(
        max_length=63,
        help_text="Nom technique de la table (ex: produits, clients)"
    )
    display_name = serializers.CharField(
        max_length=255,
        help_text="Nom d'affichage de la table (ex: Produits, Clients)"
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Description de la table (optionnel)"
    )
    icon = serializers.CharField(
        max_length=10,
        default='📋',
        help_text="Icône pour représenter la table"
    )
    auto_generate_pages = serializers.BooleanField(
        default=True,
        help_text="Générer automatiquement les pages (liste, détail, formulaire) ?"
    )
    fields = FieldDefinitionSerializer(
        many=True,
        help_text="Liste des champs de la table"
    )

    def validate_table_name(self, value):
        """Valide que le nom de la table est valide pour PostgreSQL."""
        import re
        if not re.match(r'^[a-z][a-z0-9_]*$', value):
            raise serializers.ValidationError(
                "Le nom de la table ne peut contenir que des lettres minuscules, des chiffres et des tirets bas, et doit commencer par une lettre."
            )
        return value

    def validate_project_id(self, value):
        """Valide que le projet existe et que l'utilisateur a les droits."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Utilisateur non authentifié.")
        
        try:
            project = Project.objects.get(id=value)
            # Vérifier que l'utilisateur a accès au projet
            if project.created_by != request.user:
                # Vérifier si c'est un projet d'organisation
                if not project.organization:
                    raise serializers.ValidationError("Vous n'avez pas accès à ce projet.")
                
                # Vérifier si l'utilisateur est membre de l'organisation
                is_member = project.organization.members.filter(
                    id=request.user.id,
                    status='ACTIVE'
                ).exists()
                if not is_member:
                    raise serializers.ValidationError("Vous n'avez pas accès à ce projet.")
            
            return value
        except Project.DoesNotExist:
            raise serializers.ValidationError("Projet introuvable.")

    def validate_fields(self, value):
        """Valide qu'il y a au moins un champ et que les noms sont uniques."""
        if not value:
            raise serializers.ValidationError("Une table doit contenir au moins un champ.")
        
        # Vérifier l'unicité des noms de champs
        field_names = [field['name'] for field in value]
        if len(field_names) != len(set(field_names)):
            raise serializers.ValidationError("Les noms des champs doivent être uniques.")
        
        return value

    def create(self, validated_data):
        """Crée le schéma de données et ses champs."""
        request = self.context.get('request')
        fields_data = validated_data.pop('fields')
        project_id = validated_data.pop('project_id')
        
        # Récupérer le projet
        project = Project.objects.get(id=project_id)
        
        # Créer le schéma de données
        data_schema = DataSchema.objects.create(
            project=project,
            created_by=request.user,
            **validated_data
        )
        
        # Créer les champs
        for field_data in fields_data:
            # Extraire les données de relation si présentes
            related_schema_id = field_data.pop('related_schema_id', None)
            
            # Créer le champ
            field = FieldSchema.objects.create(
                schema=data_schema,
                created_by=request.user,
                **field_data
            )
            
            # Gérer la relation si spécifiée
            if related_schema_id:
                try:
                    related_schema = DataSchema.objects.get(
                        id=related_schema_id, 
                        project=project  # Sécurité: seulement dans le même projet
                    )
                    field.related_schema = related_schema
                    field.save()
                except DataSchema.DoesNotExist:
                    # Ignorer silencieusement si le schéma lié n'existe pas
                    pass
        
        return data_schema


class TableUpdateSerializer(serializers.Serializer):
    """
    Serializer pour la mise à jour de tables (ajout/suppression de champs).
    """
    display_name = serializers.CharField(
        max_length=255,
        required=False,
        help_text="Nouveau nom d'affichage de la table"
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Nouvelle description de la table"
    )
    icon = serializers.CharField(
        max_length=10,
        required=False,
        help_text="Nouvelle icône pour la table"
    )
    new_fields = FieldDefinitionSerializer(
        many=True,
        required=False,
        help_text="Nouveaux champs à ajouter"
    )
    fields_to_delete = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="IDs des champs à supprimer"
    )

    def validate_fields_to_delete(self, value):
        """Valide que les champs à supprimer existent."""
        if value:
            # La validation sera faite dans la méthode update
            pass
        return value

    def update(self, instance, validated_data):
        """Met à jour le schéma de données et ses champs."""
        request = self.context.get('request')
        
        # Mettre à jour les champs du schéma
        if 'display_name' in validated_data:
            instance.display_name = validated_data['display_name']
        if 'description' in validated_data:
            instance.description = validated_data['description']
        if 'icon' in validated_data:
            instance.icon = validated_data['icon']
        
        instance.save()
        
        # Ajouter de nouveaux champs
        new_fields_data = validated_data.get('new_fields', [])
        for field_data in new_fields_data:
            related_schema_id = field_data.pop('related_schema_id', None)
            
            field = FieldSchema.objects.create(
                schema=instance,
                created_by=request.user,
                **field_data
            )
            
            if related_schema_id:
                try:
                    related_schema = DataSchema.objects.get(
                        id=related_schema_id,
                        project=instance.project
                    )
                    field.related_schema = related_schema
                    field.save()
                except DataSchema.DoesNotExist:
                    pass
        
        # Supprimer des champs
        fields_to_delete = validated_data.get('fields_to_delete', [])
        if fields_to_delete:
            FieldSchema.objects.filter(
                id__in=fields_to_delete,
                schema=instance
            ).delete()
        
        return instance
