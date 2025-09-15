from .celery import app as celery_app

# Ceci garantit que l'app Celery est importée quand Django démarre
__all__ = ('celery_app',)