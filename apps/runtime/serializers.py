"""
Sérialiseurs pour le module Runtime.

Définit les schémas de sérialisation pour les modèles du module Runtime.
"""
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils import timezone

from .models import GeneratedApp, DeploymentLog
from apps.studio.serializers import ProjectSerializer


class DeploymentActionSerializer(serializers.Serializer):
    """Sérialiseur pour les actions de déploiement."""
    target = serializers.ChoiceField(
        choices=['local', 'staging', 'production'],
        default='local',
        help_text="Cible de déploiement (local, staging, production)"
    )
    force = serializers.BooleanField(
        default=False,
        help_text="Forcer le déploiement même si aucun changement détecté"
    )
    
    def validate(self, attrs):
        """Valide les données de l'action de déploiement."""
        # Ajouter des validations personnalisées si nécessaire
        return attrs


class DeploymentLogSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les journaux de déploiement."""
    
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    performed_by = serializers.StringRelatedField(
        source='performed_by.email',
        read_only=True
    )
    
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = DeploymentLog
        fields = [
            'id', 'app', 'status', 'status_display', 'started_at',
            'completed_at', 'performed_by', 'duration', 'error_message'
        ]
        read_only_fields = [
            'id', 'app', 'status', 'started_at', 'completed_at',
            'performed_by', 'duration', 'error_message'
        ]
    
    def get_duration(self, obj):
        """Calcule la durée du déploiement en secondes."""
        if not obj.completed_at:
            return None
        duration = obj.completed_at - obj.started_at
        return duration.total_seconds()


class GeneratedAppSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les applications générées."""
    
    project = ProjectSerializer(read_only=True)
    project_tracking_id = serializers.UUIDField(write_only=True)
    
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    deployment_target_display = serializers.CharField(
        source='get_deployment_target_display',
        read_only=True
    )
    
    last_deployment = serializers.SerializerMethodField()
    
    class Meta:
        model = GeneratedApp
        fields = [
            'id', 'project', 'project_tracking_id', 'version', 'status', 'status_display',
            'deployment_target', 'deployment_target_display', 'api_base_url',
            'admin_url', 'created_at', 'updated_at', 'last_deployed_at',
            'last_deployment', 'config'
        ]
        read_only_fields = [
            'id', 'project', 'status', 'created_at', 'updated_at',
            'last_deployed_at', 'last_deployment'
        ]
    
    def get_last_deployment(self, obj):
        """Récupère les informations du dernier déploiement."""
        last_deployment = obj.deployment_logs.order_by('-started_at').first()
        if last_deployment:
            return DeploymentLogSerializer(last_deployment).data
        return None
    
    def validate_project_tracking_id(self, value):
        """Vérifie que le projet existe et que l'utilisateur y a accès."""
        from apps.studio.models import Project
        from apps.foundation.models import OrganizationMember
        
        try:
            project = Project.objects.get(tracking_id=value)
            user = self.context['request'].user

            if user.is_superuser:
                return value

            if project.organization is None:
                if project.created_by_id != user.id:
                    raise ValidationError("Vous n'avez pas accès à ce projet.")
                return value

            org_ids = OrganizationMember.objects.filter(
                user=user,
                status='ACTIVE'
            ).values_list('organization_id', flat=True)

            if project.organization_id not in org_ids:
                raise ValidationError("Vous n'avez pas accès à ce projet.")

            return value
        except Project.DoesNotExist:
            raise ValidationError("Projet introuvable.")
    
    def create(self, validated_data):
        """Crée une nouvelle application générée."""
        from apps.studio.models import Project
        
        project_tracking_id = validated_data.pop('project_tracking_id')
        project = Project.objects.get(tracking_id=project_tracking_id)
        
        if GeneratedApp.objects.filter(project=project).exists():
            raise ValidationError({"project_tracking_id": "Une application existe déjà pour ce projet."})
        
        app = GeneratedApp.objects.create(
            project=project,
            **validated_data
        )
        
        return app
    
    def update(self, instance, validated_data):
        """Met à jour une application générée."""
        # Mise à jour de la version si nécessaire
        if 'version' in validated_data and validated_data['version'] != instance.version:
            validated_data['last_versioned_at'] = timezone.now()
        
        return super().update(instance, validated_data)


class AppStatusSerializer(serializers.Serializer):
    """Sérialiseur pour le statut d'une application."""
    
    app_id = serializers.UUIDField()
    status = serializers.CharField()
    deployment_status = serializers.DictField()
    last_deployed = serializers.DateTimeField(allow_null=True)
    api_url = serializers.URLField(allow_blank=True, allow_null=True)
    admin_url = serializers.URLField(allow_blank=True, allow_null=True)


class AppLogsSerializer(serializers.Serializer):
    """Sérialiseur pour les logs d'une application."""
    
    app_id = serializers.UUIDField()
    logs = serializers.CharField()
