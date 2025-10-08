from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db import transaction
from .models import Project, DataSchema, Page
from .serializers import ProjectSerializer, DataSchemaSerializer, PageSerializer
from .schema_manager import SchemaManager
from apps.foundation.permissions import IsOrgMember, IsOrgAdmin

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
                
                schema_manager.create_dynamic_table(
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

