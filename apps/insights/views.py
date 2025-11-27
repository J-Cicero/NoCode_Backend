"""
Vues pour le module Insights.

Expose les APIs REST pour :
- Tracking d'événements et activités utilisateur
- Consultation des métriques système et applicatives
- Rapports d'analytics et performance
"""
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .permissions import CanViewAnalytics, CanManageMetrics, CanAccessReports, CanExportData
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiParameter,
    OpenApiResponse, OpenApiExample
)

from .models import (
    UserActivity, SystemMetric, ApplicationMetric,
    UserMetric, PerformanceMetric
)
from .serializers import (
    UserActivitySerializer, UserActivityCreateSerializer,
    SystemMetricSerializer, ApplicationMetricSerializer,
    UserMetricSerializer, PerformanceMetricSerializer,
    EventTrackingSerializer, AnalyticsReportSerializer,
    PerformanceReportSerializer
)
from .services import MetricsCollector, AnalyticsService

logger = logging.getLogger(__name__)

class StandardPagination(PageNumberPagination):
    """Pagination standard pour les vues."""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

@extend_schema_view(
    list=extend_schema(
        summary="Liste des activités utilisateur",
        description="Retourne la liste des activités utilisateur pour l'organisation courante.",
        responses={
            200: UserActivitySerializer(many=True),
            403: OpenApiResponse(description="Accès non autorisé")
        }
    ),
    retrieve=extend_schema(
        summary="Détails d'une activité",
        description="Retourne les détails d'une activité utilisateur spécifique.",
        responses={
            200: UserActivitySerializer,
            404: OpenApiResponse(description="Activité non trouvée")
        }
    )
)
class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour consulter les activités utilisateur.

    Permet de tracer et analyser toutes les actions effectuées
    par les utilisateurs sur la plateforme.
    """
    serializer_class = UserActivitySerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated, CanViewAnalytics]

    def get_queryset(self):
        """Filtre les activités par organisation de l'utilisateur."""
        queryset = UserActivity.objects.select_related('user', 'organization')
        user = self.request.user

        # Staff voit tout
        if user.is_staff or user.is_superuser:
            return queryset

        # Récupérer les organisations dont l'utilisateur est membre
        from apps.foundation.permissions import get_user_organizations
        org_ids = get_user_organizations(user)
        
        if org_ids:
            # Activités de ses organisations + ses propres activités
            queryset = queryset.filter(
                Q(organization_id__in=org_ids) | Q(user=user)
            )
        else:
            # Seulement ses propres activités
            queryset = queryset.filter(user=user)

        return queryset

    def get_serializer_context(self):
        """Ajoute le contexte de requête aux sérialiseurs."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @extend_schema(
        summary="Filtrer les activités",
        description="Filtre les activités par type, utilisateur, date, etc.",
        parameters=[
            OpenApiParameter(
                name='activity_type',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Type d\'activité à filtrer'
            ),
            OpenApiParameter(
                name='user_id',
                type=str,
                location=OpenApiParameter.QUERY,
                description='ID utilisateur à filtrer'
            ),
            OpenApiParameter(
                name='start_date',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Date de début (YYYY-MM-DD)'
            ),
            OpenApiParameter(
                name='end_date',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Date de fin (YYYY-MM-DD)'
            ),
        ],
        responses={
            200: UserActivitySerializer(many=True),
        }
    )
    @action(detail=False, methods=['get'])
    def filter(self, request):
        """Filtre les activités selon les paramètres."""
        queryset = self.get_queryset()

        # Filtre par type d'activité
        activity_type = request.query_params.get('activity_type')
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)

        # Filtre par utilisateur
        user_id = request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Filtre par dates
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                queryset = queryset.filter(created_at__gte=start_date)
            except ValueError:
                pass

        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                queryset = queryset.filter(created_at__lte=end_date)
            except ValueError:
                pass

        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

@extend_schema_view(
    list=extend_schema(
        summary="Liste des métriques système",
        description="Retourne les métriques système collectées.",
        responses={
            200: SystemMetricSerializer(many=True),
        }
    ),
    retrieve=extend_schema(
        summary="Détails d'une métrique système",
        description="Retourne les détails d'une métrique système spécifique.",
        responses={
            200: SystemMetricSerializer,
            404: OpenApiResponse(description="Métrique non trouvée")
        }
    )
)
class SystemMetricViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint pour consulter les métriques système."""
    queryset = SystemMetric.objects.all()
    serializer_class = SystemMetricSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated, CanViewAnalytics]

@extend_schema_view(
    list=extend_schema(
        summary="Liste des métriques d'application",
        description="Retourne les métriques des applications générées.",
        responses={
            200: ApplicationMetricSerializer(many=True),
        }
    ),
    retrieve=extend_schema(
        summary="Détails d'une métrique d'application",
        description="Retourne les détails d'une métrique d'application spécifique.",
        responses={
            200: ApplicationMetricSerializer,
            404: OpenApiResponse(description="Métrique non trouvée")
        }
    )
)
class ApplicationMetricViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint pour consulter les métriques d'application."""
    queryset = ApplicationMetric.objects.select_related('app')
    serializer_class = ApplicationMetricSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated, CanViewAnalytics]

    def get_queryset(self):
        """Filtre par organisation si nécessaire."""
        queryset = super().get_queryset()
        user = self.request.user

        # Staff voit tout
        if user.is_staff or user.is_superuser:
            return queryset

        # Récupérer les organisations dont l'utilisateur est membre
        from apps.foundation.permissions import get_user_organizations
        org_ids = get_user_organizations(user)
        
        # Filtrer par projets des organisations + projets perso
        queryset = queryset.filter(
            Q(app__project__organization_id__in=org_ids) | 
            Q(app__project__organization__isnull=True, app__project__created_by=user)
        )

        return queryset

@extend_schema_view(
    list=extend_schema(
        summary="Liste des métriques utilisateur",
        description="Retourne les métriques d'utilisation par utilisateur.",
        responses={
            200: UserMetricSerializer(many=True),
        }
    ),
    retrieve=extend_schema(
        summary="Détails d'une métrique utilisateur",
        description="Retourne les détails d'une métrique utilisateur spécifique.",
        responses={
            200: UserMetricSerializer,
            404: OpenApiResponse(description="Métrique non trouvée")
        }
    )
)
class UserMetricViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint pour consulter les métriques utilisateur."""
    queryset = UserMetric.objects.select_related('user', 'organization')
    serializer_class = UserMetricSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated, CanViewAnalytics]

    def get_queryset(self):
        """Filtre par organisation de l'utilisateur."""
        queryset = super().get_queryset()
        user = self.request.user

        # Staff voit tout
        if user.is_staff or user.is_superuser:
            return queryset

        # Récupérer les organisations dont l'utilisateur est membre
        from apps.foundation.permissions import get_user_organizations
        org_ids = get_user_organizations(user)
        
        # Métriques de ses organisations + ses propres métriques
        queryset = queryset.filter(
            Q(organization_id__in=org_ids) | Q(user=user)
        )

        return queryset

@extend_schema_view(
    list=extend_schema(
        summary="Liste des métriques de performance",
        description="Retourne les métriques de performance détaillées.",
        responses={
            200: PerformanceMetricSerializer(many=True),
        }
    ),
    retrieve=extend_schema(
        summary="Détails d'une métrique de performance",
        description="Retourne les détails d'une métrique de performance spécifique.",
        responses={
            200: PerformanceMetricSerializer,
            404: OpenApiResponse(description="Métrique non trouvée")
        }
    )
)
class PerformanceMetricViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint pour consulter les métriques de performance."""
    queryset = PerformanceMetric.objects.select_related('organization', 'user')
    serializer_class = PerformanceMetricSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated, CanViewAnalytics]

@extend_schema(
    summary="Tracker un événement personnalisé",
    description="Permet d'envoyer un événement personnalisé pour le tracking.",
    request=EventTrackingSerializer,
    responses={
        201: OpenApiResponse(
            description="Événement tracké avec succès",
            examples={
                "application/json": {
                    "status": "tracked",
                    "event_id": "550e8400-e29b-41d4-a716-446655440000",
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            }
        ),
        400: OpenApiResponse(description="Données invalides"),
        403: OpenApiResponse(description="Accès non autorisé")
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_event(request):
    """
    API endpoint pour tracker des événements personnalisés.

    Permet aux clients d'envoyer des événements de tracking
    pour analyse et monitoring.
    """
    serializer = EventTrackingSerializer(data=request.data, context={'request': request})

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    try:
        # Récupérer la première organisation active de l'utilisateur
        from apps.foundation.models import OrganizationMember
        
        membership = OrganizationMember.objects.filter(
            user=request.user,
            status='ACTIVE'
        ).select_related('organization').first()
        
        organization = membership.organization if membership else None
        
        # Créer l'activité de tracking
        activity = UserActivity.objects.create(
            user=request.user if request.user.is_authenticated else None,
            organization=organization,
            activity_type=f"tracking.{data['event_type']}",
            description=f"Événement personnalisé: {data['event_type']}",
            metadata=data['event_data'],
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            session_id=data.get('session_id')
        )

        # Collecter les métriques si nécessaire
        MetricsCollector.collect_event_metric(
            event_type=data['event_type'],
            user=request.user,
            organization=organization,
            metadata=data['event_data']
        )

        return Response({
            'status': 'tracked',
            'event_id': str(activity.id),
            'timestamp': activity.created_at.isoformat()
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Erreur lors du tracking d'événement: {str(e)}")
        return Response(
            {'error': 'Erreur lors du tracking'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@extend_schema(
    summary="Rapport d'analytics",
    description="Génère un rapport d'analytics pour une organisation.",
    request=AnalyticsReportSerializer,
    responses={
        200: OpenApiResponse(
            description="Rapport généré avec succès",
            examples={
                "application/json": {
                    "organization_id": "550e8400-e29b-41d4-a716-446655440000",
                    "period": {"start": "2024-01-01", "end": "2024-01-31"},
                    "metrics": {
                        "user_activity": {"total": 1250, "daily_average": 40},
                        "system_performance": {"avg_response_time": 245, "error_rate": 0.02},
                        "app_metrics": {"total_apps": 15, "active_apps": 12}
                    }
                }
            }
        ),
        400: OpenApiResponse(description="Paramètres invalides"),
        403: OpenApiResponse(description="Accès non autorisé")
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analytics_report(request):
    """
    Génère un rapport d'analytics personnalisé.

    Permet de générer des rapports sur mesure avec les métriques
    demandées pour une période donnée.
    """
    serializer = AnalyticsReportSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    try:
        # Générer le rapport
        report = AnalyticsService.generate_analytics_report(
            organization_id=data['organization_id'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            metrics=data.get('metrics', []),
            group_by=data.get('group_by', 'day'),
            user=request.user
        )

        return Response(report, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Erreur lors de la génération du rapport: {str(e)}")
        return Response(
            {'error': 'Erreur lors de la génération du rapport'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@extend_schema(
    summary="Rapport de performance d'application",
    description="Génère un rapport de performance pour une application spécifique.",
    request=PerformanceReportSerializer,
    responses={
        200: OpenApiResponse(
            description="Rapport généré avec succès",
            examples={
                "application/json": {
                    "app_id": "550e8400-e29b-41d4-a716-446655440000",
                    "period": {"start": "2024-01-01", "end": "2024-01-31"},
                    "performance": {
                        "response_time": {"avg": 245, "min": 120, "max": 450},
                        "error_rate": 0.02,
                        "uptime": 0.98,
                        "requests_per_day": 1250
                    }
                }
            }
        ),
        400: OpenApiResponse(description="Paramètres invalides"),
        403: OpenApiResponse(description="Accès non autorisé"),
        404: OpenApiResponse(description="Application non trouvée")
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def performance_report(request):
    """
    Génère un rapport de performance pour une application.

    Fournit des métriques détaillées de performance pour
    une application spécifique sur une période donnée.
    """
    serializer = PerformanceReportSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    try:
        # Vérifier que l'utilisateur a accès à cette application
        from apps.runtime.models import GeneratedApp
        app = get_object_or_404(GeneratedApp, id=data['app_id'])

        # Vérifier les permissions
        if not (request.user.is_staff or request.user.is_superuser):
            from apps.foundation.permissions import is_org_member
            
            # Vérifier si c'est un projet perso
            if not app.project.organization:
                if app.project.created_by != request.user:
                    return Response(
                        {'error': 'Accès non autorisé à cette application'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            else:
                # Vérifier membership de l'organisation
                if not is_org_member(request.user, app.project.organization):
                    return Response(
                        {'error': 'Accès non autorisé à cette application'},
                        status=status.HTTP_403_FORBIDDEN
                    )

        # Générer le rapport de performance
        report = AnalyticsService.generate_performance_report(
            app_id=data['app_id'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            metrics=data.get('metrics', [])
        )

        return Response(report, status=status.HTTP_200_OK)

    except GeneratedApp.DoesNotExist:
        return Response(
            {'error': 'Application non trouvée'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Erreur lors de la génération du rapport de performance: {str(e)}")
        return Response(
            {'error': 'Erreur lors de la génération du rapport'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
