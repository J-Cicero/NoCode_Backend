
from .base import *

print(f"🔍 SETTINGS LOADED: {__file__}")  # Debug pour vérifier quel settings est utilisé

DEBUG = True

ALLOWED_HOSTS = ['*']

# Désactiver la redirection SSL en développement
SECURE_SSL_REDIRECT = False
print(f"🔍 SECURE_SSL_REDIRECT: {SECURE_SSL_REDIRECT}")  # Debug pour vérifier la valeur

SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

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

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

CSRF_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

SESSION_COOKIE_SECURE = False

INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]


CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'


CELERY_BEAT_SCHEDULER = None

NOCODE_CONFIG.update({
    'AUTO_MIGRATE_GENERATED_APPS': True,
    'ENABLE_CODE_GENERATION_DEBUG': True,
    'ENABLE_WEBSOCKET_DEBUG': True,
})

SECURE_SSL_REDIRECT = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False