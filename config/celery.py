
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('nocode_platform')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'cleanup-expired-sessions': {
        'task': 'apps.foundation.tasks.cleanup_expired_sessions',
        'schedule': crontab(minute=0),  
    },

    'generate-daily-analytics': {
        'task': 'apps.insights.tasks.generate_daily_analytics',
        'schedule': crontab(hour=2, minute=0),  
    },

    'health-check-deployed-apps': {
        'task': 'apps.runtime.tasks.health_check_apps',
        'schedule': crontab(minute='*/5'),  
    },

    'cleanup-old-logs': {
        'task': 'apps.insights.tasks.cleanup_old_logs',
        'schedule': crontab(hour=3, minute=0, day_of_week=1),  # Tous les lundis à 3h
    },

    'backup-metadata': {
        'task': 'apps.studio.tasks.backup_project_metadata',
        'schedule': crontab(hour=4, minute=0),  # Tous les jours à 4h
    },

    'update-performance-metrics': {
        'task': 'apps.insights.tasks.update_performance_metrics',
        'schedule': crontab(minute='*/10'),  # Toutes les 10 minutes
    },
}

app.conf.task_routes = {
    'apps.foundation.tasks.*': {'queue': 'critical'},
    'apps.runtime.tasks.deploy_app': {'queue': 'critical'},

    'apps.automation.tasks.*': {'queue': 'workflows'},

    'apps.runtime.tasks.generate_app_code': {'queue': 'heavy'},
    'apps.studio.tasks.backup_project_metadata': {'queue': 'heavy'},

    'apps.insights.tasks.*': {'queue': 'analytics'},

    '*': {'queue': 'default'},
}

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

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')