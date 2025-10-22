"""
Serializers pour le module Automation
"""
from rest_framework import serializers
from .models import (
    Workflow, WorkflowStep, Trigger, Integration,
    IntegrationCredential, WorkflowExecution,
    WorkflowExecutionLog, ActionTemplate
)
from apps.foundation.serializers import UserBaseSerializer, OrganizationBaseSerializer


class WorkflowStepSerializer(serializers.ModelSerializer):
    """Serializer pour les étapes de workflow."""
    
    integration_name = serializers.CharField(source='integration.name', read_only=True)
    
    class Meta:
        model = WorkflowStep
        fields = [
            'id', 'step_id', 'name', 'action_type', 'params',
            'integration', 'integration_name', 'order', 'condition',
            'on_error', 'retry_count', 'retry_delay', 'metadata',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TriggerSerializer(serializers.ModelSerializer):
    """Serializer pour les déclencheurs."""
    
    class Meta:
        model = Trigger
        fields = [
            'id', 'trigger_type', 'config', 'webhook_url',
            'webhook_secret', 'cron_expression', 'event_type',
            'is_active', 'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'webhook_url', 'webhook_secret', 'created_at', 'updated_at']


class WorkflowListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour les listes de workflows."""
    
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    triggers_count = serializers.IntegerField(source='triggers.count', read_only=True)
    steps_count = serializers.IntegerField(source='steps.count', read_only=True)
    
    class Meta:
        model = Workflow
        fields = [
            'id', 'name', 'description', 'status', 'organization',
            'organization_name', 'created_by', 'created_by_name',
            'project', 'execution_count', 'success_count', 'failure_count',
            'success_rate', 'last_executed_at', 'triggers_count',
            'steps_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'execution_count', 'success_count', 'failure_count',
            'success_rate', 'last_executed_at', 'created_at', 'updated_at'
        ]


class WorkflowDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un workflow."""
    
    steps = WorkflowStepSerializer(many=True, read_only=True)
    triggers = TriggerSerializer(many=True, read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Workflow
        fields = [
            'id', 'name', 'description', 'status', 'organization',
            'organization_name', 'created_by', 'created_by_name',
            'project', 'config', 'variables', 'execution_count',
            'success_count', 'failure_count', 'success_rate',
            'last_executed_at', 'steps', 'triggers',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'execution_count', 'success_count', 'failure_count',
            'success_rate', 'last_executed_at', 'created_at', 'updated_at'
        ]


class WorkflowCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un workflow."""
    
    steps = WorkflowStepSerializer(many=True, required=False)
    triggers = TriggerSerializer(many=True, required=False)
    
    class Meta:
        model = Workflow
        fields = [
            'name', 'description', 'organization', 'project',
            'status', 'config', 'variables', 'steps', 'triggers'
        ]
    
    def create(self, validated_data):
        steps_data = validated_data.pop('steps', [])
        triggers_data = validated_data.pop('triggers', [])
        
        # Créer le workflow
        workflow = Workflow.objects.create(**validated_data)
        
        # Créer les étapes
        for step_data in steps_data:
            WorkflowStep.objects.create(workflow=workflow, **step_data)
        
        # Créer les déclencheurs
        for trigger_data in triggers_data:
            Trigger.objects.create(workflow=workflow, **trigger_data)
        
        return workflow


class IntegrationSerializer(serializers.ModelSerializer):
    """Serializer pour les intégrations."""
    
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = Integration
        fields = [
            'id', 'name', 'integration_type', 'organization',
            'organization_name', 'config', 'status', 'total_calls',
            'successful_calls', 'failed_calls', 'success_rate',
            'last_used_at', 'rate_limit', 'metadata',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_calls', 'successful_calls', 'failed_calls',
            'success_rate', 'last_used_at', 'created_at', 'updated_at'
        ]


class IntegrationCredentialSerializer(serializers.ModelSerializer):
    """Serializer pour les credentials (sans exposer les données sensibles)."""
    
    class Meta:
        model = IntegrationCredential
        fields = [
            'id', 'credential_type', 'is_active', 'expires_at',
            'is_expired', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_expired', 'created_at', 'updated_at']


class WorkflowExecutionLogSerializer(serializers.ModelSerializer):
    """Serializer pour les logs d'exécution."""
    
    step_name = serializers.CharField(source='step.name', read_only=True)
    
    class Meta:
        model = WorkflowExecutionLog
        fields = [
            'id', 'step', 'step_id', 'step_name', 'level',
            'message', 'details', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class WorkflowExecutionListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour les listes d'exécutions."""
    
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    triggered_by_name = serializers.CharField(source='triggered_by.get_full_name', read_only=True)
    trigger_type = serializers.CharField(source='trigger.trigger_type', read_only=True)
    
    class Meta:
        model = WorkflowExecution
        fields = [
            'id', 'workflow', 'workflow_name', 'trigger', 'trigger_type',
            'triggered_by', 'triggered_by_name', 'status', 'duration',
            'current_step_id', 'started_at', 'completed_at', 'created_at'
        ]
        read_only_fields = ['id', 'duration', 'created_at']


class WorkflowExecutionDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour une exécution."""
    
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    triggered_by_name = serializers.CharField(source='triggered_by.get_full_name', read_only=True)
    logs = WorkflowExecutionLogSerializer(many=True, read_only=True)
    
    class Meta:
        model = WorkflowExecution
        fields = [
            'id', 'workflow', 'workflow_name', 'trigger', 'triggered_by',
            'triggered_by_name', 'status', 'input_data', 'output_data',
            'context', 'error_message', 'error_details', 'current_step_id',
            'completed_steps', 'duration', 'started_at', 'completed_at',
            'created_at', 'updated_at', 'logs'
        ]
        read_only_fields = [
            'id', 'duration', 'created_at', 'updated_at'
        ]


class ActionTemplateSerializer(serializers.ModelSerializer):
    """Serializer pour les templates d'actions."""
    
    organization_name = serializers.CharField(source='organization.name', read_only=True, allow_null=True)
    
    class Meta:
        model = ActionTemplate
        fields = [
            'id', 'name', 'description', 'category', 'action_type',
            'default_params', 'param_schema', 'is_public', 'is_system',
            'organization', 'organization_name', 'icon', 'tags',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_system', 'created_at', 'updated_at']


class WorkflowExecuteSerializer(serializers.Serializer):
    """Serializer pour exécuter un workflow."""
    
    input_data = serializers.JSONField(default=dict, required=False)
    async_execution = serializers.BooleanField(default=True)


class IntegrationTestSerializer(serializers.Serializer):
    """Serializer pour tester une intégration."""
    
    test_params = serializers.JSONField(default=dict, required=False)


class IntegrationCredentialCreateSerializer(serializers.Serializer):
    """Serializer pour créer des credentials."""
    
    credential_type = serializers.CharField()
    credentials_data = serializers.JSONField()
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
