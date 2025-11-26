"""
URLs configuration for the runtime module.

This module defines the URL patterns for the runtime API endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'apps', views.GeneratedAppViewSet, basename='app')
router.register(r'deployment-logs', views.DeploymentLogViewSet, basename='deployment-log')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    
    # ============================================
    # ENDPOINTS API DYNAMIQUES NOCODE
    # ============================================
    
    # Schéma du projet (métadonnées de toutes les tables)
    path('projects/<uuid:project_id>/schema/', views.ProjectSchemaViewSet.as_view({'get': 'list'}), name='project-schema'),
    path('projects/<uuid:project_id>/schema/<str:pk>/', views.ProjectSchemaViewSet.as_view({'get': 'retrieve'}), name='project-table-schema'),
    
    # CRUD dynamique pour chaque table
    path('projects/<uuid:project_id>/tables/<str:table_name>/', views.DynamicTableViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='dynamic-table-list'),
    
    path('projects/<uuid:project_id>/tables/<str:table_name>/<int:pk>/', views.DynamicTableViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='dynamic-table-detail'),
    
    # Métadonnées pour le frontend
    path('projects/<uuid:project_id>/tables/<str:table_name>/schema/', views.DynamicTableViewSet.as_view({
        'get': 'schema'
    }), name='dynamic-table-schema'),
    
    path('projects/<uuid:project_id>/tables/<str:table_name>/fields/', views.DynamicTableViewSet.as_view({
        'get': 'fields'
    }), name='dynamic-table-fields'),
]
