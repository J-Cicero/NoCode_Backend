"""
URLs pour le module Automation
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from .views import (
    WorkflowViewSet, WorkflowStepViewSet, IntegrationViewSet,
    WorkflowExecutionViewSet, ActionTemplateViewSet
)

app_name = 'automation'

# Router principal
router = DefaultRouter()
router.register(r'workflows', WorkflowViewSet, basename='workflow')
router.register(r'integrations', IntegrationViewSet, basename='integration')
router.register(r'executions', WorkflowExecutionViewSet, basename='execution')
router.register(r'action-templates', ActionTemplateViewSet, basename='action-template')

# Router imbriqué pour les étapes de workflows
workflows_router = routers.NestedDefaultRouter(router, r'workflows', lookup='workflow')
workflows_router.register(r'steps', WorkflowStepViewSet, basename='workflow-steps')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(workflows_router.urls)),
]
