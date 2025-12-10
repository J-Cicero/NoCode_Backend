# from .celery import app as celery_app  # Temporairement désactivé pour corriger le démarrage

# Ceci garantit que l'app Celery est importée quand Django démarre
__all__ = ()  # Temporairement vide