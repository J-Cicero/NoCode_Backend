from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from .models import Project, DataSchema, Page, Component
from .serializers import (
    ProjectSerializer, 
    DataSchemaSerializer, 
    PageSerializer,
    ComponentSerializer
)
from apps.studio.services.project_service import ProjectService
from apps.studio.services.schema_service import SchemaService
from apps.foundation.models import OrganizationMember
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
        """Retourne les projets accessibles à l'utilisateur.

        - Projets personnels : organization is null et created_by = user
        - Projets d'organisation : organisations dont l'utilisateur est membre
        """
        user = self.request.user

        org_ids = OrganizationMember.objects.filter(
            user=user,
            status='ACTIVE'
        ).values_list('organization_id', flat=True)

        return Project.objects.filter(
            Q(organization__isnull=True, created_by=user) |
            Q(organization_id__in=org_ids)
        ).select_related('organization', 'created_by')
    
    def perform_create(self, serializer):
        """Crée un nouveau projet (personnel ou d'organisation) et son schéma associé.

        - Projet personnel : aucun organization_id fourni → organization = NULL
        - Projet d'organisation : organization_id fourni →
            - require que l'utilisateur soit OWNER de cette organisation
        """
        user = self.request.user
        org_tracking_id = serializer.validated_data.get('organization_id')

        # Vérifie les droits si le projet est lié à une organisation
        if org_tracking_id and not ProjectService.user_can_create_for_org(user, org_tracking_id):
            raise PermissionDenied("Seul le propriétaire de l'organisation peut créer un projet pour celle-ci.")

        # Sauvegarde le projet (le serializer gère l'association éventuelle à l'organisation)
        project = serializer.save()

        # Bootstrap du schéma PostgreSQL et de la page d'accueil via le service
        ProjectService.bootstrap_project_with_schema_and_homepage(project)
    
    @action(detail=True, methods=['post'])
    def add_table(self, request, pk=None):

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
            data_schema = SchemaService.add_table_to_project(
                project=project,
                table_name=table_name,
                display_name=request.data.get('display_name', table_name),
                fields=fields,
                serializer_context={'request': request},
            )

            return Response(
                DataSchemaSerializer(data_schema).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @action(detail=True, methods=['get'])
    def tables(self, request, pk=None):

        project = self.get_object()
        schemas = DataSchema.objects.filter(project=project)
        return Response(DataSchemaSerializer(schemas, many=True).data)

    @action(detail=True, methods=['get'])
    def export_project(self, request, pk=None):

        project = self.get_object()

        try:

            pages = Page.objects.filter(project=project)
            schemas = DataSchema.objects.filter(project=project)

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

        try:
            if 'file' not in request.FILES:
                return Response(
                    {'error': 'Aucun fichier fourni'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            file = request.FILES['file']
            import json

            try:
                data = json.load(file)
            except json.JSONDecodeError:
                return Response(
                    {'error': 'Fichier JSON invalide'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            required_keys = ['project', 'pages', 'schemas']
            missing_keys = [key for key in required_keys if key not in data]
            if missing_keys:
                return Response(
                    {'error': f'Clés manquantes dans le fichier: {", ".join(missing_keys)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():

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

                project = project_serializer.save(created_by=request.user)
                schema_manager = SchemaManager()
                schema_name = schema_manager.create_project_schema(project.id)
                project.schema_name = schema_name
                project.save(update_fields=['schema_name'])

                for schema_data in data['schemas']:

                    schema_serializer = DataSchemaSerializer(data={
                        'project': project.id,
                        'table_name': schema_data['table_name'],
                        'display_name': schema_data['display_name'],
                        'fields_config': schema_data['fields_config']
                    })

                    if schema_serializer.is_valid():
                        data_schema = schema_serializer.save()

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

    serializer_class = DataSchemaSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get_queryset(self):
        # Filtre par l'organisation de l'utilisateur
        return DataSchema.objects.filter(
            project__organization__members=self.request.user
        ).select_related('project')
    
    def perform_create(self, serializer):
        # La création de table se fait via l'endpoint add_table de ProjectViewSet
        raise NotImplementedError("Utilisez l'endpoint convenable  pour créer des tables")


class PageViewSet(viewsets.ModelViewSet):
    serializer_class = PageSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get_queryset(self):
        return Page.objects.filter(
            project__organization__members=self.request.user
        ).select_related('project')
    
    def perform_create(self, serializer):
        project = serializer.validated_data['project']
        if not project.organization.members.filter(id=self.request.user.id).exists():
            raise PermissionDenied("Vous n'avez pas la permission d'ajouter des pages à ce projet.")
        
        serializer.save()


class ComponentViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = ComponentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Component.objects.filter(is_active=True)

    @action(detail=False, methods=['get'])
    def categories(self, request):

        categories = Component.objects.filter(is_active=True).values_list('category', flat=True).distinct()
        return Response(list(categories))

    @action(detail=True, methods=['get'])
    def properties_schema(self, request, pk=None):

        component = self.get_object()
        return Response({
            'name': component.name,
            'properties': component.properties,
            'validation_rules': component.validation_rules,
            'default_config': component.default_config
        })

