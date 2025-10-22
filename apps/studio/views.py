from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
from .models import Project, DataSchema, Page, Component
from .serializers import (
    ProjectSerializer, 
    DataSchemaSerializer, 
    PageSerializer,
    ComponentSerializer
)
from .schema_manager import SchemaManager
from apps.foundation.permissions import IsOrgMember, IsOrgAdmin
import logging

logger = logging.getLogger(__name__)
class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les projets NoCode
    """
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get_queryset(self):
        # Ne retourne que les projets de l'organisation de l'utilisateur
        user = self.request.user
        return Project.objects.filter(organization__members=user).select_related('organization', 'created_by')
    
    def perform_create(self, serializer):
        # Crée un nouveau projet et son schéma associé
        with transaction.atomic():
            # Sauvegarde le projet
            project = serializer.save(
                created_by=self.request.user,
                organization=self.request.user.organization  # Supposant que l'utilisateur a une organisation
            )
            
            # Crée le schéma dans PostgreSQL
            schema_manager = SchemaManager()
            schema_name = schema_manager.create_project_schema(project.id)
            
            # Met à jour le projet avec le nom du schéma
            project.schema_name = schema_name
            project.save(update_fields=['schema_name'])
            
            # Crée une page d'accueil par défaut
            Page.objects.create(
                project=project,
                name="Accueil",
                route="home",
                is_home=True,
                config={
                    "title": "Bienvenue sur votre nouveau site",
                    "sections": [
                        {
                            "type": "hero",
                            "title": "Bienvenue sur votre nouveau site",
                            "subtitle": "Commencez par créer votre première page"
                        }
                    ]
                }
            )
    
    @action(detail=True, methods=['post'])
    def add_table(self, request, pk=None):
        """
        Ajoute une nouvelle table au schéma du projet
        
        Args:
            request: La requête HTTP
            pk: L'ID du projet
            
        Returns:
            Response: La réponse HTTP avec le résultat de l'opération
        """
        project = self.get_object()
        
        # Validation des données
        table_name = request.data.get('table_name')
        fields = request.data.get('fields', [])
        
        if not table_name or not fields:
            return Response(
                {"error": "Les champs 'table_name' et 'fields' sont obligatoires"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Crée d'abord l'entrée dans DataSchema
            schema_serializer = DataSchemaSerializer(data={
                'project': project.id,
                'table_name': table_name,
                'display_name': request.data.get('display_name', table_name),
                'fields_config': fields
            }, context={'request': request})
            
            if not schema_serializer.is_valid():
                return Response(schema_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                # Sauvegarde le schéma
                data_schema = schema_serializer.save()
                
                # Crée la table dans le schéma PostgreSQL
                schema_manager = SchemaManager()
                
                # Convertit la configuration des champs en format pour SQL
                columns = [
                    (field['name'], self._get_sql_type(field['type']), 
                     'NOT NULL' if field.get('required', False) else '')
                    for field in fields
                ]
                
                schema_manager.create_table(
                    schema_name=project.schema_name,
                    table_name=table_name,
                    columns=columns
                )
                
                return Response(
                    DataSchemaSerializer(data_schema).data,
                    status=status.HTTP_201_CREATED
                )
                
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _get_sql_type(self, field_type):
        """Convertit un type de champ en type SQL"""
        type_mapping = {
            'string': 'VARCHAR(255)',
            'text': 'TEXT',
            'integer': 'INTEGER',
            'float': 'FLOAT',
            'boolean': 'BOOLEAN',
            'date': 'DATE',
            'datetime': 'TIMESTAMP WITH TIME ZONE',
            'json': 'JSONB'
        }
        return type_mapping.get(field_type, 'TEXT')
    
    @action(detail=True, methods=['get'])
    def tables(self, request, pk=None):
        """
        Liste toutes les tables du projet
        
        Args:
            request: La requête HTTP
            pk: L'ID du projet
            
        Returns:
            Response: La réponse HTTP avec la liste des tables
        """
        project = self.get_object()
        schemas = DataSchema.objects.filter(project=project)
        return Response(DataSchemaSerializer(schemas, many=True).data)

    @action(detail=True, methods=['get'])
    def export_project(self, request, pk=None):
        """
        Exporte un projet complet au format JSON.

        Returns:
            Response: JSON contenant toutes les données du projet
        """
        project = self.get_object()

        try:
            # Récupérer toutes les données du projet
            pages = Page.objects.filter(project=project)
            schemas = DataSchema.objects.filter(project=project)

            # Construire l'export complet
            export_data = {
                'project': ProjectSerializer(project).data,
                'pages': PageSerializer(pages, many=True).data,
                'schemas': DataSchemaSerializer(schemas, many=True).data,
                'export_info': {
                    'exported_at': timezone.now().isoformat(),
                    'exported_by': request.user.username,
                    'version': '1.0.0',
                    'description': 'Export complet du projet NoCode'
                }
            }

            return Response(export_data)

        except Exception as e:
            return Response(
                {'error': f'Erreur lors de l\'export: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def import_project(self, request):
        """
        Importe un projet depuis un fichier JSON.

        Args:
            request: Requête contenant le fichier JSON du projet

        Returns:
            Response: Informations du projet importé
        """
        try:
            # Récupérer les données JSON
            if 'file' not in request.FILES:
                return Response(
                    {'error': 'Aucun fichier fourni'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            file = request.FILES['file']
            import json

            # Lire et parser le JSON
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                return Response(
                    {'error': 'Fichier JSON invalide'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Valider la structure du JSON
            required_keys = ['project', 'pages', 'schemas']
            missing_keys = [key for key in required_keys if key not in data]
            if missing_keys:
                return Response(
                    {'error': f'Clés manquantes dans le fichier: {", ".join(missing_keys)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                # Créer le projet
                project_data = data['project']
                project_serializer = ProjectSerializer(data={
                    'name': project_data['name'],
                    'organization': request.user.organization.id
                })

                if not project_serializer.is_valid():
                    return Response(
                        {'error': f'Erreur de validation du projet: {project_serializer.errors}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Créer le projet et son schéma PostgreSQL
                project = project_serializer.save(created_by=request.user)
                schema_manager = SchemaManager()
                schema_name = schema_manager.create_project_schema(project.id)
                project.schema_name = schema_name
                project.save(update_fields=['schema_name'])

                # Importer les schémas et créer les tables
                for schema_data in data['schemas']:
                    # Créer l'entrée DataSchema
                    schema_serializer = DataSchemaSerializer(data={
                        'project': project.id,
                        'table_name': schema_data['table_name'],
                        'display_name': schema_data['display_name'],
                        'fields_config': schema_data['fields_config']
                    })

                    if schema_serializer.is_valid():
                        data_schema = schema_serializer.save()

                        # Créer la table dans PostgreSQL
                        columns = [
                            (field['name'], self._get_sql_type(field['type']),
                             'NOT NULL' if field.get('required', False) else '')
                            for field in schema_data['fields_config']
                        ]

                        schema_manager.create_table(
                            schema_name=project.schema_name,
                            table_name=schema_data['table_name'],
                            columns=columns
                        )

                # Importer les pages
                for page_data in data['pages']:
                    page_serializer = PageSerializer(data={
                        'project': project.id,
                        'name': page_data['name'],
                        'route': page_data['route'],
                        'config': page_data['config'],
                        'is_home': page_data['is_home']
                    })

                    if page_serializer.is_valid():
                        page_serializer.save()

                # Retourner les informations du projet importé
                return Response({
                    'message': 'Projet importé avec succès',
                    'project': ProjectSerializer(project).data,
                    'pages_count': len(data['pages']),
                    'schemas_count': len(data['schemas']),
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Erreur lors de l'import de projet: {e}", exc_info=True)
            return Response(
                {'error': f'Erreur lors de l\'import: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DataSchemaViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les schémas de données
    """
    serializer_class = DataSchemaSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get_queryset(self):
        # Filtre par l'organisation de l'utilisateur
        return DataSchema.objects.filter(
            project__organization__members=self.request.user
        ).select_related('project')
    
    def perform_create(self, serializer):
        # La création de table se fait via l'endpoint add_table de ProjectViewSet
        raise NotImplementedError("Utilisez l'endpoint /projects/<id>/add_table/ pour créer des tables")


class PageViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les pages du builder
    """
    serializer_class = PageSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get_queryset(self):
        # Filtre par l'organisation de l'utilisateur
        return Page.objects.filter(
            project__organization__members=self.request.user
        ).select_related('project')
    
    def perform_create(self, serializer):
        # Vérifie que l'utilisateur a le droit de créer une page pour ce projet
        project = serializer.validated_data['project']
        if not project.organization.members.filter(id=self.request.user.id).exists():
            raise PermissionDenied("Vous n'avez pas la permission d'ajouter des pages à ce projet.")
        
        serializer.save()


class ComponentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour consulter le catalogue de composants (lecture seule)
    """
    serializer_class = ComponentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Retourne seulement les composants actifs
        return Component.objects.filter(is_active=True)

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """
        Retourne la liste des catégories de composants disponibles
        """
        categories = Component.objects.filter(is_active=True).values_list('category', flat=True).distinct()
        return Response(list(categories))

    @action(detail=True, methods=['get'])
    def properties_schema(self, request, pk=None):
        """
        Retourne le schéma des propriétés d'un composant spécifique
        """
        component = self.get_object()
        return Response({
            'name': component.name,
            'properties': component.properties,
            'validation_rules': component.validation_rules,
            'default_config': component.default_config
        })

