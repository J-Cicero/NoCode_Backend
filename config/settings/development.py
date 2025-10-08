"""
Configuration pour l'environnement de développement
"""
from .base import *

# Debug activé en développement
DEBUG = True

# Hosts autorisés en développement
ALLOWED_HOSTS = ['*']

# Configuration de la base de données pour le développement
DATABASES['default'].update({
    'OPTIONS': {
        'sslmode': 'disable',  # Pas de SSL en local
    }
})

# Configuration des logs pour le développement
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Email en console pour le développement
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CORS permissif en développement
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# CSRF - Configuration permissive pour le développement
CSRF_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Session cookies
SESSION_COOKIE_SECURE = False

# Configuration pour le debug toolbar
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]
NOCODE_CONFIG.update({
    'AUTO_MIGRATE_GENERATED_APPS': True,
    'ENABLE_CODE_GENERATION_DEBUG': True,
    'ENABLE_WEBSOCKET_DEBUG': True,
})
# Désactiver les vérifications HTTPS en dev
SECURE_SSL_REDIRECT = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False