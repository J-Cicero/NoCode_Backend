from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from .permissions import HasProjectAccess
from apps.foundation.permissions import IsOrgMember
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import Project, DataSchema, FieldSchema, Page, ComponentInstance, Component
from apps.foundation.services.event_bus import EventBus
from .serializers import ProjectSerializer, DataSchemaSerializer, FieldSchemaSerializer, PageSerializer, ComponentSerializer
from .user_friendly_serializers import TableCreationSerializer, TableUpdateSerializer

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        summary="📋 Lister tous les projets accessibles",
        description="""
        **Récupère la liste de tous les projets accessibles par l'utilisateur connecté.**
        
        ## 🎯 Projets retournés :
        
        ### Pour un Client Individuel (sans organisation) :
        - ✅ Tous les projets qu'il a créés personnellement
        - ✅ Les projets où `organization` est NULL
        
        ### Pour un Membre d'Organisation :
        - ✅ Tous ses projets personnels (créés par lui, organization=NULL)
        - ✅ Tous les projets de ses organisations (où il est membre actif)
        - ✅ Visible par tous les membres (OWNER, ADMIN, MEMBER)
        
        ## 📊 Réponse :
        - Liste de projets avec leurs détails complets
        - Inclut : tracking_id, name, schema_name, organization, created_by, dates
        
        ## 🔐 Permissions :
        - Authentification requise (Bearer Token)
        - Retourne uniquement les projets accessibles par l'utilisateur
        
        ## 💡 Exemple d'utilisation :
        ```
        GET /api/v1/studio/projects/
        Authorization: Bearer <votre_token>
        ```
        """,
        tags=["📁 Studio - Projets"]
    ),
    create=extend_schema(
        summary="➕ Créer un nouveau projet",
        description="""
        **Crée un nouveau projet NoCode.**
        
        ## 🎯 Types de projets :
        
        ### 1️⃣ Projet Personnel (Client Individuel) :
        ```json
        {
            "name": "Mon Application Mobile"
            // Ne pas fournir organization_id
        }
        ```
        - Le projet sera lié uniquement au créateur
        - `organization` sera NULL
        - Seul le créateur aura accès
        
        ### 2️⃣ Projet d'Organisation :
        ```json
        {
            "name": "ERP Entreprise",
            "organization_id": "uuid-de-votre-organisation"
        }
        ```
        - Le projet sera lié à l'organisation
        - Tous les membres actifs de l'organisation auront accès
        - OWNER/ADMIN peuvent modifier, MEMBER peut lire
        
        ## ⚙️ Ce qui est créé automatiquement :
        - ✅ Un schéma PostgreSQL unique (`schema_name`)
        - ✅ Une page d'accueil par défaut
        - ✅ Une structure de base pour l'application
        
        ## 🔐 Permissions :
        - Authentification requise
        - Pour créer un projet d'organisation : être membre actif de cette organisation
        
        ## 📊 Réponse :
        - Détails complets du projet créé
        - Code HTTP 201 Created
        
        ## ⚠️ Notes importantes :
        - Le nom du projet doit être unique dans votre espace
        - Le schema_name est généré automatiquement
        - La suppression d'un projet supprime toutes ses données
        """,
        tags=["📁 Studio - Projets"],
        examples=[
            OpenApiExample(
                "Projet Personnel",
                value={"name": "Mon Portfolio"},
                request_only=True
            ),
            OpenApiExample(
                "Projet Organisation",
                value={
                    "name": "CRM Enterprise",
                    "organization_id": "550e8400-e29b-41d4-a716-446655440000"
                },
                request_only=True
            )
        ]
    ),
    retrieve=extend_schema(
        summary="🔍 Récupérer les détails d'un projet",
        description="""
        **Récupère les informations détaillées d'un projet spécifique.**
        
        ## 🎯 Informations retournées :
        - tracking_id (UUID unique du projet)
        - name (nom du projet)
        - schema_name (nom du schéma PostgreSQL)
        - organization (organisation liée, ou NULL si projet personnel)
        - created_by (email et nom du créateur)
        - created_at / updated_at (dates de création/modification)
        
        ## 🔐 Permissions :
        - Authentification requise
        - Accès autorisé si :
          - ✅ Vous êtes le créateur du projet
          - ✅ Vous êtes membre actif de l'organisation du projet
        
        ## 💡 Exemple :
        ```
        GET /api/v1/studio/projects/{tracking_id}/
        Authorization: Bearer <votre_token>
        ```
        """,
        tags=["📁 Studio - Projets"]
    ),
    update=extend_schema(
        summary="✏️ Modifier un projet (PUT complet)",
        description="""
        **Modifie complètement un projet existant.**
        
        ## 📝 Champs modifiables :
        - `name` : Nouveau nom du projet
        - `organization_id` : Changer d'organisation (si autorisé)
        
        ## 🔐 Permissions :
        - Authentification requise
        - Modification autorisée si :
          - ✅ Vous êtes le créateur du projet
          - ✅ Vous êtes OWNER ou ADMIN de l'organisation du projet
          - ❌ Les MEMBER ne peuvent PAS modifier
        
        ## ⚠️ Notes :
        - Le schema_name ne peut pas être modifié
        - Le tracking_id ne change jamais
        
        ## 💡 Exemple :
        ```json
        PUT /api/v1/studio/projects/{tracking_id}/
        {
            "name": "Nouveau Nom du Projet"
        }
        ```
        """,
        tags=["📁 Studio - Projets"]
    ),
    partial_update=extend_schema(
        summary="✏️ Modifier partiellement un projet (PATCH)",
        description="""
        **Modifie partiellement un projet existant.**
        
        Même fonctionnement que PUT, mais vous pouvez ne modifier que les champs souhaités.
        
        ## 💡 Exemple :
        ```json
        PATCH /api/v1/studio/projects/{tracking_id}/
        {
            "name": "Nouveau Nom"
        }
        ```
        
        ## 🔐 Permissions : Identiques à PUT
        """,
        tags=["📁 Studio - Projets"]
    ),
    destroy=extend_schema(
        summary="🗑️ Supprimer un projet",
        description="""
        **Supprime définitivement un projet et toutes ses données associées.**
        
        ## ⚠️ ATTENTION - Cette action est IRRÉVERSIBLE !
        
        ### Ce qui sera supprimé :
        - 🗑️ Le projet lui-même
        - 🗑️ Le schéma PostgreSQL complet
        - 🗑️ Toutes les tables du projet
        - 🗑️ Toutes les pages et composants
        - 🗑️ Toutes les données stockées dans ce projet
        
        ## 🔐 Permissions :
        - Authentification requise
        - Suppression autorisée si :
          - ✅ Vous êtes le créateur du projet
          - ✅ Vous êtes OWNER ou ADMIN de l'organisation du projet
          - ❌ Les MEMBER ne peuvent PAS supprimer
        
        ## 📊 Réponse :
        - Code HTTP 204 No Content (succès)
        - Code HTTP 403 Forbidden (pas autorisé)
        - Code HTTP 404 Not Found (projet inexistant)
        
        ## 💡 Conseil :
        Avant de supprimer, assurez-vous d'avoir exporté les données importantes !
        """,
        tags=["📁 Studio - Projets"]
    ),
)
class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les projets NoCode
    """
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, HasProjectAccess]

    def get_queryset(self):
        """
        Retourne les projets accessibles par l'utilisateur :
        - Projets créés par l'utilisateur (client individuel)
        - Projets des organisations dont l'utilisateur est membre
        """
        user = self.request.user
        
        # Projets personnels
        user_projects = Project.objects.filter(created_by=user)
        
        # Projets des organisations
        user_orgs = user.organization_memberships.filter(
            status='ACTIVE'
        ).values_list('organization_id', flat=True)
        org_projects = Project.objects.filter(organization_id__in=user_orgs)
        
        # Combinaison des deux
        return (user_projects | org_projects).distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publier le projet - déclenche la génération Runtime"""
        project = self.get_object()
        
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


@extend_schema_view(
    list=extend_schema(
        summary="📊 Lister toutes les tables (schémas de données)",
        description="""
        **Récupère la liste de toutes les tables (DataSchema) de vos projets accessibles.**
        
        ## 🎯 Qu'est-ce qu'un DataSchema (Table) ?
        Un DataSchema représente une **table de base de données** dans votre projet NoCode :
        - Équivalent à une table SQL
        - Contient des champs (FieldSchema)
        - Stocke les données de votre application
        
        ## 📊 Filtrage disponible :
        Paramètre `?project=<project_id>` : Filtrer les tables d'un projet spécifique
        
        ## 💡 Exemple :
        ```
        GET /api/v1/studio/schemas/
        GET /api/v1/studio/schemas/?project=uuid-du-projet
        ```
        
        ## 🔐 Permissions :
        - Uniquement les tables des projets accessibles
        """,
        tags=["📊 Studio - Tables (Schémas)"],
        parameters=[
            OpenApiParameter(
                name="project",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description="UUID du projet pour filtrer les tables",
                required=False
            )
        ]
    ),
    create=extend_schema(
        summary="➕ Créer une nouvelle table",
        description="""
        **Crée une nouvelle table (DataSchema) dans un projet.**
        
        ## 📝 Informations requises :
        ```json
        {
            "name": "clients",
            "display_name": "Clients",
            "project_id": "uuid-du-projet"
        }
        ```
        
        ## 🎯 Ce qui est créé :
        - Une table dans le schéma PostgreSQL du projet
        - Un modèle de données prêt à recevoir des champs
        - Une structure pour stocker vos données
        
        ## ⚙️ Prochaines étapes après création :
        1. Ajouter des champs (FieldSchema) à la table
        2. Créer des formulaires et vues pour manipuler les données
        3. Utiliser l'API Runtime pour CRUD sur les données
        
        ## 🔐 Permissions :
        - Créateur du projet : ✅ Autorisé
        - OWNER/ADMIN d'organisation : ✅ Autorisé
        - MEMBER d'organisation : ❌ Lecture seule
        
        ## 💡 Bonnes pratiques :
        - `name` : en minuscules, sans espaces (ex: "clients", "commandes")
        - `display_name` : nom lisible (ex: "Clients", "Commandes")
        """,
        tags=["📊 Studio - Tables (Schémas)"],
        examples=[
            OpenApiExample(
                "Table Clients",
                value={
                    "name": "clients",
                    "display_name": "Clients",
                    "project_id": "550e8400-e29b-41d4-a716-446655440000"
                },
                request_only=True
            )
        ]
    ),
    retrieve=extend_schema(
        summary="🔍 Récupérer les détails d'une table",
        description="""
        **Récupère les informations complètes d'une table spécifique.**
        
        ## 📊 Informations retournées :
        - ID et nom de la table
        - Projet parent
        - Liste des champs (fields)
        - Métadonnées (dates, etc.)
        """,
        tags=["📊 Studio - Tables (Schémas)"]
    ),
    update=extend_schema(
        summary="✏️ Modifier une table",
        description="""
        **Modifie les informations d'une table existante.**
        
        ## 📝 Champs modifiables :
        - `display_name` : Nom d'affichage de la table
        - `name` : ⚠️ Attention, peut casser des références existantes
        
        ## 🔐 Permissions : Identiques à la création
        """,
        tags=["📊 Studio - Tables (Schémas)"]
    ),
    partial_update=extend_schema(
        summary="✏️ Modifier partiellement une table",
        tags=["📊 Studio - Tables (Schémas)"]
    ),
    destroy=extend_schema(
        summary="🗑️ Supprimer une table",
        description="""
        **Supprime une table et TOUTES ses données.**
        
        ## ⚠️ ATTENTION - Action IRRÉVERSIBLE !
        - 🗑️ La table sera supprimée
        - 🗑️ Tous les champs seront supprimés
        - 🗑️ Toutes les données stockées seront perdues
        
        ## 🔐 Permissions : Identiques à la création
        """,
        tags=["📊 Studio - Tables (Schémas)"]
    ),
)
class DataSchemaViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les schémas de données (tables)
    """
    serializer_class = DataSchemaSerializer
    permission_classes = [IsAuthenticated, HasProjectAccess]

    def get_queryset(self):
        """Retourne les schémas des projets accessibles par l'utilisateur"""
        user = self.request.user
        
        # Récupérer les IDs des projets accessibles
        user_projects = Project.objects.filter(created_by=user)
        user_orgs = user.organization_memberships.filter(
            status='ACTIVE'
        ).values_list('organization_id', flat=True)
        org_projects = Project.objects.filter(organization_id__in=user_orgs)
        accessible_projects = (user_projects | org_projects).distinct()
        
        project_id = self.request.query_params.get('project')
        if project_id:
            return DataSchema.objects.filter(
                project_id=project_id, 
                project__in=accessible_projects
            )
        return DataSchema.objects.filter(project__in=accessible_projects)

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
        """Retourne les champs des schémas des projets accessibles"""
        user = self.request.user
        
        # Récupérer les IDs des projets accessibles
        user_projects = Project.objects.filter(created_by=user)
        user_orgs = user.organization_memberships.filter(
            status='ACTIVE'
        ).values_list('organization_id', flat=True)
        org_projects = Project.objects.filter(organization_id__in=user_orgs)
        accessible_projects = (user_projects | org_projects).distinct()
        
        schema_id = self.request.query_params.get('schema')
        if schema_id:
            return FieldSchema.objects.filter(
                schema_id=schema_id, 
                schema__project__in=accessible_projects
            )
        return FieldSchema.objects.filter(schema__project__in=accessible_projects)

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
            # Vérifier que l'utilisateur a accès au projet
            user = request.user
            user_projects = Project.objects.filter(created_by=user)
            user_orgs = user.organization_memberships.filter(
                status='ACTIVE'
            ).values_list('organization_id', flat=True)
            org_projects = Project.objects.filter(organization_id__in=user_orgs)
            accessible_projects = (user_projects | org_projects).distinct()
            
            project = accessible_projects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {'error': 'Projet non trouvé ou accès refusé'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Créer une page si aucune n'existe
        page, created = Page.objects.get_or_create(
            project=project,
            is_home=True,
            defaults={'name': "Page d'accueil"}
        )

        # Résoudre le composant (catalogue) via `Component.name`
        try:
            component_def = Component.objects.get(name=component_type)
        except Component.DoesNotExist:
            return Response({'error': f"Composant inconnu: {component_type}"}, status=status.HTTP_400_BAD_REQUEST)

        # Champs layout (optionnels)
        parent_id = request.data.get('parent')
        slot = request.data.get('slot', '')

        parent = None
        if parent_id:
            parent = ComponentInstance.objects.filter(id=parent_id, page=page).first()

        # Créer le composant instance
        instance = ComponentInstance.objects.create(
            page=page,
            component=component_def,
            parent=parent,
            slot=slot,
            position=position,
            config=config,
        )

        return Response({
            'component_id': str(instance.id),
            'page_id': str(page.id),
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
            # Vérifier que l'utilisateur a accès au projet du composant
            user = request.user
            user_projects = Project.objects.filter(created_by=user)
            user_orgs = user.organization_memberships.filter(
                status='ACTIVE'
            ).values_list('organization_id', flat=True)
            org_projects = Project.objects.filter(organization_id__in=user_orgs)
            accessible_projects = (user_projects | org_projects).distinct()
            
            component = ComponentInstance.objects.get(
                id=component_id,
                page__project__in=accessible_projects
            )
            component.position = position
            component.save(update_fields=['position'])
            
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
            # Vérifier que l'utilisateur a accès au projet du composant
            user = request.user
            user_projects = Project.objects.filter(created_by=user)
            user_orgs = user.organization_memberships.filter(
                status='ACTIVE'
            ).values_list('organization_id', flat=True)
            org_projects = Project.objects.filter(organization_id__in=user_orgs)
            accessible_projects = (user_projects | org_projects).distinct()
            
            component = ComponentInstance.objects.get(
                id=component_id,
                page__project__in=accessible_projects
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
            # Vérifier que l'utilisateur a accès au projet
            user = request.user
            user_projects = Project.objects.filter(created_by=user)
            user_orgs = user.organization_memberships.filter(
                status='ACTIVE'
            ).values_list('organization_id', flat=True)
            org_projects = Project.objects.filter(organization_id__in=user_orgs)
            accessible_projects = (user_projects | org_projects).distinct()
            
            project = accessible_projects.get(id=project_id)
            pages = Page.objects.filter(project=project)
            
            state = {
                'project': {
                    'id': str(project.id),
                    'name': project.name,
                    'status': project.status
                },
                'pages': []
            }

            for page in pages:
                components = ComponentInstance.objects.filter(page=page)
                page_data = {
                    'id': str(page.id),
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
        """Retourne les pages des projets accessibles"""
        user = self.request.user
        
        # Récupérer les IDs des projets accessibles
        user_projects = Project.objects.filter(created_by=user)
        user_orgs = user.organization_memberships.filter(
            status='ACTIVE'
        ).values_list('organization_id', flat=True)
        org_projects = Project.objects.filter(organization_id__in=user_orgs)
        accessible_projects = (user_projects | org_projects).distinct()
        
        return Page.objects.filter(project__in=accessible_projects)

    def perform_create(self, serializer):
        page = serializer.save()
        EventBus.publish(
            event_name='studio.page.created',
            event_data={'page_id': str(page.id), 'project_id': page.project_id, 'route': page.route, 'name': page.name},
            source_module='studio.views',
            user=self.request.user,
        )

    def perform_update(self, serializer):
        page = serializer.save()
        EventBus.publish(
            event_name='studio.page.updated',
            event_data={'page_id': str(page.id), 'project_id': page.project_id, 'route': page.route, 'name': page.name},
            source_module='studio.views',
            user=self.request.user,
        )

    def perform_destroy(self, instance):
        payload = {'page_id': str(instance.id), 'project_id': instance.project_id, 'route': instance.route, 'name': instance.name}
        instance.delete()
        EventBus.publish(
            event_name='studio.page.deleted',
            event_data=payload,
            source_module='studio.views',
            user=self.request.user,
        )

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
        """Retourne les composants des projets accessibles"""
        user = self.request.user
        
        # Récupérer les IDs des projets accessibles
        user_projects = Project.objects.filter(created_by=user)
        user_orgs = user.organization_memberships.filter(
            status='ACTIVE'
        ).values_list('organization_id', flat=True)
        org_projects = Project.objects.filter(organization_id__in=user_orgs)
        accessible_projects = (user_projects | org_projects).distinct()
        
        return ComponentInstance.objects.filter(page__project__in=accessible_projects)

    def perform_create(self, serializer):
        # Le signal auto_create_page_if_needed se déclenchera ici
        component = serializer.save()
        EventBus.publish(
            event_name='studio.component_instance.created',
            event_data={'component_instance_id': str(component.id), 'page_id': component.page_id, 'component_name': component.component.name},
            source_module='studio.views',
            user=self.request.user,
        )

    def perform_update(self, serializer):
        component = serializer.save()
        EventBus.publish(
            event_name='studio.component_instance.updated',
            event_data={'component_instance_id': str(component.id), 'page_id': component.page_id, 'component_name': component.component.name},
            source_module='studio.views',
            user=self.request.user,
        )

    def perform_destroy(self, instance):
        payload = {'component_instance_id': str(instance.id), 'page_id': instance.page_id, 'component_name': instance.component.name}
        instance.delete()
        EventBus.publish(
            event_name='studio.component_instance.deleted',
            event_data=payload,
            source_module='studio.views',
            user=self.request.user,
        )
