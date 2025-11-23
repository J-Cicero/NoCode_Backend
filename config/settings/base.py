
import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', 
                      cast=lambda v: [s.strip() for s in v.split(',')])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    'channels',
    
    'apps.foundation',
    'apps.studio',
    'apps.runtime',
    'apps.insights',
    'apps.automation',
]

# Configuration CORS pour permettre les requêtes depuis les fichiers locaux
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "null",  # Pour les fichiers locaux file://
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',


]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

ROOT_URLCONF = 'config.urls'

SPECTACULAR_SETTINGS = {
    'TITLE': 'NoCode Platform API',
    'DESCRIPTION': 'API pour la plateforme NoCode',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': r'/api/v[0-9]',
    'SCHEMA_PATH_PREFIX_TRIM': True,
    'TAGS_SORTER': 'alpha',
   'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
    'PREPROCESSING_HOOKS': [
        'drf_spectacular.hooks.preprocess_exclude_path_format',
    ],
    'ENUM_NAME_OVERRIDES': {
        'FieldType': [
            'string', 'text', 'integer', 'float', 'boolean', 'date', 'datetime', 'json'
        ],
    },
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # 'rest_framework_simplejwt.authentication.JWTAuthentication',
        # 'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        # 'rest_framework.permissions.IsAuthenticated',
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S%z',
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'nocode',
        'USER': 'nocode_user',
        'PASSWORD':'cicero',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Internationalisation
LANGUAGE_CODE = 'fr'
TIME_ZONE = 'UTC'
USE_TZ = True

# Fichiers statiques
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SITE_ID = 1

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

NOCODE_CONFIG = {
    'MAX_TABLES_PER_PROJECT': config('MAX_TABLES_PER_PROJECT', default=50, cast=int),
    'MAX_FIELDS_PER_TABLE': config('MAX_FIELDS_PER_TABLE', default=100, cast=int),
    'MAX_PROJECTS_PER_ORG': config('MAX_PROJECTS_PER_ORG', default=10, cast=int),
    'GENERATED_APPS_DIR': BASE_DIR / 'generated_apps',
    'DOCKER_REGISTRY': config('DOCKER_REGISTRY', default='localhost:5000'),
    'KUBERNETES_NAMESPACE': config('KUBERNETES_NAMESPACE', default='nocode'),
    'DEFAULT_SUBDOMAIN': config('DEFAULT_SUBDOMAIN', default='app.nocode.local'),
}

os.makedirs(BASE_DIR / 'logs', exist_ok=True)
os.makedirs(NOCODE_CONFIG['GENERATED_APPS_DIR'], exist_ok=True)

AUTH_USER_MODEL = 'foundation.User'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER or 'noreply@example.com'

SUPPORT_EMAIL = config('SUPPORT_EMAIL', default=DEFAULT_FROM_EMAIL)
SITE_NAME = config('SITE_NAME', default='NoCode Platform')
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')