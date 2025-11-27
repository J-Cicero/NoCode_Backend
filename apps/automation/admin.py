"""
Configuration de l'administration Django pour Automation
"""
from django.contrib import admin
from .models import (
    Workflow, WorkflowStep, Trigger, Integration,
    IntegrationCredential, WorkflowExecution,
    WorkflowExecutionLog, ActionTemplate
)


# Only show Automation admin to superusers/staff
def has_admin_permission(request):
    """Check if user has admin permissions for Automation module"""
    return request.user.is_superuser or request.user.is_staff


class WorkflowStepInline(admin.TabularInline):
    model = WorkflowStep
    extra = 0
    fields = ['step_id', 'name', 'action_type', 'order', 'on_error']
    ordering = ['order']


class TriggerInline(admin.TabularInline):
    model = Trigger
    extra = 0
    fields = ['trigger_type', 'is_active', 'event_type', 'cron_expression']


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'status', 'execution_count', 'success_rate', 'last_executed_at', 'created_at']
    list_filter = ['status', 'created_at', 'organization']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'execution_count', 'success_count', 'failure_count', 'last_executed_at', 'created_at', 'updated_at']
    inlines = [WorkflowStepInline, TriggerInline]
    
    def has_module_permission(self, request):
        return has_admin_permission(request)
    
    def has_view_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_change_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_add_permission(self, request):
        return has_admin_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('id', 'name', 'description', 'organization', 'created_by', 'project', 'status')
        }),
        ('Configuration', {
            'fields': ('config', 'variables')
        }),
        ('Statistiques', {
            'fields': ('execution_count', 'success_count', 'failure_count', 'last_executed_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    list_display = ['step_id', 'workflow', 'name', 'action_type', 'order', 'on_error']
    list_filter = ['action_type', 'on_error', 'workflow']
    search_fields = ['name', 'step_id', 'workflow__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def has_module_permission(self, request):
        return has_admin_permission(request)
    
    def has_view_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_change_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_add_permission(self, request):
        return has_admin_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        return has_admin_permission(request)


@admin.register(Trigger)
class TriggerAdmin(admin.ModelAdmin):
    list_display = ['workflow', 'trigger_type', 'is_active', 'event_type', 'created_at']
    list_filter = ['trigger_type', 'is_active', 'created_at']
    search_fields = ['workflow__name', 'event_type']
    readonly_fields = ['id', 'webhook_url', 'created_at', 'updated_at']
    
    def has_module_permission(self, request):
        return has_admin_permission(request)
    
    def has_view_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_change_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_add_permission(self, request):
        return has_admin_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        return has_admin_permission(request)


@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    list_display = ['name', 'integration_type', 'organization', 'status', 'success_rate', 'last_used_at']
    list_filter = ['integration_type', 'status', 'organization']
    search_fields = ['name']
    readonly_fields = ['id', 'total_calls', 'successful_calls', 'failed_calls', 'last_used_at', 'created_at', 'updated_at']
    
    def has_module_permission(self, request):
        return has_admin_permission(request)
    
    def has_view_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_change_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_add_permission(self, request):
        return has_admin_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('id', 'name', 'integration_type', 'organization', 'status')
        }),
        ('Configuration', {
            'fields': ('config', 'rate_limit', 'metadata')
        }),
        ('Statistiques', {
            'fields': ('total_calls', 'successful_calls', 'failed_calls', 'last_used_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(IntegrationCredential)
class IntegrationCredentialAdmin(admin.ModelAdmin):
    list_display = ['integration', 'credential_type', 'is_active', 'expires_at', 'created_at']
    list_filter = ['is_active', 'credential_type', 'created_at']
    search_fields = ['integration__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def has_module_permission(self, request):
        return has_admin_permission(request)
    
    def has_view_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_change_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_add_permission(self, request):
        return has_admin_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        return has_admin_permission(request)


class WorkflowExecutionLogInline(admin.TabularInline):
    model = WorkflowExecutionLog
    extra = 0
    fields = ['level', 'message', 'step_id', 'created_at']
    readonly_fields = ['level', 'message', 'step_id', 'created_at']
    can_delete = False
    max_num = 0  # Read-only


@admin.register(WorkflowExecution)
class WorkflowExecutionAdmin(admin.ModelAdmin):
    list_display = ['id', 'workflow', 'status', 'triggered_by', 'duration_display', 'started_at', 'completed_at']
    list_filter = ['status', 'created_at', 'workflow']
    search_fields = ['workflow__name', 'id']
    readonly_fields = ['id', 'duration', 'created_at', 'updated_at']
    inlines = [WorkflowExecutionLogInline]
    
    def has_module_permission(self, request):
        return has_admin_permission(request)
    
    def has_view_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_change_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_add_permission(self, request):
        return has_admin_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('id', 'workflow', 'trigger', 'triggered_by', 'status')
        }),
        ('Données', {
            'fields': ('input_data', 'output_data', 'context'),
            'classes': ('collapse',)
        }),
        ('Progression', {
            'fields': ('current_step_id', 'completed_steps')
        }),
        ('Erreurs', {
            'fields': ('error_message', 'error_details'),
            'classes': ('collapse',)
        }),
        ('Durée', {
            'fields': ('duration', 'started_at', 'completed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def duration_display(self, obj):
        if obj.duration:
            return f"{obj.duration:.2f}s"
        return "-"
    duration_display.short_description = 'Durée'


@admin.register(WorkflowExecutionLog)
class WorkflowExecutionLogAdmin(admin.ModelAdmin):
    list_display = ['execution', 'level', 'step_id', 'message_short', 'created_at']
    list_filter = ['level', 'created_at']
    search_fields = ['message', 'execution__id']
    readonly_fields = ['id', 'created_at']
    
    def has_module_permission(self, request):
        return has_admin_permission(request)
    
    def has_view_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_change_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_add_permission(self, request):
        return has_admin_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def message_short(self, obj):
        return obj.message[:100] if len(obj.message) > 100 else obj.message
    message_short.short_description = 'Message'


@admin.register(ActionTemplate)
class ActionTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'action_type', 'is_public', 'is_system', 'organization']
    list_filter = ['category', 'is_public', 'is_system', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def has_module_permission(self, request):
        return has_admin_permission(request)
    
    def has_view_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_change_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    def has_add_permission(self, request):
        return has_admin_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        return has_admin_permission(request)
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('id', 'name', 'description', 'category', 'action_type')
        }),
        ('Configuration', {
            'fields': ('default_params', 'param_schema')
        }),
        ('Visibilité', {
            'fields': ('is_public', 'is_system', 'organization')
        }),
        ('Métadonnées', {
            'fields': ('icon', 'tags'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
