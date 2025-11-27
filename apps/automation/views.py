"""
Views pour le module Automation
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
import logging
from .models import (
    Workflow, WorkflowStep, Trigger, Integration,
    WorkflowExecution, WorkflowExecutionLog, ActionTemplate, Node, Edge
)
from .serializers import (
    WorkflowListSerializer, WorkflowDetailSerializer, WorkflowCreateSerializer,
    WorkflowStepSerializer, TriggerSerializer, IntegrationSerializer,
    WorkflowExecutionListSerializer, WorkflowExecutionDetailSerializer,
    WorkflowExecutionLogSerializer, ActionTemplateSerializer,
    WorkflowExecuteSerializer, IntegrationTestSerializer,
    IntegrationCredentialCreateSerializer, NodeSerializer, EdgeSerializer, WorkflowGraphSerializer
)
from apps.foundation.permissions import IsOrgMember, IsOrgAdmin

logger = logging.getLogger(__name__)


class WorkflowViewSet(viewsets.ModelViewSet):
    """
    API pour gérer les workflows.
    
    Endpoints:
    - GET /api/automation/workflows/ : Liste des workflows
    - POST /api/automation/workflows/ : Créer un workflow
    - GET /api/automation/workflows/{id}/ : Détails d'un workflow
    - PUT /api/automation/workflows/{id}/ : Mettre à jour un workflow
    - DELETE /api/automation/workflows/{id}/ : Supprimer un workflow
    - POST /api/automation/workflows/{id}/execute/ : Exécuter un workflow
    - GET /api/automation/workflows/{id}/executions/ : Historique d'exécutions
    - POST /api/automation/workflows/{id}/validate/ : Valider un workflow
    - POST /api/automation/workflows/{id}/duplicate/ : Dupliquer un workflow
    """
    
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get_queryset(self):
        user = self.request.user
        
        # Staff voit tout
        if user.is_staff or user.is_superuser:
            return Workflow.objects.all().select_related(
                'organization', 'created_by', 'project'
            ).prefetch_related('steps', 'triggers')
        
        # Récupérer les organisations dont l'utilisateur est membre
        from apps.foundation.permissions import get_user_organizations
        org_ids = get_user_organizations(user)
        
        return Workflow.objects.filter(
            organization_id__in=org_ids
        ).select_related('organization', 'created_by', 'project').prefetch_related('steps', 'triggers')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return WorkflowListSerializer
        elif self.action == 'create':
            return WorkflowCreateSerializer
        return WorkflowDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """
        Exécute un workflow.
        
        Body:
        {
            "input_data": {...},
            "async_execution": true
        }
        """
        workflow = self.get_object()
        
        serializer = WorkflowExecuteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        input_data = serializer.validated_data.get('input_data', {})
        async_execution = serializer.validated_data.get('async_execution', True)
        
        try:
            if async_execution:
                # Exécution asynchrone via Celery
                task = execute_workflow_async.delay(
                    workflow_id=str(workflow.id),
                    input_data=input_data,
                    user_id=request.user.id
                )
                
                return Response({
                    'message': 'Workflow démarré en arrière-plan',
                    'task_id': task.id,
                    'async': True,
                }, status=status.HTTP_202_ACCEPTED)
            else:
                # Exécution synchrone
                engine = WorkflowEngine(workflow)
                execution = engine.execute(
                    input_data=input_data,
                    triggered_by=request.user
                )
                
                serializer = WorkflowExecutionDetailSerializer(execution)
                return Response({
                    'message': 'Workflow exécuté avec succès',
                    'execution': serializer.data,
                    'async': False,
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du workflow: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def executions(self, request, pk=None):
        """
        Récupère l'historique des exécutions d'un workflow.
        """
        workflow = self.get_object()
        executions = workflow.executions.all().order_by('-created_at')
        
        # Pagination
        page = self.paginate_queryset(executions)
        if page is not None:
            serializer = WorkflowExecutionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = WorkflowExecutionListSerializer(executions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """
        Valide la configuration d'un workflow.
        """
        workflow = self.get_object()
        
        is_valid, errors = WorkflowValidator.validate(workflow)
        
        return Response({
            'is_valid': is_valid,
            'errors': errors,
        })
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        Duplique un workflow.
        """
        workflow = self.get_object()
        
        try:
            # Créer une copie
            new_workflow = Workflow.objects.create(
                name=f"{workflow.name} (Copie)",
                description=workflow.description,
                organization=workflow.organization,
                created_by=request.user,
                project=workflow.project,
                status='DRAFT',
                config=workflow.config,
                variables=workflow.variables,
            )
            
            # Copier les étapes
            for step in workflow.steps.all():
                WorkflowStep.objects.create(
                    workflow=new_workflow,
                    name=step.name,
                    step_id=step.step_id,
                    action_type=step.action_type,
                    params=step.params,
                    integration=step.integration,
                    order=step.order,
                    condition=step.condition,
                    on_error=step.on_error,
                    retry_count=step.retry_count,
                    retry_delay=step.retry_delay,
                    metadata=step.metadata,
                )
            
            # Copier les déclencheurs
            for trigger in workflow.triggers.all():
                Trigger.objects.create(
                    workflow=new_workflow,
                    trigger_type=trigger.trigger_type,
                    config=trigger.config,
                    cron_expression=trigger.cron_expression,
                    event_type=trigger.event_type,
                    is_active=False,  # Désactivé par défaut
                    metadata=trigger.metadata,
                )
            
            serializer = WorkflowDetailSerializer(new_workflow)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Erreur lors de la duplication: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WorkflowStepViewSet(viewsets.ModelViewSet):
    """
    API pour gérer les étapes de workflows.
    """
    
    serializer_class = WorkflowStepSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get_queryset(self):
        user = self.request.user
        workflow_id = self.kwargs.get('workflow_pk')
        
        if not workflow_id:
            return WorkflowStep.objects.none()
        
        # Staff voit tout
        if user.is_staff or user.is_superuser:
            return WorkflowStep.objects.filter(
                workflow_id=workflow_id
            ).order_by('order')
        
        # Récupérer les organisations dont l'utilisateur est membre
        from apps.foundation.permissions import get_user_organizations
        org_ids = get_user_organizations(user)
        
        return WorkflowStep.objects.filter(
            workflow_id=workflow_id,
            workflow__organization_id__in=org_ids
        ).order_by('order')
    
    def perform_create(self, serializer):
        workflow_id = self.kwargs.get('workflow_pk')
        workflow = get_object_or_404(Workflow, id=workflow_id)
        serializer.save(workflow=workflow)


class IntegrationViewSet(viewsets.ModelViewSet):
    """
    API pour gérer les intégrations.
    
    Endpoints:
    - GET /api/automation/integrations/ : Liste des intégrations
    - GET /api/automation/integrations/available/ : Intégrations disponibles
    - POST /api/automation/integrations/configure/ : Configurer une intégration
    - POST /api/automation/integrations/{id}/test/ : Tester une intégration
    - POST /api/automation/integrations/{id}/execute/ : Exécuter une action
    """
    
    serializer_class = IntegrationSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get_queryset(self):
        user = self.request.user
        
        # Staff voit tout
        if user.is_staff or user.is_superuser:
            return Integration.objects.all().select_related('organization')
        
        # Récupérer les organisations dont l'utilisateur est membre
        from apps.foundation.permissions import get_user_organizations
        org_ids = get_user_organizations(user)
        
        return Integration.objects.filter(
            organization_id__in=org_ids
        ).select_related('organization')
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """
        Liste les types d'intégrations disponibles.
        """
        available_integrations = [
            {
                'type': 'email',
                'name': 'Email',
                'description': 'Envoi d\'emails via SMTP ou SendGrid',
                'icon': 'mail',
                'config_fields': ['provider', 'smtp_host', 'smtp_port', 'from_email'],
            },
            {
                'type': 'stripe',
                'name': 'Stripe',
                'description': 'Paiements et abonnements',
                'icon': 'credit-card',
                'config_fields': ['api_key'],
            },
            {
                'type': 'webhook',
                'name': 'Webhook HTTP',
                'description': 'Appels HTTP vers des APIs externes',
                'icon': 'send',
                'config_fields': ['url', 'method', 'headers'],
            },
            {
                'type': 'slack',
                'name': 'Slack',
                'description': 'Notifications Slack',
                'icon': 'message-square',
                'config_fields': ['webhook_url'],
            },
            {
                'type': 'database',
                'name': 'Base de données',
                'description': 'Requêtes sur bases de données',
                'icon': 'database',
                'config_fields': ['connection_string'],
            },
            {
                'type': 'api',
                'name': 'API REST',
                'description': 'API REST personnalisée',
                'icon': 'code',
                'config_fields': ['base_url', 'auth_type'],
            },
        ]
        
        return Response({
            'integrations': available_integrations,
            'count': len(available_integrations),
        })
    
    @action(detail=False, methods=['post'])
    def configure(self, request):
        """
        Configure une nouvelle intégration.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Créer l'intégration
        integration = serializer.save(organization=request.user.organization)
        
        # Sauvegarder les credentials si fournis
        credentials_data = request.data.get('credentials')
        if credentials_data:
            credential_serializer = IntegrationCredentialCreateSerializer(data=credentials_data)
            credential_serializer.is_valid(raise_exception=True)
            
            integration_service = IntegrationService()
            integration_service.save_credentials(
                integration=integration,
                credential_type=credential_serializer.validated_data['credential_type'],
                credentials_data=credential_serializer.validated_data['credentials_data'],
                expires_at=credential_serializer.validated_data.get('expires_at')
            )
        
        return Response(
            self.get_serializer(integration).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """
        Teste une intégration.
        """
        integration = self.get_object()
        
        integration_service = IntegrationService()
        success, message = integration_service.test_integration(integration)
        
        # Mettre à jour le statut
        if success:
            integration.status = 'active'
        else:
            integration.status = 'error'
        integration.save(update_fields=['status'])
        
        return Response({
            'success': success,
            'message': message,
            'status': integration.status,
        })
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """
        Exécute une action sur l'intégration.
        """
        integration = self.get_object()
        params = request.data.get('params', {})
        
        try:
            integration_service = IntegrationService()
            result = integration_service.execute(integration, params)
            
            return Response({
                'success': True,
                'result': result,
            })
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de l'intégration: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WorkflowExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API pour consulter les exécutions de workflows.
    """
    
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get_queryset(self):
        user = self.request.user
        
        # Staff voit tout
        if user.is_staff or user.is_superuser:
            return WorkflowExecution.objects.all().select_related(
                'workflow', 'trigger', 'triggered_by'
            ).order_by('-created_at')
        
        # Récupérer les organisations dont l'utilisateur est membre
        from apps.foundation.permissions import get_user_organizations
        org_ids = get_user_organizations(user)
        
        return WorkflowExecution.objects.filter(
            workflow__organization_id__in=org_ids
        ).select_related('workflow', 'trigger', 'triggered_by').order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return WorkflowExecutionListSerializer
        return WorkflowExecutionDetailSerializer
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """
        Récupère les logs d'une exécution.
        """
        execution = self.get_object()
        logs = execution.logs.all().order_by('created_at')
        
        serializer = WorkflowExecutionLogSerializer(logs, many=True)
        return Response({
            'logs': serializer.data,
            'count': logs.count(),
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Annule une exécution en cours.
        """
        execution = self.get_object()
        
        if not execution.is_running:
            return Response(
                {'error': 'L\'exécution n\'est pas en cours'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        execution.status = 'cancelled'
        execution.completed_at = timezone.now()
        execution.save(update_fields=['status', 'completed_at'])
        
        return Response({
            'message': 'Exécution annulée',
            'execution': self.get_serializer(execution).data,
        })


class ActionTemplateViewSet(viewsets.ModelViewSet):
    """
    API pour gérer les templates d'actions.
    """
    
    serializer_class = ActionTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Staff voit tout
        if user.is_staff or user.is_superuser:
            return ActionTemplate.objects.all().order_by('category', 'name')
        
        # Récupérer les organisations dont l'utilisateur est membre
        from apps.foundation.permissions import get_user_organizations
        org_ids = get_user_organizations(user)
        
        # Templates système + publics + ceux des organisations de l'utilisateur
        return ActionTemplate.objects.filter(
            Q(is_system=True) | Q(is_public=True) | Q(organization_id__in=org_ids)
        ).order_by('category', 'name')
    
    def perform_create(self, serializer):
        # Assigner à la première organisation active de l'utilisateur
        from apps.foundation.models import OrganizationMember
        
        membership = OrganizationMember.objects.filter(
            user=self.request.user,
            status='ACTIVE'
        ).select_related('organization').first()
        
        if membership:
            serializer.save(organization=membership.organization)
        else:
            serializer.save()


# === VIEWS POUR LE GRAPHE VISUEL (NODE/EDGE) ===

class NodeViewSet(viewsets.ModelViewSet):
    """ViewSet pour les opérations CRUD sur les nœuds."""
    
    serializer_class = NodeSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get_queryset(self):
        """Filtre les nœuds par workflow."""
        workflow_id = self.kwargs.get('workflow_pk')
        if workflow_id:
            return Node.objects.filter(workflow_id=workflow_id)
        return Node.objects.none()
    
    def perform_create(self, serializer):
        """Associe le nœud au workflow lors de la création."""
        workflow_id = self.kwargs.get('workflow_pk')
        workflow = get_object_or_404(Workflow, id=workflow_id)
        serializer.save(workflow=workflow)

    @action(detail=False, methods=['post'])
    def batch_create(self, request, workflow_pk=None):
        """Crée plusieurs nœuds en une seule opération."""
        workflow = get_object_or_404(Workflow, id=workflow_pk)
        
        if not isinstance(request.data, list):
            return Response(
                {'error': 'Les données doivent être une liste de nœuds'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_nodes = []
        errors = []
        
        with transaction.atomic():
            for index, node_data in enumerate(request.data):
                node_data['workflow'] = workflow.id
                serializer = self.get_serializer(data=node_data)
                
                if serializer.is_valid():
                    node = serializer.save()
                    created_nodes.append(serializer.data)
                else:
                    errors.append({
                        'index': index,
                        'errors': serializer.errors
                    })
        
        if errors:
            return Response({
                'created': created_nodes,
                'errors': errors,
                'partial_success': len(created_nodes) > 0
            }, status=status.HTTP_207_MULTI_STATUS if created_nodes else status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'created': created_nodes,
            'count': len(created_nodes)
        }, status=status.HTTP_201_CREATED)


class EdgeViewSet(viewsets.ModelViewSet):
    """ViewSet pour les opérations CRUD sur les arêtes."""
    
    serializer_class = EdgeSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get_queryset(self):
        """Filtre les arêtes par workflow."""
        workflow_id = self.kwargs.get('workflow_pk')
        if workflow_id:
            return Edge.objects.filter(workflow_id=workflow_id)
        return Edge.objects.none()
    
    def perform_create(self, serializer):
        """Associe l'arête au workflow lors de la création."""
        workflow_id = self.kwargs.get('workflow_pk')
        workflow = get_object_or_404(Workflow, id=workflow_id)
        serializer.save(workflow=workflow)


class WorkflowGraphViewSet(viewsets.GenericViewSet):
    """ViewSet pour les opérations sur le graphe complet d'un workflow."""
    
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get_queryset(self):
        return Workflow.objects.all()
    
    @action(detail=True, methods=['get'])
    def graph(self, request, pk=None):
        """Retourne le graphe complet du workflow."""
        workflow = get_object_or_404(Workflow, id=pk)
        serializer = WorkflowGraphSerializer(workflow)
        return Response(serializer.data)
