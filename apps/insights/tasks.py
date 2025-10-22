"""
Tâches Celery pour le module Insights.

Fournit les tâches asynchrones pour :
- Agrégation périodique des métriques
- Génération de rapports automatiques
- Nettoyage des données anciennes
- Collecte de métriques système
"""
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from celery import shared_task
from django.db.models import Count, Avg, Sum
from django.core.cache import cache

from .models import UserActivity, SystemMetric, ApplicationMetric, UserMetric
from .services import MetricsCollector, AnalyticsService

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def collect_system_metrics_task(self):
    """
    Tâche périodique pour collecter les métriques système.

    Cette tâche est exécutée régulièrement pour surveiller
    les performances du système.
    """
    try:
        logger.info("Début de la collecte des métriques système")

        # Collecter les métriques système
        MetricsCollector.collect_system_metrics()

        logger.info("Collecte des métriques système terminée avec succès")
        return {'status': 'success', 'message': 'Métriques système collectées'}

    except Exception as e:
        logger.error(f"Erreur lors de la collecte des métriques système: {str(e)}", exc_info=True)

        # Retry avec backoff exponentiel
        if self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)  # 1min, 2min, 4min
            raise self.retry(exc=e, countdown=countdown)

        return {
            'status': 'error',
            'message': f'Échec de la collecte après {self.max_retries} tentatives',
            'error': str(e)
        }

@shared_task(bind=True, max_retries=3)
def aggregate_daily_metrics_task(self, date_str=None):
    """
    Tâche pour agréger les métriques quotidiennes.

    Regroupe les métriques par jour pour améliorer les performances
    des requêtes d'analytics.
    """
    try:
        # Utiliser la date du jour si non spécifiée
        if date_str:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            target_date = timezone.now().date() - timedelta(days=1)  # Jour précédent

        logger.info(f"Agrégation des métriques pour le {target_date}")

        # Agréger les activités utilisateur par organisation et type
        activities = UserActivity.objects.filter(
            created_at__date=target_date
        ).values('organization', 'activity_type').annotate(count=Count('id'))

        for activity in activities:
            if activity['organization']:
                # Créer ou mettre à jour la métrique agrégée
                UserMetric.objects.update_or_create(
                    organization_id=activity['organization'],
                    metric_type=f"daily.{activity['activity_type']}",
                    date=target_date,
                    defaults={'value': activity['count']}
                )

        # Agréger les métriques système
        system_metrics = SystemMetric.objects.filter(
            created_at__date=target_date
        ).values('metric_type').annotate(
            avg_value=Avg('value'),
            count=Count('id')
        )

        # Stocker les métriques agrégées dans le cache pour accès rapide
        cache_key = f"daily_metrics_{target_date.strftime('%Y%m%d')}"
        cache_data = {
            'date': target_date,
            'activities_count': activities.count(),
            'system_metrics': {
                item['metric_type']: {
                    'avg': round(item['avg_value'], 2),
                    'count': item['count']
                } for item in system_metrics
            }
        }

        # Cache pour 7 jours
        cache.set(cache_key, cache_data, 7 * 24 * 3600)

        logger.info(f"Agrégation terminée pour {target_date}")
        return {'status': 'success', 'aggregated_records': len(activities)}

    except Exception as e:
        logger.error(f"Erreur lors de l'agrégation des métriques: {str(e)}", exc_info=True)

        if self.request.retries < self.max_retries:
            countdown = 300 * (2 ** self.request.retries)  # 5min, 10min, 20min
            raise self.retry(exc=e, countdown=countdown)

        return {
            'status': 'error',
            'message': f'Échec de l\'agrégation après {self.max_retries} tentatives',
            'error': str(e)
        }

@shared_task(bind=True, max_retries=3)
def generate_analytics_reports_task(self, organization_id=None):
    """
    Tâche pour générer automatiquement les rapports d'analytics.

    Génère des rapports périodiques pour toutes les organisations
    ou une organisation spécifique.
    """
    try:
        logger.info("Début de la génération des rapports d'analytics")

        # Déterminer les organisations à traiter
        if organization_id:
            from apps.foundation.models import Organization
            try:
                organization = Organization.objects.get(id=organization_id)
                organizations = [organization]
            except Organization.DoesNotExist:
                return {'status': 'error', 'message': 'Organisation non trouvée'}
        else:
            from apps.foundation.models import Organization
            organizations = Organization.objects.filter(is_active=True)

        reports_generated = 0

        for organization in organizations:
            try:
                # Générer le rapport pour les 30 derniers jours
                end_date = timezone.now().date()
                start_date = end_date - timedelta(days=30)

                report = AnalyticsService.generate_analytics_report(
                    organization_id=str(organization.id),
                    start_date=start_date,
                    end_date=end_date,
                    metrics=['user_activity', 'system_performance', 'app_metrics'],
                    group_by='day'
                )

                # Sauvegarder le rapport dans le cache
                cache_key = f"analytics_report_{organization.id}_{end_date.strftime('%Y%m%d')}"
                cache.set(cache_key, report, 24 * 3600)  # Cache pour 24h

                reports_generated += 1

            except Exception as e:
                logger.error(f"Erreur lors de la génération du rapport pour {organization.name}: {str(e)}")
                continue

        logger.info(f"Génération de rapports terminée: {reports_generated} rapports générés")
        return {
            'status': 'success',
            'reports_generated': reports_generated,
            'organizations_processed': len(organizations)
        }

    except Exception as e:
        logger.error(f"Erreur lors de la génération des rapports: {str(e)}", exc_info=True)

        if self.request.retries < self.max_retries:
            countdown = 600 * (2 ** self.request.retries)  # 10min, 20min, 40min
            raise self.retry(exc=e, countdown=countdown)

        return {
            'status': 'error',
            'message': f'Échec de la génération après {self.max_retries} tentatives',
            'error': str(e)
        }

@shared_task(bind=True, max_retries=3)
def cleanup_old_metrics_task(self, days_to_keep=90):
    """
    Tâche pour nettoyer les anciennes métriques.

    Supprime les données de métriques plus anciennes que
    la période de rétention spécifiée.
    """
    try:
        logger.info(f"Début du nettoyage des métriques (rétention: {days_to_keep} jours)")

        cutoff_date = timezone.now() - timedelta(days=days_to_keep)

        # Compter les enregistrements avant suppression
        activities_before = UserActivity.objects.filter(created_at__lt=cutoff_date).count()
        system_metrics_before = SystemMetric.objects.filter(created_at__lt=cutoff_date).count()
        app_metrics_before = ApplicationMetric.objects.filter(created_at__lt=cutoff_date).count()
        user_metrics_before = UserMetric.objects.filter(created_at__lt=cutoff_date).count()

        # Supprimer les anciennes données
        deleted_activities = UserActivity.objects.filter(created_at__lt=cutoff_date).delete()[0]
        deleted_system_metrics = SystemMetric.objects.filter(created_at__lt=cutoff_date).delete()[0]
        deleted_app_metrics = ApplicationMetric.objects.filter(created_at__lt=cutoff_date).delete()[0]
        deleted_user_metrics = UserMetric.objects.filter(created_at__lt=cutoff_date).delete()[0]

        logger.info(
            "Nettoyage terminé: "
            f"Activités={deleted_activities}, "
            f"Système={deleted_system_metrics}, "
            f"Apps={deleted_app_metrics}, "
            f"Utilisateurs={deleted_user_metrics}"
        )

        return {
            'status': 'success',
            'deleted_records': {
                'activities': deleted_activities,
                'system_metrics': deleted_system_metrics,
                'app_metrics': deleted_app_metrics,
                'user_metrics': deleted_user_metrics,
            },
            'retention_days': days_to_keep
        }

    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des métriques: {str(e)}", exc_info=True)

        if self.request.retries < self.max_retries:
            countdown = 3600 * (2 ** self.request.retries)  # 1h, 2h, 4h
            raise self.retry(exc=e, countdown=countdown)

        return {
            'status': 'error',
            'message': f'Échec du nettoyage après {self.max_retries} tentatives',
            'error': str(e)
        }

@shared_task(bind=True, max_retries=3)
def collect_application_performance_task(self, app_id=None):
    """
    Tâche pour collecter les métriques de performance des applications.

    Cette tâche peut être déclenchée après le déploiement
    ou exécutée périodiquement pour surveiller les performances.
    """
    try:
        logger.info("Début de la collecte des métriques d'application")

        from apps.runtime.models import GeneratedApp

        # Si un app_id spécifique est fourni
        if app_id:
            try:
                app = GeneratedApp.objects.get(id=app_id)
                apps = [app]
            except GeneratedApp.DoesNotExist:
                return {'status': 'error', 'message': 'Application non trouvée'}
        else:
            # Toutes les applications actives
            apps = GeneratedApp.objects.filter(status='deployed')

        collected_metrics = 0

        for app in apps:
            try:
                # Collecter les métriques de base
                metrics_data = {
                    'response.time': {
                        'value': 200 + (hash(app.name) % 100),  # Simulation
                        'unit': 'ms'
                    },
                    'requests.count': {
                        'value': 100 + (hash(app.name) % 50),  # Simulation
                        'unit': 'count'
                    },
                    'errors.count': {
                        'value': (hash(app.name) % 10),  # Simulation
                        'unit': 'count'
                    },
                    'uptime': {
                        'value': 95 + (hash(app.name) % 5),  # Simulation
                        'unit': '%'
                    }
                }

                MetricsCollector.collect_application_metrics(app, metrics_data)
                collected_metrics += len(metrics_data)

            except Exception as e:
                logger.error(f"Erreur lors de la collecte des métriques pour {app.name}: {str(e)}")
                continue

        logger.info(f"Collecte des métriques d'application terminée: {collected_metrics} métriques collectées")
        return {
            'status': 'success',
            'apps_processed': len(apps),
            'metrics_collected': collected_metrics
        }

    except Exception as e:
        logger.error(f"Erreur lors de la collecte des métriques d'application: {str(e)}", exc_info=True)

        if self.request.retries < self.max_retries:
            countdown = 300 * (2 ** self.request.retries)  # 5min, 10min, 20min
            raise self.retry(exc=e, countdown=countdown)

        return {
            'status': 'error',
            'message': f'Échec de la collecte après {self.max_retries} tentatives',
            'error': str(e)
        }


def start_periodic_tasks():
    """
    Démarre les tâches périodiques lors du lancement de l'application.

    Cette fonction est appelée dans apps.py pour démarrer
    les tâches récurrentes.
    """
    try:
        # Démarrer la collecte de métriques système toutes les 5 minutes
        collect_system_metrics_task.apply_async(
            countdown=300,  # Démarrer dans 5 minutes
            expires=3600    # Expirer après 1 heure
        )

        # Démarrer l'agrégation quotidienne à minuit
        from datetime import time
        midnight = time(0, 0, 0)
        # Calculer le temps jusqu'à minuit prochain
        now = timezone.now()
        midnight_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if now > midnight_today:
            midnight_tomorrow = midnight_today + timedelta(days=1)
        else:
            midnight_tomorrow = midnight_today

        countdown_to_midnight = (midnight_tomorrow - now).total_seconds()

        aggregate_daily_metrics_task.apply_async(
            countdown=countdown_to_midnight,
            expires=86400  # Expirer après 24h
        )

        logger.info("Tâches périodiques Insights démarrées")

    except Exception as e:
        logger.error(f"Erreur lors du démarrage des tâches périodiques: {str(e)}")
