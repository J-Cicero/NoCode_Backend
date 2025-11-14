"""
Sérialiseurs pour le module Insights.

Convertit les modèles en formats JSON pour les APIs REST.
"""
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import UserActivity, SystemMetric, ApplicationMetric, UserMetric, PerformanceMetric

class ContentTypeSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les ContentTypes."""

    class Meta:
        model = ContentType
        fields = ['id', 'app_label', 'model']

class UserActivitySerializer(serializers.ModelSerializer):
    """Sérialiseur pour les activités utilisateur."""

    user = serializers.StringRelatedField(read_only=True)
    organization = serializers.StringRelatedField(read_only=True)
    content_type = ContentTypeSerializer(read_only=True)
    content_object = serializers.SerializerMethodField()

    class Meta:
        model = UserActivity
        fields = [
            'id', 'user', 'organization', 'activity_type', 'description',
            'metadata', 'content_type', 'object_id', 'content_object',
            'ip_address', 'user_agent', 'session_id', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_content_object(self, obj):
        """Retourne l'objet générique associé."""
        if obj.content_object:
            return {
                'type': obj.content_type.model,
                'id': obj.object_id,
                'str': str(obj.content_object)
            }
        return None

class UserActivityCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour créer une activité utilisateur."""

    class Meta:
        model = UserActivity
        fields = [
            'activity_type', 'description', 'metadata',
            'content_type', 'object_id', 'ip_address', 'user_agent'
        ]

    def create(self, validated_data):
        """Crée une activité avec l'utilisateur et l'organisation du contexte."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
            validated_data['organization'] = request.user.organization

        return super().create(validated_data)

class SystemMetricSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les métriques système."""

    class Meta:
        model = SystemMetric
        fields = [
            'id', 'metric_type', 'value', 'unit', 'tags',
            'hostname', 'service', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class ApplicationMetricSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les métriques d'application."""

    app = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ApplicationMetric
        fields = [
            'id', 'app', 'metric_type', 'value', 'unit',
            'environment', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class UserMetricSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les métriques utilisateur."""

    user = serializers.StringRelatedField(read_only=True)
    organization = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = UserMetric
        fields = [
            'id', 'user', 'organization', 'metric_type', 'value',
            'date', 'context', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class PerformanceMetricSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les métriques de performance."""

    organization = serializers.StringRelatedField(read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = PerformanceMetric
        fields = [
            'id', 'category', 'name', 'value', 'unit',
            'timestamp', 'organization', 'user', 'metadata'
        ]
        read_only_fields = ['id', 'timestamp']

class EventTrackingSerializer(serializers.Serializer):
    """Sérialiseur pour le tracking d'événements personnalisés."""

    event_type = serializers.CharField(max_length=100, required=True)
    event_data = serializers.DictField(required=True)
    timestamp = serializers.DateTimeField(default_timezone=timezone.now)
    session_id = serializers.CharField(max_length=255, required=False, allow_blank=True)
    user_id = serializers.UUIDField(required=False)
    organization_id = serializers.UUIDField(required=False)

    def validate_event_type(self, value):
        """Valide que le type d'événement est autorisé."""
        allowed_events = [
            'page_view', 'button_click', 'form_submit', 'api_call',
            'error_occurred', 'feature_used', 'search_performed'
        ]
        if value not in allowed_events:
            raise serializers.ValidationError(
                f"Type d'événement non autorisé. Utilisez: {', '.join(allowed_events)}"
            )
        return value

class AnalyticsReportSerializer(serializers.Serializer):
    """Sérialiseur pour les rapports d'analytics."""

    organization_id = serializers.UUIDField(required=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    metrics = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=['user_activity', 'system_performance', 'app_metrics']
    )
    group_by = serializers.ChoiceField(
        choices=['day', 'week', 'month'],
        default='day'
    )

class PerformanceReportSerializer(serializers.Serializer):
    """Sérialiseur pour les rapports de performance."""

    app_id = serializers.UUIDField(required=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    metrics = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=['response_time', 'error_rate', 'uptime']
    )
