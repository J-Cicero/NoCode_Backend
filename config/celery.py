"""
Configuration Celery pour la plateforme NoCode
"""
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Définir le module de settings Django par défaut
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Créer l'instance Celery
app = Celery('nocode_platform')

# Configuration à partir des settings Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-découverte des tâches dans toutes les apps installées
app.autodiscover_tasks()

# Configuration des tâches périodiques
app.conf.beat_schedule = {
    # Nettoyage des sessions expirées toutes les heures
    'cleanup-expired-sessions': {
        'task': 'apps.foundation.tasks.cleanup_expired_sessions',
        'schedule': crontab(minute=0),  # Toutes les heures
    },

    # Génération des rapports analytics quotidiens
    'generate-daily-analytics': {
        'task': 'apps.insights.tasks.generate_daily_analytics',
        'schedule': crontab(hour=2, minute=0),  # Tous les jours à 2h
    },

    # Vérification de l'état des applications déployées
    'health-check-deployed-apps': {
        'task': 'apps.runtime.tasks.health_check_apps',
        'schedule': crontab(minute='*/5'),  # Toutes les 5 minutes
    },

    # Nettoyage des logs anciens
    'cleanup-old-logs': {
        'task': 'apps.insights.tasks.cleanup_old_logs',
        'schedule': crontab(hour=3, minute=0, day_of_week=1),  # Tous les lundis à 3h
    },

    # Backup automatique des métadonnées importantes
    'backup-metadata': {
        'task': 'apps.studio.tasks.backup_project_metadata',
        'schedule': crontab(hour=4, minute=0),  # Tous les jours à 4h
    },

    # Mise à jour des métriques de performance
    'update-performance-metrics': {
        'task': 'apps.insights.tasks.update_performance_metrics',
        'schedule': crontab(minute='*/10'),  # Toutes les 10 minutes
    },
}

# Configuration des queues
app.conf.task_routes = {
    # Queue haute priorité pour les tâches critiques
    'apps.foundation.tasks.*': {'queue': 'critical'},
    'apps.runtime.tasks.deploy_app': {'queue': 'critical'},

    # Queue normale pour les workflows
    'apps.automation.tasks.*': {'queue': 'workflows'},

    # Queue longue pour les tâches lourdes
    'apps.runtime.tasks.generate_app_code': {'queue': 'heavy'},
    'apps.studio.tasks.backup_project_metadata': {'queue': 'heavy'},

    # Queue analytics pour les tâches de reporting
    'apps.insights.tasks.*': {'queue': 'analytics'},

    # Queue par défaut pour tout le reste
    '*': {'queue': 'default'},
}

# Configuration des limites de retry
app.conf.task_annotations = {
    'apps.runtime.tasks.deploy_app': {
        'rate_limit': '10/m',
        'max_retries': 3,
    },
    'apps.automation.tasks.execute_workflow': {
        'rate_limit': '50/m',
        'max_retries': 5,
    },
    'apps.foundation.tasks.send_notification_email': {
        'rate_limit': '100/m',
        'max_retries': 3,
    },
}

# Signal de démarrage pour initialiser les connexions
@app.task(bind=True)
def debug_task(self):
    """Tâche de debug pour vérifier la configuration Celery"""
    print(f'Request: {self.request!r}')