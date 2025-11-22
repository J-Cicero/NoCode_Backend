"""
URLs pour le module Automation
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    WorkflowViewSet, WorkflowStepViewSet, IntegrationViewSet,
    WorkflowExecutionViewSet, ActionTemplateViewSet, NodeViewSet, EdgeViewSet, WorkflowGraphViewSet
)

app_name = 'automation'

# Router principal
router = DefaultRouter()
router.register(r'workflows', WorkflowViewSet, basename='workflow')
router.register(r'integrations', IntegrationViewSet, basename='integration')
router.register(r'executions', WorkflowExecutionViewSet, basename='execution')
router.register(r'action-templates', ActionTemplateViewSet, basename='action-template')

# Router imbriqué pour les opérations de graphe
workflow_router = DefaultRouter()
workflow_router.register(r'nodes', NodeViewSet, basename='workflow-node')
workflow_router.register(r'edges', EdgeViewSet, basename='workflow-edge')
workflow_router.register(r'graph', WorkflowGraphViewSet, basename='workflow-graph')

# Note: Les WorkflowSteps sont accessibles via les actions custom des workflows
# POST /api/automation/workflows/{id}/steps/
# Les nœuds et arêtes sont accessibles via:
# GET/POST /api/automation/workflows/{id}/nodes/
# GET/POST /api/automation/workflows/{id}/edges/
# GET /api/automation/workflows/{id}/graph/

urlpatterns = [
    path('', include(router.urls)),
    path('workflows/<uuid:pk>/', include(workflow_router.urls)),
]
