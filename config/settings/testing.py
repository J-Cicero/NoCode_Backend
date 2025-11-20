
from .base import *
from datetime import timedelta
import tempfile

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}


class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

MEDIA_ROOT = tempfile.mkdtemp()

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

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=10),
}

NOCODE_CONFIG.update({
    'MAX_TABLES_PER_PROJECT': 5,
    'MAX_FIELDS_PER_TABLE': 10,
    'MAX_PROJECTS_PER_ORG': 3,
    'GENERATED_APPS_DIR': tempfile.mkdtemp(),
    'AUTO_MIGRATE_GENERATED_APPS': False,
    'ENABLE_CODE_GENERATION_DEBUG': False,
    'ENABLE_WEBSOCKET_DEBUG': False,
})

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

STRIPE_PUBLIC_KEY = 'pk_test_12345'
STRIPE_SECRET_KEY = 'sk_test_12345'
STRIPE_WEBHOOK_SECRET = 'whsec_test_12345'
CORS_ALLOW_ALL_ORIGINS = True