"""
Services pour le module Insights.

Fournit les fonctionnalités de collecte de métriques,
d'analytics et de monitoring.
"""
import logging
import psutil
import time
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Q
from django.contrib.auth import get_user_model
from django.core.cache import cache

from .models import (
    UserActivity, SystemMetric, ApplicationMetric,
    UserMetric, PerformanceMetric
)

logger = logging.getLogger(__name__)
User = get_user_model()

class MetricsCollector:
    """Service de collecte de métriques système et applicatives."""

    @staticmethod
    def collect_system_metrics():
        """Collecte les métriques système (CPU, mémoire, disque, etc.)."""
        try:
            # Métriques CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            SystemMetric.objects.create(
                metric_type='cpu.usage',
                value=cpu_percent,
                unit='%',
                hostname='localhost',
                service='system'
            )

            # Métriques mémoire
            memory = psutil.virtual_memory()
            SystemMetric.objects.create(
                metric_type='memory.usage',
                value=memory.percent,
                unit='%',
                hostname='localhost',
                service='system'
            )

            # Métriques disque
            disk = psutil.disk_usage('/')
            SystemMetric.objects.create(
                metric_type='disk.usage',
                value=disk.percent,
                unit='%',
                hostname='localhost',
                service='system'
            )

            logger.info("Métriques système collectées avec succès")

        except Exception as e:
            logger.error(f"Erreur lors de la collecte des métriques système: {str(e)}")

    @staticmethod
    def collect_event_metric(event_type, user=None, organization=None, metadata=None):
        """Collecte une métrique basée sur un événement utilisateur."""
        try:
            # Métrique de comptage d'événements
            metric_type = f"events.{event_type}"

            # Créer ou mettre à jour la métrique quotidienne
            today = timezone.now().date()

            metric, created = UserMetric.objects.get_or_create(
                user=user,
                organization=organization,
                metric_type=metric_type,
                date=today,
                defaults={'value': 0}
            )

            metric.value += 1
            metric.context.update(metadata or {})
            metric.save()

        except Exception as e:
            logger.error(f"Erreur lors de la collecte de métrique d'événement: {str(e)}")

    @staticmethod
    def collect_application_metrics(app, metrics_data):
        """Collecte les métriques d'une application."""
        try:
            for metric_type, value in metrics_data.items():
                ApplicationMetric.objects.create(
                    app=app,
                    metric_type=metric_type,
                    value=value.get('value', 0),
                    unit=value.get('unit', ''),
                    environment=value.get('environment', 'production'),
                    metadata=value.get('metadata', {})
                )

        except Exception as e:
            logger.error(f"Erreur lors de la collecte des métriques d'application: {str(e)}")

    @staticmethod
    def collect_performance_metrics(category, name, value, unit='', metadata=None):
        """Collecte une métrique de performance."""
        try:
            PerformanceMetric.objects.create(
                category=category,
                name=name,
                value=value,
                unit=unit,
                metadata=metadata or {}
            )

        except Exception as e:
            logger.error(f"Erreur lors de la collecte de métrique de performance: {str(e)}")


class AnalyticsService:
    """Service d'analyse et génération de rapports."""

    @staticmethod
    def generate_analytics_report(organization_id, start_date, end_date, metrics=None, group_by='day', user=None):
        """Génère un rapport d'analytics pour une organisation."""
        try:
            report = {
                'organization_id': organization_id,
                'period': {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d')
                },
                'generated_at': timezone.now().isoformat(),
                'metrics': {}
            }

            # Activités utilisateur
            if not metrics or 'user_activity' in metrics:
                activities = UserActivity.objects.filter(
                    organization_id=organization_id,
                    created_at__range=[start_date, end_date]
                )

                # Comptage par type d'activité
                activity_counts = activities.values('activity_type').annotate(
                    count=Count('id')
                ).order_by('-count')

                # Comptage par jour
                daily_activities = activities.extra(
                    select={'day': 'DATE(created_at)'}
                ).values('day').annotate(count=Count('id')).order_by('day')

                report['metrics']['user_activity'] = {
                    'total': activities.count(),
                    'by_type': {item['activity_type']: item['count'] for item in activity_counts},
                    'daily': {item['day']: item['count'] for item in daily_activities},
                    'unique_users': activities.values('user').distinct().count()
                }

            # Métriques système
            if not metrics or 'system_performance' in metrics:
                system_metrics = SystemMetric.objects.filter(
                    created_at__range=[start_date, end_date]
                )

                # Agrégation par métrique
                system_agg = system_metrics.values('metric_type').annotate(
                    avg_value=Avg('value'),
                    max_value=Sum('value'),
                    count=Count('id')
                )

                report['metrics']['system_performance'] = {
                    'total_measurements': system_metrics.count(),
                    'by_metric': {
                        item['metric_type']: {
                            'avg': round(item['avg_value'], 2),
                            'max': round(item['max_value'], 2),
                            'count': item['count']
                        } for item in system_agg
                    }
                }

            # Métriques d'application
            if not metrics or 'app_metrics' in metrics:
                app_metrics = ApplicationMetric.objects.filter(
                    app__project__organization_id=organization_id,
                    created_at__range=[start_date, end_date]
                )

                # Applications actives
                active_apps = ApplicationMetric.objects.filter(
                    app__project__organization_id=organization_id,
                    metric_type='uptime',
                    created_at__gte=timezone.now() - timedelta(days=7)
                ).values('app').distinct().count()

                report['metrics']['app_metrics'] = {
                    'total_measurements': app_metrics.count(),
                    'active_apps': active_apps,
                    'total_apps': ApplicationMetric.objects.filter(
                        app__project__organization_id=organization_id
                    ).values('app').distinct().count()
                }

            return report

        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport d'analytics: {str(e)}")
            raise

    @staticmethod
    def generate_performance_report(app_id, start_date, end_date, metrics=None):
        """Génère un rapport de performance pour une application."""
        try:
            from apps.runtime.models import GeneratedApp

            app = GeneratedApp.objects.get(id=app_id)

            report = {
                'app_id': app_id,
                'app_name': app.name,
                'period': {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d')
                },
                'generated_at': timezone.now().isoformat(),
                'performance': {}
            }

            # Métriques de l'application
            app_metrics = ApplicationMetric.objects.filter(
                app_id=app_id,
                created_at__range=[start_date, end_date]
            )

            # Temps de réponse
            if not metrics or 'response_time' in metrics:
                response_times = app_metrics.filter(metric_type='response.time')
                if response_times.exists():
                    report['performance']['response_time'] = {
                        'avg': round(response_times.aggregate(Avg('value'))['value__avg'] or 0, 2),
                        'min': round(response_times.aggregate(Sum('value'))['value__min'] or 0, 2),
                        'max': round(response_times.aggregate(Sum('value'))['value__max'] or 0, 2),
                        'count': response_times.count()
                    }

            # Taux d'erreur
            if not metrics or 'error_rate' in metrics:
                error_metrics = app_metrics.filter(metric_type='errors.count')
                total_requests = app_metrics.filter(metric_type='requests.count').aggregate(
                    Sum('value')
                )['value__sum'] or 0

                total_errors = error_metrics.aggregate(Sum('value'))['value__sum'] or 0
                error_rate = (total_errors / total_requests) if total_requests > 0 else 0

                report['performance']['error_rate'] = round(error_rate, 4)

            # Disponibilité (uptime)
            if not metrics or 'uptime' in metrics:
                uptime_metrics = app_metrics.filter(metric_type='uptime')
                if uptime_metrics.exists():
                    avg_uptime = uptime_metrics.aggregate(Avg('value'))['value__avg'] or 0
                    report['performance']['uptime'] = round(avg_uptime, 4)

            # Requêtes par jour
            if not metrics or 'requests_per_day' in metrics:
                requests_per_day = app_metrics.filter(metric_type='requests.count').extra(
                    select={'day': 'DATE(created_at)'}
                ).values('day').annotate(total=Sum('value')).order_by('day')

                report['performance']['requests_per_day'] = {
                    item['day']: item['total'] for item in requests_per_day
                }

            return report

        except GeneratedApp.DoesNotExist:
            raise ValueError("Application non trouvée")
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport de performance: {str(e)}")
            raise

    @staticmethod
    def get_user_engagement_metrics(organization_id, days=30):
        """Calcule les métriques d'engagement utilisateur."""
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)

            # Utilisateurs actifs
            active_users = UserActivity.objects.filter(
                organization_id=organization_id,
                created_at__range=[start_date, end_date],
                user__isnull=False
            ).values('user').distinct().count()

            # Sessions totales
            total_sessions = UserActivity.objects.filter(
                organization_id=organization_id,
                created_at__range=[start_date, end_date],
                activity_type='user.login'
            ).count()

            # Actions par utilisateur
            actions_per_user = UserActivity.objects.filter(
                organization_id=organization_id,
                created_at__range=[start_date, end_date],
                user__isnull=False
            ).values('user').annotate(action_count=Count('id'))

            avg_actions = actions_per_user.aggregate(Avg('action_count'))['action_count__avg'] or 0

            return {
                'active_users': active_users,
                'total_sessions': total_sessions,
                'avg_actions_per_user': round(avg_actions, 2),
                'period_days': days
            }

        except Exception as e:
            logger.error(f"Erreur lors du calcul des métriques d'engagement: {str(e)}")
            return {}


class ActivityTracker:
    """Service de suivi automatique des activités utilisateur."""

    @staticmethod
    def track_user_action(user, action_type, description='', metadata=None, content_object=None, request=None):
        """Trace une action utilisateur."""
        try:
            activity_data = {
                'activity_type': action_type,
                'description': description,
                'metadata': metadata or {}
            }

            # Ajouter l'objet générique si fourni
            if content_object:
                activity_data['content_type'] = content_object._meta.label
                activity_data['object_id'] = content_object.id

            # Ajouter les informations de requête si fournies
            if request:
                activity_data['ip_address'] = request.META.get('REMOTE_ADDR')
                activity_data['user_agent'] = request.META.get('HTTP_USER_AGENT')

            # Créer l'activité
            UserActivity.objects.create(
                user=user,
                organization=user.organization if hasattr(user, 'organization') else None,
                **activity_data
            )

        except Exception as e:
            logger.error(f"Erreur lors du tracking d'activité utilisateur: {str(e)}")

    @staticmethod
    def track_login(user, request=None):
        """Trace une connexion utilisateur."""
        ActivityTracker.track_user_action(
            user=user,
            action_type='user.login',
            description=f'Connexion de {user.email}',
            request=request
        )

    @staticmethod
    def track_logout(user, request=None):
        """Trace une déconnexion utilisateur."""
        ActivityTracker.track_user_action(
            user=user,
            action_type='user.logout',
            description=f'Déconnexion de {user.email}',
            request=request
        )

    @staticmethod
    def track_project_action(user, project, action_type, request=None):
        """Trace une action sur un projet."""
        ActivityTracker.track_user_action(
            user=user,
            action_type=f'project.{action_type}',
            description=f'{action_type.title()} du projet {project.name}',
            content_object=project,
            request=request
        )

    @staticmethod
    def track_app_action(user, app, action_type, request=None):
        """Trace une action sur une application."""
        ActivityTracker.track_user_action(
            user=user,
            action_type=f'app.{action_type}',
            description=f'{action_type.title()} de l\'application {app.name}',
            content_object=app,
            request=request
        )
