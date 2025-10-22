"""
Consumers WebSocket pour le module Automation
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

logger = logging.getLogger(__name__)


class WorkflowExecutionConsumer(AsyncWebsocketConsumer):
    """
    Consumer pour suivre l'exécution d'un workflow en temps réel.
    """
    
    async def connect(self):
        """Connexion au WebSocket."""
        self.execution_id = self.scope['url_route']['kwargs']['execution_id']
        self.execution_group_name = f'execution_{self.execution_id}'
        
        # Vérifier l'authentification
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close()
            return
        
        # Vérifier les permissions
        has_permission = await self.check_permissions(user)
        if not has_permission:
            await self.close()
            return
        
        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.execution_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Envoyer l'état initial
        initial_state = await self.get_execution_state()
        await self.send(text_data=json.dumps({
            'type': 'initial_state',
            'execution': initial_state,
            'timestamp': timezone.now().isoformat(),
        }))
        
        logger.info(f"Client connecté pour suivre l'exécution {self.execution_id}")
    
    async def disconnect(self, close_code):
        """Déconnexion du WebSocket."""
        await self.channel_layer.group_discard(
            self.execution_group_name,
            self.channel_name
        )
        
        logger.info(f"Client déconnecté de l'exécution {self.execution_id}")
    
    async def receive(self, text_data):
        """Réception d'un message du client."""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat(),
                }))
            
            elif action == 'get_logs':
                logs = await self.get_execution_logs()
                await self.send(text_data=json.dumps({
                    'type': 'logs',
                    'logs': logs,
                    'timestamp': timezone.now().isoformat(),
                }))
                
        except json.JSONDecodeError:
            logger.error("Erreur de décodage JSON")
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {e}", exc_info=True)
    
    # Handlers pour les événements diffusés par le groupe
    
    async def execution_started(self, event):
        """Événement: exécution démarrée."""
        await self.send(text_data=json.dumps({
            'type': 'execution_started',
            'execution_id': event['execution_id'],
            'timestamp': event.get('timestamp', timezone.now().isoformat()),
        }))
    
    async def step_started(self, event):
        """Événement: étape démarrée."""
        await self.send(text_data=json.dumps({
            'type': 'step_started',
            'step_id': event['step_id'],
            'step_name': event.get('step_name'),
            'timestamp': event.get('timestamp', timezone.now().isoformat()),
        }))
    
    async def step_completed(self, event):
        """Événement: étape complétée."""
        await self.send(text_data=json.dumps({
            'type': 'step_completed',
            'step_id': event['step_id'],
            'step_name': event.get('step_name'),
            'result': event.get('result'),
            'timestamp': event.get('timestamp', timezone.now().isoformat()),
        }))
    
    async def step_failed(self, event):
        """Événement: étape échouée."""
        await self.send(text_data=json.dumps({
            'type': 'step_failed',
            'step_id': event['step_id'],
            'step_name': event.get('step_name'),
            'error': event.get('error'),
            'timestamp': event.get('timestamp', timezone.now().isoformat()),
        }))
    
    async def execution_completed(self, event):
        """Événement: exécution terminée."""
        await self.send(text_data=json.dumps({
            'type': 'execution_completed',
            'execution_id': event['execution_id'],
            'status': event['status'],
            'duration': event.get('duration'),
            'output_data': event.get('output_data'),
            'timestamp': event.get('timestamp', timezone.now().isoformat()),
        }))
    
    async def execution_failed(self, event):
        """Événement: exécution échouée."""
        await self.send(text_data=json.dumps({
            'type': 'execution_failed',
            'execution_id': event['execution_id'],
            'error': event.get('error'),
            'timestamp': event.get('timestamp', timezone.now().isoformat()),
        }))
    
    async def log_entry(self, event):
        """Événement: nouveau log."""
        await self.send(text_data=json.dumps({
            'type': 'log',
            'log': {
                'level': event.get('level'),
                'message': event.get('message'),
                'step_id': event.get('step_id'),
                'details': event.get('details'),
            },
            'timestamp': event.get('timestamp', timezone.now().isoformat()),
        }))
    
    # Méthodes de base de données
    
    @database_sync_to_async
    def check_permissions(self, user):
        """Vérifie que l'utilisateur a accès à cette exécution."""
        from ..models import WorkflowExecution
        
        try:
            execution = WorkflowExecution.objects.select_related('workflow__organization').get(
                id=self.execution_id
            )
            
            # Vérifier que l'utilisateur appartient à la même organisation
            if hasattr(user, 'organization'):
                return execution.workflow.organization == user.organization
            
            return False
        except WorkflowExecution.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_execution_state(self):
        """Récupère l'état actuel de l'exécution."""
        from ..models import WorkflowExecution
        from ..serializers import WorkflowExecutionDetailSerializer
        
        try:
            execution = WorkflowExecution.objects.select_related('workflow', 'triggered_by').get(
                id=self.execution_id
            )
            
            serializer = WorkflowExecutionDetailSerializer(execution)
            return serializer.data
        except WorkflowExecution.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_execution_logs(self):
        """Récupère les logs de l'exécution."""
        from ..models import WorkflowExecutionLog
        from ..serializers import WorkflowExecutionLogSerializer
        
        logs = WorkflowExecutionLog.objects.filter(
            execution_id=self.execution_id
        ).order_by('created_at')
        
        serializer = WorkflowExecutionLogSerializer(logs, many=True)
        return serializer.data


class WorkflowMonitorConsumer(AsyncWebsocketConsumer):
    """
    Consumer pour monitorer tous les workflows d'une organisation.
    """
    
    async def connect(self):
        """Connexion au WebSocket."""
        user = self.scope.get('user')
        
        if not user or not user.is_authenticated:
            await self.close()
            return
        
        if not hasattr(user, 'organization'):
            await self.close()
            return
        
        self.organization_id = user.organization.id
        self.monitor_group_name = f'workflow_monitor_{self.organization_id}'
        
        # Rejoindre le groupe de monitoring
        await self.channel_layer.group_add(
            self.monitor_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Envoyer les statistiques initiales
        stats = await self.get_organization_stats()
        await self.send(text_data=json.dumps({
            'type': 'initial_stats',
            'stats': stats,
            'timestamp': timezone.now().isoformat(),
        }))
        
        logger.info(f"Client connecté au monitoring de l'organisation {self.organization_id}")
    
    async def disconnect(self, close_code):
        """Déconnexion du WebSocket."""
        await self.channel_layer.group_discard(
            self.monitor_group_name,
            self.channel_name
        )
        
        logger.info(f"Client déconnecté du monitoring de l'organisation {self.organization_id}")
    
    async def receive(self, text_data):
        """Réception d'un message du client."""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'get_stats':
                stats = await self.get_organization_stats()
                await self.send(text_data=json.dumps({
                    'type': 'stats',
                    'stats': stats,
                    'timestamp': timezone.now().isoformat(),
                }))
            
            elif action == 'get_active_executions':
                executions = await self.get_active_executions()
                await self.send(text_data=json.dumps({
                    'type': 'active_executions',
                    'executions': executions,
                    'timestamp': timezone.now().isoformat(),
                }))
                
        except json.JSONDecodeError:
            logger.error("Erreur de décodage JSON")
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {e}", exc_info=True)
    
    # Handlers pour les événements
    
    async def workflow_created(self, event):
        """Événement: nouveau workflow créé."""
        await self.send(text_data=json.dumps({
            'type': 'workflow_created',
            'workflow': event.get('workflow'),
            'timestamp': event.get('timestamp', timezone.now().isoformat()),
        }))
    
    async def execution_started(self, event):
        """Événement: nouvelle exécution démarrée."""
        await self.send(text_data=json.dumps({
            'type': 'execution_started',
            'execution': event.get('execution'),
            'timestamp': event.get('timestamp', timezone.now().isoformat()),
        }))
    
    async def execution_completed(self, event):
        """Événement: exécution terminée."""
        await self.send(text_data=json.dumps({
            'type': 'execution_completed',
            'execution_id': event['execution_id'],
            'workflow_id': event.get('workflow_id'),
            'status': event['status'],
            'duration': event.get('duration'),
            'timestamp': event.get('timestamp', timezone.now().isoformat()),
        }))
    
    # Méthodes de base de données
    
    @database_sync_to_async
    def get_organization_stats(self):
        """Récupère les statistiques de l'organisation."""
        from ..models import Workflow, WorkflowExecution
        from django.db.models import Count, Avg
        from datetime import timedelta
        
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        
        # Compter les workflows
        workflows_count = Workflow.objects.filter(
            organization_id=self.organization_id
        ).count()
        
        # Compter les exécutions des dernières 24h
        recent_executions = WorkflowExecution.objects.filter(
            workflow__organization_id=self.organization_id,
            created_at__gte=last_24h
        )
        
        executions_count = recent_executions.count()
        success_count = recent_executions.filter(status='completed').count()
        failed_count = recent_executions.filter(status='failed').count()
        running_count = recent_executions.filter(status='running').count()
        
        return {
            'workflows_count': workflows_count,
            'executions_24h': executions_count,
            'success_count': success_count,
            'failed_count': failed_count,
            'running_count': running_count,
            'success_rate': (success_count / executions_count * 100) if executions_count > 0 else 0,
        }
    
    @database_sync_to_async
    def get_active_executions(self):
        """Récupère les exécutions actives."""
        from ..models import WorkflowExecution
        from ..serializers import WorkflowExecutionListSerializer
        
        executions = WorkflowExecution.objects.filter(
            workflow__organization_id=self.organization_id,
            status__in=['pending', 'running']
        ).select_related('workflow', 'triggered_by').order_by('-created_at')[:10]
        
        serializer = WorkflowExecutionListSerializer(executions, many=True)
        return serializer.data
