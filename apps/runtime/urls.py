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
]
