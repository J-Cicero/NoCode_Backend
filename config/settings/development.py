"""
Configuration pour l'environnement de développement
"""
from .base import *

# Debug activé en développement
DEBUG = True

# Hosts autorisés en développement
ALLOWED_HOSTS = ['*']

# Base de données avec plus de verbosité
DATABASES['default']['OPTIONS'].update({
    'sslmode': 'disable',  # Pas de SSL en local
})

# Logging plus verbeux en dev
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['apps']['level'] = 'DEBUG'

# Email en console pour le développement
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CORS permissif en développement
CORS_ALLOW_ALL_ORIGINS = True

# Configuration Celery pour dev
CELERY_TASK_ALWAYS_EAGER = config('CELERY_ALWAYS_EAGER', default=False, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = True

# Tools de développement
if DEBUG:
    try:
        import debug_toolbar

        INSTALLED_APPS.append('debug_toolbar')
        MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

        DEBUG_TOOLBAR_CONFIG = {
            'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
            'SHOW_TEMPLATE_CONTEXT': True,
        }

        # IPs autorisées pour debug toolbar
        INTERNAL_IPS = [
            '127.0.0.1',
            'localhost',
        ]
    except ImportError:
        pass

# Configuration spécifique dev pour les apps générées
USANIDI_CONFIG.update({
    'AUTO_MIGRATE_GENERATED_APPS': True,
    'ENABLE_CODE_GENERATION_DEBUG': True,
    'ENABLE_WEBSOCKET_DEBUG': True,
})

# Désactiver les vérifications HTTPS en dev
SECURE_SSL_REDIRECT = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False