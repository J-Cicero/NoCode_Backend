"""
Vues pour le module Runtime.

Ce module expose les API REST pour gérer les applications générées et leurs déploiements.
"""
import logging
import json
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction, connection
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample,
    OpenApiResponse, OpenApiTypes
)

from .models import GeneratedApp, DeploymentLog
from .serializers import (
    GeneratedAppSerializer,
    DeploymentLogSerializer,
    DeploymentActionSerializer,
    AppStatusSerializer,
    AppLogsSerializer
)
from .services import AppGenerator, DeploymentManager, KubernetesDeployment, LocalDeployment
from .builders.serializer_builder import SerializerBuilder
from .builders.viewset_builder import ViewSetBuilder
from apps.foundation.models import OrganizationMember
from apps.studio.models import Project, DataSchema

logger = logging.getLogger(__name__)

@extend_schema_view(
    list=extend_schema(
        summary="Lister les applications générées",
        description="Retourne la liste des applications générées par l'utilisateur courant.",
        responses={
            200: GeneratedAppSerializer(many=True),
            403: OpenApiResponse(description="Accès non autorisé")
        }
    ),
    create=extend_schema(
        summary="Créer une nouvelle application",
        description="Crée une nouvelle application générée.",
        responses={
            201: GeneratedAppSerializer,
            400: OpenApiResponse(description="Données invalides"),
            403: OpenApiResponse(description="Accès non autorisé")
        }
    ),
    retrieve=extend_schema(
        summary="Récupérer une application",
        description="Récupère les détails d'une application générée.",
        responses={
            200: GeneratedAppSerializer,
            404: OpenApiResponse(description="Application non trouvée")
        }
    ),
    update=extend_schema(
        summary="Mettre à jour une application",
        description="Met à jour les informations d'une application générée.",
        responses={
            200: GeneratedAppSerializer,
            400: OpenApiResponse(description="Données invalides"),
            403: OpenApiResponse(description="Accès non autorisé"),
            404: OpenApiResponse(description="Application non trouvée")
        }
    ),
    destroy=extend_schema(
        summary="Supprimer une application",
        description="Supprime une application générée.",
        responses={
            204: None,
            403: OpenApiResponse(description="Accès non autorisé"),
            404: OpenApiResponse(description="Application non trouvée")
        }
    )
)
class GeneratedAppViewSet(viewsets.ModelViewSet):
    """
    API endpoint qui permet de gérer les applications générées.
    """
    queryset = GeneratedApp.objects.all()
    serializer_class = GeneratedAppSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtre les applications par utilisateur et organisations où il est membre."""
        user = self.request.user
        queryset = super().get_queryset()

        if user.is_superuser:
            return queryset

        # Apps de projets perso créés par l’utilisateur
        personal_qs = queryset.filter(project__organization__isnull=True, project__created_by=user)

        # Apps de projets des organisations où l’utilisateur est membre
        org_ids = OrganizationMember.objects.filter(
            user=user,
            status='ACTIVE'
        ).values_list('organization_id', flat=True)

        org_qs = queryset.filter(project__organization_id__in=org_ids)

        return personal_qs.union(org_qs)
    
    def perform_create(self, serializer):
        """Crée une nouvelle application générée."
        
        Args:
            serializer: Le sérialiseur contenant les données de l'application
        """
        with transaction.atomic():
            instance = serializer.save()
            
            # Génération du code de l'application
            try:
                generator = AppGenerator(instance.project)
                generator.generate()
                instance.status = 'generated'
                instance.save(update_fields=['status', 'updated_at'])
            except Exception as e:
                logger.error(f"Erreur lors de la génération de l'application: {str(e)}")
                instance.status = 'error'
                instance.save(update_fields=['status', 'updated_at'])
    
    @extend_schema(
        methods=['post'],
        summary="Déployer une application",
        description="Lance le déploiement d'une application générée sur l'environnement cible.",
        request=DeploymentActionSerializer,
        responses={
            202: OpenApiResponse(
                description="Déploiement démarré avec succès",
                examples={
                    "application/json": {
                        "status": "déploiement démarré",
                        "deployment_id": "550e8400-e29b-41d4-a716-446655440000",
                        "app_status": "deployment_pending"
                    }
                }
            ),
            400: OpenApiResponse(description="L'application n'est pas dans un état déployable"),
            403: OpenApiResponse(description="Accès non autorisé"),
            404: OpenApiResponse(description="Application non trouvée"),
            500: OpenApiResponse(description="Erreur lors du démarrage du déploiement")
        }
    )
    @extend_schema(
        methods=['post'],
        summary="Déployer une application",
        description="Lance le déploiement d'une application générée sur l'environnement cible.",
        request=DeploymentActionSerializer,
        responses={
            202: OpenApiResponse(
                description="Déploiement démarré avec succès",
                examples={
                    "application/json": {
                        "status": "déploiement démarré",
                        "deployment_id": "550e8400-e29b-41d4-a716-446655440000",
                        "app_status": "deployment_pending"
                    }
                }
            ),
            400: OpenApiResponse(description="L'application n'est pas dans un état déployable"),
            403: OpenApiResponse(description="Accès non autorisé"),
            404: OpenApiResponse(description="Application non trouvée"),
            500: OpenApiResponse(description="Erreur lors du démarrage du déploiement")
        }
    )
    @action(detail=True, methods=['post'])
    def deploy(self, request, pk=None):
        """Déploie l'application sur la cible de déploiement configurée.
        
        Args:
            request: La requête HTTP
            pk: L'identifiant de l'application à déployer
            
        Returns:
            Response: Réponse JSON avec le statut du déploiement
        """
        app = self.get_object()
        user = request.user

        # Vérifier les permissions
        if not user.is_superuser:
            if app.project.organization is None:
                if app.project.created_by_id != user.id:
                    return Response(
                        {"detail": "Vous n'avez pas la permission de déployer cette application."},
                        status=status.HTTP_403_FORBIDDEN
                    )
            else:
                org_ids = OrganizationMember.objects.filter(
                    user=user,
                    status='ACTIVE'
                ).values_list('organization_id', flat=True)
                if app.project.organization_id not in org_ids:
                    return Response(
                        {"detail": "Vous n'avez pas la permission de déployer cette application."},
                        status=status.HTTP_403_FORBIDDEN
                    )
        
        # Vérifier que l'application est dans un état déployable
        if app.status not in ['generated', 'deployment_failed']:
            return Response(
                {"error": "L'application doit être générée avant d'être déployée"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Créer une entrée de journal pour le déploiement
            deployment_log = DeploymentLog.objects.create(
                app=app,
                status='pending',
                performed_by=request.user
            )
            
            # Mettre à jour le statut de l'application
            app.status = 'deployment_pending'
            app.save(update_fields=['status', 'updated_at'])
            
            # Démarrer le déploiement de manière asynchrone
            from .tasks import deploy_app_task
            deploy_app_task.delay(deployment_log.id)
            
            return Response(
                {
                    "status": "déploiement démarré", 
                    "deployment_id": str(deployment_log.id),
                    "app_status": app.status
                },
                status=status.HTTP_202_ACCEPTED
            )
            
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du déploiement: {str(e)}", 
                       exc_info=True)
            return Response(
                {
                    "error": "Erreur lors du démarrage du déploiement", 
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        methods=['get'],
        summary="Obtenir le statut d'une application",
        description="Récupère les informations de statut d'une application générée, y compris son état de déploiement.",
        responses={
            200: OpenApiResponse(
                description="Statut de l'application récupéré avec succès",
                examples={
                    "application/json": {
                        "app_id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "Mon Application",
                        "status": "deployed",
                        "deployment_status": {"status": "success", "version": "1.0.0"},
                        "last_deployed": "2023-10-21T12:00:00Z",
                        "last_deployment_status": "success",
                        "api_url": "https://api.example.com/v1",
                        "admin_url": "https://admin.example.com",
                        "created_at": "2023-10-20T10:00:00Z",
                        "updated_at": "2023-10-21T12:00:00Z"
                    }
                }
            ),
            403: OpenApiResponse(description="Accès non autorisé"),
            404: OpenApiResponse(description="Application non trouvée"),
            500: OpenApiResponse(description="Erreur lors de la récupération du statut")
        }
    )
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Récupère le statut de déploiement de l'application.
        
        Args:
            request: La requête HTTP
            pk: L'identifiant de l'application
            
        Returns:
            Response: Les informations de statut de l'application
        """
        app = self.get_object()
        user = request.user

        # Vérifier les permissions
        if not user.is_superuser:
            if app.project.organization is None:
                if app.project.created_by_id != user.id:
                    return Response(
                        {"detail": "Accès non autorisé."},
                        status=status.HTTP_403_FORBIDDEN
                    )
            else:
                org_ids = OrganizationMember.objects.filter(
                    user=user,
                    status='ACTIVE'
                ).values_list('organization_id', flat=True)
                if app.project.organization_id not in org_ids:
                    return Response(
                        {"detail": "Accès non autorisé."},
                        status=status.HTTP_403_FORBIDDEN
                    )
        
        try:
            manager = DeploymentManager(app)
            status_info = manager.get_status()
            
            # Récupérer le dernier log de déploiement
            last_deployment = app.deployments.order_by('-created_at').first()
            
            return Response({
                "app_id": str(app.id),
                "name": app.name,
                "status": app.status,
                "deployment_status": status_info,
                "last_deployed": last_deployment.created_at if last_deployment else None,
                "last_deployment_status": last_deployment.status if last_deployment else None,
                "api_url": app.api_base_url,
                "admin_url": app.admin_url,
                "created_at": app.created_at,
                "updated_at": app.updated_at
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut: {str(e)}", 
                       exc_info=True)
            return Response(
                {"error": "Erreur lors de la récupération du statut", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        methods=['get'],
        summary="Obtenir les journaux d'une application",
        description="Récupère l'historique des journaux de déploiement pour une application spécifique.",
        responses={
            200: OpenApiResponse(
                description="Journaux récupérés avec succès",
                examples={
                    "application/json": {
                        "app_id": "550e8400-e29b-41d4-a716-446655440000",
                        "app_name": "Mon Application",
                        "total_logs": 3,
                        "logs": [
                            {
                                "id": 1,
                                "status": "success",
                                "created_at": "2023-10-21T12:00:00Z",
                                "completed_at": "2023-10-21T12:05:00Z"
                            },
                            {
                                "id": 2,
                                "status": "failed",
                                "error_message": "Erreur de connexion au serveur",
                                "created_at": "2023-10-21T11:30:00Z",
                                "completed_at": "2023-10-21T11:35:00Z"
                            }
                        ]
                    }
                }
            ),
            403: OpenApiResponse(description="Accès non autorisé"),
            404: OpenApiResponse(description="Application non trouvée"),
            500: OpenApiResponse(description="Erreur lors de la récupération des journaux")
        }
    )
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Récupère les logs de déploiement de l'application.
        
        Args:
            request: La requête HTTP
            pk: L'identifiant de l'application
            
        Returns:
            Response: Les logs de déploiement de l'application
        """
        app = self.get_object()
        
        # Vérifier les permissions
        if not request.user.is_superuser and app.project.organization != request.user.organization:
            return Response(
                {"detail": "Accès non autorisé."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Récupérer les logs depuis la base de données
            logs = DeploymentLog.objects.filter(app=app).order_by('-created_at')
            
            # Sérialiser les logs
            log_serializer = DeploymentLogSerializer(logs, many=True)
            
            return Response({
                "app_id": str(app.id),
                "app_name": app.name,
                "total_logs": logs.count(),
                "logs": log_serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des logs: {str(e)}", 
                       exc_info=True)
            return Response(
                {"error": "Erreur lors de la récupération des logs", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@extend_schema_view(
    list=extend_schema(
        summary="Lister les journaux de déploiement",
        description="Retourne la liste des journaux de déploiement pour les applications de l'utilisateur.",
        parameters=[
            OpenApiParameter(
                name='app_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description="Filtrer par ID d'application",
                required=False
            ),
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filtrer par statut (ex: 'success', 'failed', 'pending')",
                required=False,
                enum=['success', 'failed', 'pending', 'in_progress']
            )
        ],
        responses={
            200: DeploymentLogSerializer(many=True),
            400: OpenApiResponse(description="Paramètres de requête invalides"),
            403: OpenApiResponse(description="Accès non autorisé")
        }
    ),
    retrieve=extend_schema(
        summary="Récupérer un journal de déploiement",
        description="Récupère les détails d'un journal de déploiement spécifique par son ID.",
        responses={
            200: DeploymentLogSerializer,
            403: OpenApiResponse(description="Accès non autorisé"),
            404: OpenApiResponse(description="Journal de déploiement non trouvé")
        }
    )
)
class DeploymentLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint qui permet de consulter les journaux de déploiement.
    
    Ce ViewSet fournit les opérations CRUD de base pour les journaux de déploiement,
    avec des filtres par application et organisation.
    """
    serializer_class = DeploymentLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtre les journaux de déploiement par utilisateur et organisation.
        
        Returns:
            QuerySet: Les journaux de déploiement filtrés
        """
        queryset = DeploymentLog.objects.select_related(
            'app', 
            'app__project', 
            'performed_by'
        ).order_by('-created_at')
        
        # Filtrage par application si spécifié
        app_id = self.request.query_params.get('app_id')
        if app_id:
            queryset = queryset.filter(app_id=app_id)
        
        # Filtrage par statut si spécifié
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        user = self.request.user

        if user.is_superuser:
            return queryset

        # Journaux des apps de projets perso créés par l’utilisateur
        personal_qs = queryset.filter(app__project__organization__isnull=True, app__project__created_by=user)

        # Journaux des apps des organisations où l’utilisateur est membre
        org_ids = OrganizationMember.objects.filter(
            user=user,
            status='ACTIVE'
        ).values_list('organization_id', flat=True)

        org_qs = queryset.filter(app__project__organization_id__in=org_ids)

        return personal_qs.union(org_qs)
        
    @extend_schema(
        methods=['post'],
        summary="Relancer un déploiement échoué",
        description="Relance un déploiement qui a échoué précédemment en créant une nouvelle entrée de journal.",
        responses={
            202: OpenApiResponse(
                description="Relance du déploiement démarrée avec succès",
                examples={
                    "application/json": {
                        "status": "déploiement relancé",
                        "new_deployment_id": "660e8400-e29b-41d4-a716-446655440001",
                        "original_deployment_id": "550e8400-e29b-41d4-a716-446655440000"
                    }
                }
            ),
            400: OpenApiResponse(description="Le déploiement ne peut pas être relancé"),
            403: OpenApiResponse(description="Accès non autorisé"),
            404: OpenApiResponse(description="Journal de déploiement non trouvé"),
            500: OpenApiResponse(description="Erreur lors de la relance du déploiement")
        }
    )
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Relance un déploiement échoué.
        
        Args:
            request: La requête HTTP
            pk: L'identifiant du journal de déploiement à relancer
            
        Returns:
            Response: Les informations du nouveau déploiement
        """
        deployment_log = self.get_object()
        
        # Vérifier les permissions
        if not request.user.is_superuser and deployment_log.app.project.organization != request.user.organization:
            return Response(
                {"detail": "Accès non autorisé."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Vérifier que le déploiement est en échec
        if deployment_log.status != 'failed':
            return Response(
                {"error": "Seuls les déploiements en échec peuvent être relancés"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            with transaction.atomic():
                # Créer un nouveau log de déploiement
                new_deployment = DeploymentLog.objects.create(
                    app=deployment_log.app,
                    status='pending',
                    performed_by=request.user,
                    previous_deployment=deployment_log,
                    environment=deployment_log.environment,
                    version=deployment_log.version
                )
                
                # Mettre à jour le statut de l'application
                deployment_log.app.status = 'deployment_pending'
                deployment_log.app.save(update_fields=['status', 'updated_at'])
                
                # Démarrer le déploiement de manière asynchrone
                deploy_app_task.delay(new_deployment.id)
                
                serializer = self.get_serializer(new_deployment)
                return Response(
                    {
                        "status": "redémarrage du déploiement",
                        "deployment": serializer.data
                    },
                    status=status.HTTP_202_ACCEPTED
                )
            
        except Exception as e:
            logger.error(f"Erreur lors de la relance du déploiement: {str(e)}", 
                       exc_info=True)
            return Response(
                {
                    "error": "Erreur lors de la relance du déploiement",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================
# VUES API DYNAMIQUES NOCODE
# ============================================

class DynamicProjectAPIView:
    """
    Vue de base pour les APIs dynamiques de projet.
    Gère l'accès aux tables d'un projet spécifique.
    """
    
    def __init__(self):
        self.permission_classes = [IsAuthenticated]
    
    def get_project(self, project_id):
        """Récupère un projet avec vérification des permissions."""
        project = get_object_or_404(Project, tracking_id=project_id)
        
        # Vérifier les permissions
        user = self.request.user
        if project.created_by != user:
            # Vérifier si l'utilisateur est membre de l'organisation
            if project.organization:
                is_member = OrganizationMember.objects.filter(
                    user=user,
                    organization=project.organization,
                    status='ACTIVE'
                ).exists()
                if not is_member:
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied("Vous n'avez pas accès à ce projet")
            else:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Vous n'avez pas accès à ce projet")
        
        return project


class DynamicTableViewSet(viewsets.ViewSet):
    """
    ViewSet dynamique pour les tables d'un projet.
    Fournit le CRUD automatique pour n'importe quelle table utilisateur.
    """
    permission_classes = [IsAuthenticated]  # Réactivé pour la sécurité
    
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.serializer_builder = None
        self.project = None
        self.data_schema = None
        self.table_name = None
    
    def get_project(self, project_id):
        """Récupère un projet avec vérification des permissions."""
        project = get_object_or_404(Project, tracking_id=project_id)
        
        # Vérifier les permissions
        user = getattr(self.request, 'user', None)
        if user and project.created_by != user:
            # Vérifier si l'utilisateur est membre de l'organisation
            if project.organization:
                is_member = OrganizationMember.objects.filter(
                    user=user,
                    organization=project.organization,
                    status='ACTIVE'
                ).exists()
                if not is_member:
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied("Vous n'avez pas accès à ce projet")
            else:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Vous n'avez pas accès à ce projet")
        
        return project
    
    def initialize(self, project_id, table_name):
        """Initialise les builders pour le projet et la table spécifiés."""
        self.project = self.get_project(project_id)
        self.data_schema = get_object_or_404(DataSchema, project=self.project, table_name=table_name)
        self.table_name = f"project_{self.project.id}_{table_name}"
        
        # Initialiser le serializer builder
        self.serializer_builder = SerializerBuilder(self.project)
    
    def list(self, request, project_id, table_name):
        """Liste les enregistrements de la table."""
        try:
            self.initialize(project_id, table_name)
            
            # Récupérer les données depuis la table SQL
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {self.table_name} ORDER BY created_at DESC")
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
                # Convertir en liste de dictionnaires
                data = []
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    # Convertir les valeurs JSON si nécessaire
                    for key, value in row_dict.items():
                        if isinstance(value, str):
                            try:
                                row_dict[key] = json.loads(value)
                            except (json.JSONDecodeError, TypeError):
                                pass
                    data.append(row_dict)
            
            # Pagination
            page_size = int(request.GET.get('page_size', 20))
            page_number = int(request.GET.get('page', 1))
            
            from django.core.paginator import Paginator
            paginator = Paginator(data, page_size)
            page_obj = paginator.get_page(page_number)
            
            # Sérialiser avec le serializer dynamique
            serializer_class = self.serializer_builder.create_serializer_class(self.data_schema)
            serializer = serializer_class(page_obj.object_list, many=True)
            
            return Response({
                'count': paginator.count,
                'next': page_obj.has_next() and f"?page={page_number + 1}&page_size={page_size}" or None,
                'previous': page_obj.has_previous() and f"?page={page_number - 1}&page_size={page_size}" or None,
                'results': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la liste {table_name}: {e}")
            return Response(
                {'error': 'Erreur lors de la récupération des données'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request, project_id, table_name):
        """Crée un nouvel enregistrement."""
        try:
            self.initialize(project_id, table_name)
            
            # Valider avec le serializer dynamique
            serializer_class = self.serializer_builder.create_serializer_class(self.data_schema)
            serializer = serializer_class(data=request.data)
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            
            # Construire la requête INSERT
            columns = list(validated_data.keys())
            placeholders = ['%s'] * len(columns)
            values = list(validated_data.values())
            
            # Convertir les valeurs en JSON si nécessaire
            for i, value in enumerate(values):
                if isinstance(value, (dict, list)):
                    values[i] = json.dumps(value)
            
            query = f"""
                INSERT INTO {self.table_name} ({', '.join(columns)}) 
                VALUES ({', '.join(placeholders)}) 
                RETURNING id, created_at, updated_at
            """
            
            with connection.cursor() as cursor:
                cursor.execute(query, values)
                result = cursor.fetchone()
                
                # Récupérer l'objet créé
                cursor.execute(f"SELECT * FROM {self.table_name} WHERE id = %s", [result[0]])
                columns = [col[0] for col in cursor.description]
                row = cursor.fetchone()
                
                created_obj = dict(zip(columns, row))
                # Convertir les valeurs JSON si nécessaire
                for key, value in created_obj.items():
                    if isinstance(value, str):
                        try:
                            created_obj[key] = json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            pass
            
            # Sérialiser la réponse
            serializer = serializer_class(created_obj)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Erreur lors de la création {table_name}: {e}")
            return Response(
                {'error': 'Erreur lors de la création de l\'enregistrement'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, project_id, table_name, pk):
        """Récupère un enregistrement spécifique."""
        try:
            self.initialize(project_id, table_name)
            
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {self.table_name} WHERE id = %s", [pk])
                columns = [col[0] for col in cursor.description]
                row = cursor.fetchone()
                
                if not row:
                    return Response({'error': 'Objet non trouvé'}, status=status.HTTP_404_NOT_FOUND)
                
                obj_dict = dict(zip(columns, row))
                # Convertir les valeurs JSON si nécessaire
                for key, value in obj_dict.items():
                    if isinstance(value, str):
                        try:
                            obj_dict[key] = json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            pass
            
            # Sérialiser la réponse
            serializer_class = self.serializer_builder.create_serializer_class(self.data_schema)
            serializer = serializer_class(obj_dict)
            return Response(serializer.data)
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération {table_name}/{pk}: {e}")
            return Response(
                {'error': 'Erreur lors de la récupération de l\'enregistrement'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, project_id, table_name, pk):
        """Met à jour un enregistrement."""
        try:
            self.initialize(project_id, table_name)
            
            # Récupérer l'objet existant
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {self.table_name} WHERE id = %s", [pk])
                columns = [col[0] for col in cursor.description]
                row = cursor.fetchone()
                
                if not row:
                    return Response({'error': 'Objet non trouvé'}, status=status.HTTP_404_NOT_FOUND)
                
                obj_dict = dict(zip(columns, row))
            
            # Valider avec le serializer dynamique
            serializer_class = self.serializer_builder.create_serializer_class(self.data_schema)
            serializer = serializer_class(obj_dict, data=request.data, partial=True)
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            
            if not validated_data:
                # Sérialiser et retourner l'objet inchangé
                serializer = serializer_class(obj_dict)
                return Response(serializer.data)
            
            # Construire la requête UPDATE
            set_clauses = []
            values = []
            
            for column, value in validated_data.items():
                set_clauses.append(f"{column} = %s")
                # Convertir les valeurs en JSON si nécessaire
                if isinstance(value, (dict, list)):
                    values.append(json.dumps(value))
                else:
                    values.append(value)
            
            values.append(pk)  # Pour la clause WHERE
            
            query = f"""
                UPDATE {self.table_name} 
                SET {', '.join(set_clauses)}, updated_at = NOW() 
                WHERE id = %s
            """
            
            with connection.cursor() as cursor:
                cursor.execute(query, values)
            
            # Récupérer l'objet mis à jour
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {self.table_name} WHERE id = %s", [pk])
                columns = [col[0] for col in cursor.description]
                row = cursor.fetchone()
                
                updated_obj = dict(zip(columns, row))
                # Convertir les valeurs JSON si nécessaire
                for key, value in updated_obj.items():
                    if isinstance(value, str):
                        try:
                            updated_obj[key] = json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            pass
            
            # Sérialiser la réponse
            serializer = serializer_class(updated_obj)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour {table_name}/{pk}: {e}")
            return Response(
                {'error': 'Erreur lors de la mise à jour de l\'enregistrement'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def partial_update(self, request, project_id, table_name, pk):
        """Mise à jour partielle d'un enregistrement."""
        return self.update(request, project_id, table_name, pk)
    
    def destroy(self, request, project_id, table_name, pk):
        """Supprime un enregistrement."""
        try:
            self.initialize(project_id, table_name)
            
            with connection.cursor() as cursor:
                cursor.execute(f"DELETE FROM {self.table_name} WHERE id = %s", [pk])
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression {table_name}/{pk}: {e}")
            return Response(
                {'error': 'Erreur lors de la suppression de l\'enregistrement'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def schema(self, request, project_id, table_name):
        """Retourne les métadonnées du schéma pour le frontend."""
        try:
            self.initialize(project_id, table_name)
            metadata = self.serializer_builder.create_metadata_serializer(self.data_schema)
            return Response(metadata)
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du schéma {table_name}: {e}")
            return Response(
                {'error': 'Erreur lors de la récupération du schéma'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def fields(self, request, project_id, table_name):
        """Retourne la définition des champs pour les formulaires."""
        try:
            self.initialize(project_id, table_name)
            metadata = self.serializer_builder.create_metadata_serializer(self.data_schema)
            return Response(metadata['fields'])
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des champs {table_name}: {e}")
            return Response(
                {'error': 'Erreur lors de la récupération des champs'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProjectSchemaViewSet(DynamicProjectAPIView, viewsets.ViewSet):
    """
    ViewSet pour gérer les schémas d'un projet.
    Retourne toutes les tables et leurs métadonnées.
    """
    
    def list(self, request, project_id):
        """Liste toutes les tables du projet avec leurs métadonnées."""
        try:
            project = self.get_project(project_id)
            serializer_builder = SerializerBuilder(project)
            metadata = serializer_builder.get_all_metadata()
            
            return Response({
                'project': {
                    'id': str(project.tracking_id),
                    'name': project.name,
                    'schema_name': project.schema_name,
                },
                'tables': metadata
            })
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des schémas du projet {project_id}: {e}")
            return Response(
                {'error': 'Erreur lors de la récupération des schémas'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, project_id, pk):
        """Récupère les métadonnées d'une table spécifique."""
        try:
            project = self.get_project(project_id)
            data_schema = get_object_or_404(DataSchema, project=project, table_name=pk)
            
            serializer_builder = SerializerBuilder(project)
            metadata = serializer_builder.create_metadata_serializer(data_schema)
            
            return Response(metadata)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du schéma {pk}: {e}")
            return Response(
                {'error': 'Erreur lors de la récupération du schéma'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
