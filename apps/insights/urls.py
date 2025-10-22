"""
URLs pour le module Insights.

Définit les routes API pour :
- Tracking d'événements et activités
- Consultation des métriques
- Rapports d'analytics
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UserActivityViewSet, SystemMetricViewSet,
    ApplicationMetricViewSet, UserMetricViewSet,
    PerformanceMetricViewSet, track_event,
    analytics_report, performance_report
)

# Créer le routeur pour les ViewSets
router = DefaultRouter()
router.register(r'activities', UserActivityViewSet, basename='user-activity')
router.register(r'system-metrics', SystemMetricViewSet, basename='system-metric')
router.register(r'application-metrics', ApplicationMetricViewSet, basename='application-metric')
router.register(r'user-metrics', UserMetricViewSet, basename='user-metric')
router.register(r'performance-metrics', PerformanceMetricViewSet, basename='performance-metric')

# URLs personnalisées
urlpatterns = [
    # URLs du routeur
    path('', include(router.urls)),

    # Tracking d'événements
    path('track/', track_event, name='track-event'),

    # Rapports d'analytics
    path('analytics/', analytics_report, name='analytics-report'),

    # Rapports de performance
    path('performance/', performance_report, name='performance-report'),

    # Rapports rapides (pour compatibilité)
    path('analytics/<uuid:organization_id>/', analytics_report, name='quick-analytics'),
    path('performance/<uuid:app_id>/', performance_report, name='quick-performance'),
]
