"""
Configuration pour l'environnement de test
"""
from .base import *
import tempfile

# Debug désactivé pour les tests
DEBUG = False

# Base de données en mémoire pour les tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}


# Désactiver les migrations pour accélérer les tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

# Password hashers simplifiés pour les tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Cache en mémoire pour les tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Configuration Celery pour tests (mode eager)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'

# Channels en mémoire pour les tests
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}

# Email en mémoire pour les tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Fichiers temporaires pour les tests
MEDIA_ROOT = tempfile.mkdtemp()

# Logging minimal pour les tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'propagate': False,
        },
        'apps': {
            'handlers': ['null'],
            'propagate': False,
        },
    },
}

# Configuration JWT simplifiée pour tests
SIMPLE_JWT.update({
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=10),
})

# Configuration spécifique test
NOCODE_CONFIG.update({
    'MAX_TABLES_PER_PROJECT': 5,
    'MAX_FIELDS_PER_TABLE': 10,
    'MAX_PROJECTS_PER_ORG': 3,
    'GENERATED_APPS_DIR': tempfile.mkdtemp(),
    'AUTO_MIGRATE_GENERATED_APPS': False,
    'ENABLE_CODE_GENERATION_DEBUG': False,
    'ENABLE_WEBSOCKET_DEBUG': False,
})

# Désactiver la sécurité pour les tests
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Configuration Stripe de test
STRIPE_PUBLIC_KEY = 'pk_test_12345'
STRIPE_SECRET_KEY = 'sk_test_12345'
STRIPE_WEBHOOK_SECRET = 'whsec_test_12345'

# Désactiver CORS pour les tests
CORS_ALLOW_ALL_ORIGINS = True