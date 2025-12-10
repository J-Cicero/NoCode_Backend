from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from .permissions import HasProjectAccess
from apps.foundation.permissions import IsOrgMember
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .models import Project, DataSchema, FieldSchema, Page, ComponentInstance
from .serializers import ProjectSerializer, DataSchemaSerializer, FieldSchemaSerializer, PageSerializer, ComponentSerializer
from .user_friendly_serializers import TableCreationSerializer, TableUpdateSerializer

User = get_user_model()


class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les projets NoCode
    """
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, HasProjectAccess]

    def get_queryset(self):
        return Project.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publier le projet - déclenche la génération Runtime"""
        project = self.get_object()
        
        # TODO: Implémenter la génération Runtime
        return Response({
            'message': 'Génération de l\'application démarrée',
            'project_id': str(project.tracking_id)
        })

    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        """Dépublier le projet"""
        project = self.get_object()
        project.status = 'draft'
        project.save()
        
        return Response({'message': 'Projet dépublié'})

    @action(detail=True, methods=['get'])
    def deployment_status(self, request, pk=None):
        """Statut de déploiement du projet"""
        project = self.get_object()
        return Response({
            'project_id': str(project.tracking_id),
            'status': project.status,
            'name': project.name
        })

    @action(detail=True, methods=['get'])
    def schemas(self, request, pk=None):
        """Liste des schémas de données du projet"""
        project = self.get_object()
        schemas = DataSchema.objects.filter(project=project)
        serializer = DataSchemaSerializer(schemas, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='tables/create')
    def create_table(self, request, pk=None):
        """
        Créer une table avec formulaire intuitif (sans JSON).
        Endpoint user-friendly pour la création de schémas de données.
        """
        project = self.get_object()
        
        # Ajouter le project_id aux données
        data = request.data.copy()
        data['project_id'] = project.id
        
        serializer = TableCreationSerializer(
            data=data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            data_schema = serializer.save()
            # Retourner le schéma créé avec les champs
            response_data = {
                'id': data_schema.id,
                'table_name': data_schema.table_name,
                'display_name': data_schema.display_name,
                'description': data_schema.description,
                'icon': data_schema.icon,
                'auto_generate_pages': data_schema.auto_generate_pages,
                'created_at': data_schema.created_at,
                'fields_count': data_schema.fields.count(),
                'message': 'Table créée avec succès'
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='tables')
    def list_tables(self, request, pk=None):
        """
        Lister les tables du projet avec leurs champs.
        """
        project = self.get_object()
        schemas = DataSchema.objects.filter(project=project)
        
        tables_data = []
        for schema in schemas:
            fields = FieldSchema.objects.filter(schema=schema)
            tables_data.append({
                'id': schema.id,
                'table_name': schema.table_name,
                'display_name': schema.display_name,
                'description': schema.description,
                'icon': schema.icon,
                'auto_generate_pages': schema.auto_generate_pages,
                'created_at': schema.created_at,
                'fields_count': fields.count(),
                'fields': [
                    {
                        'id': field.id,
                        'name': field.name,
                        'display_name': field.display_name,
                        'field_type': field.field_type,
                        'is_required': field.is_required,
                        'is_unique': field.is_unique
                    }
                    for field in fields
                ]
            })
        
        return Response({
            'project': {
                'id': project.id,
                'name': project.name,
                'tracking_id': project.tracking_id
            },
            'tables': tables_data
        })

    @action(detail=True, methods=['put'], url_path='tables/(?P<table_id>[^/.]+)')
    def update_table(self, request, pk=None, table_id=None):
        """
        Mettre à jour une table (ajouter/supprimer des champs).
        """
        project = self.get_object()
        
        try:
            data_schema = DataSchema.objects.get(id=table_id, project=project)
        except DataSchema.DoesNotExist:
            return Response(
                {'error': 'Table introuvable'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = TableUpdateSerializer(
            data_schema,
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            updated_schema = serializer.save()
            return Response({
                'message': 'Table mise à jour avec succès',
                'fields_count': updated_schema.fields.count()
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DataSchemaViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les schémas de données (tables)
    """
    serializer_class = DataSchemaSerializer
    permission_classes = [IsAuthenticated, HasProjectAccess]

    def get_queryset(self):
        project_id = self.request.query_params.get('project')
        if project_id:
            return DataSchema.objects.filter(project_id=project_id, project__owner=self.request.user)
        return DataSchema.objects.filter(project__owner=self.request.user)

    def perform_create(self, serializer):
        # Le signal auto_generate_django_model se déclenchera ici
        serializer.save()

    @action(detail=True, methods=['get'])
    def fields(self, request, pk=None):
        """Liste des champs du schéma"""
        schema = self.get_object()
        fields = FieldSchema.objects.filter(schema=schema)
        serializer = FieldSchemaSerializer(fields, many=True)
        return Response(serializer.data)


class FieldSchemaViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les champs des schémas de données
    """
    serializer_class = FieldSchemaSerializer
    permission_classes = [IsAuthenticated, HasProjectAccess]

    def get_queryset(self):
        schema_id = self.request.query_params.get('schema')
        if schema_id:
            return FieldSchema.objects.filter(schema_id=schema_id, schema__project__owner=self.request.user)
        return FieldSchema.objects.filter(schema__project__owner=self.request.user)

    def perform_create(self, serializer):
        # Le signal auto_add_field_to_model se déclenchera ici
        serializer.save()


class EditorViewSet(viewsets.ViewSet):
    """
    API endpoint pour l'éd et drop
    """
    permission_classes = [IsAuthenticated, HasProjectAccess]

    @action(detail=False, methods=['post'])
    def add_component(self, request):
        """Ajouter un composant - la page est créée automatiquement"""
        project_id = request.data.get('project_id')
        component_type = request.data.get('component_type')
        position = request.data.get('position', {})
        config = request.data.get('config', {})

        if not project_id or not component_type:
            return Response(
                {'error': 'project_id et component_type sont requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            project = Project.objects.get(tracking_id=project_id, owner=request.user)
        except Project.DoesNotExist:
            return Response(
                {'error': 'Projet non trouvé'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Créer une page si aucune n'existe
        page, created = Page.objects.get_or_create(
            project=project,
            is_home=True,
            defaults={'name': "Page d'accueil"}
        )

        # Créer le composant
        component = ComponentInstance.objects.create(
            page=page,
            component_type=component_type,
            position=position,
            config=config
        )

        return Response({
            'component_id': str(component.tracking_id),
            'page_id': str(page.tracking_id),
            'page_created': created
        })

    @action(detail=False, methods=['put'])
    def move_component(self, request):
        """Déplacer un composant"""
        component_id = request.data.get('component_id')
        position = request.data.get('position', {})

        if not component_id:
            return Response(
                {'error': 'component_id requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            component = ComponentInstance.objects.get(
                tracking_id=component_id,
                page__project__owner=request.user
            )
            component.position = position
            component.save()
            
            return Response({'message': 'Composant déplacé'})
        except ComponentInstance.DoesNotExist:
            return Response(
                {'error': 'Composant non trouvé'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['delete'])
    def remove_component(self, request):
        """Retirer un composant"""
        component_id = request.data.get('component_id')

        if not component_id:
            return Response(
                {'error': 'component_id requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            component = ComponentInstance.objects.get(
                tracking_id=component_id,
                page__project__owner=request.user
            )
            component.delete()
            
            return Response({'message': 'Composant supprimé'})
        except ComponentInstance.DoesNotExist:
            return Response(
                {'error': 'Composant non trouvé'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def state(self, request):
        """État actuel de l'éditeur"""
        project_id = request.query_params.get('project_id')
        
        if not project_id:
            return Response(
                {'error': 'project_id requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            project = Project.objects.get(tracking_id=project_id, owner=request.user)
            pages = Page.objects.filter(project=project)
            
            state = {
                'project': {
                    'id': str(project.tracking_id),
                    'name': project.name,
                    'status': project.status
                },
                'pages': []
            }

            for page in pages:
                components = ComponentInstance.objects.filter(page=page)
                page_data = {
                    'id': str(page.tracking_id),
                    'name': page.name,
                    'is_home': page.is_home,
                    'components': ComponentSerializer(components, many=True).data
                }
                state['pages'].append(page_data)

            return Response(state)
        except Project.DoesNotExist:
            return Response(
                {'error': 'Projet non trouvé'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class PageViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les pages
    """
    serializer_class = PageSerializer
    permission_classes = [IsAuthenticated, HasProjectAccess]

    def get_queryset(self):
        return Page.objects.filter(project__owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['get'])
    def components(self, request, pk=None):
        """Liste des composants d'une page"""
        page = self.get_object()
        components = ComponentInstance.objects.filter(page=page)
        serializer = ComponentSerializer(components, many=True)
        return Response(serializer.data)


class ComponentViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les composants
    """
    serializer_class = ComponentSerializer
    permission_classes = [IsAuthenticated, HasProjectAccess]

    def get_queryset(self):
        return ComponentInstance.objects.filter(page__project__owner=self.request.user)

    def perform_create(self, serializer):
        # Le signal auto_create_page_if_needed se déclenchera ici
        serializer.save()
