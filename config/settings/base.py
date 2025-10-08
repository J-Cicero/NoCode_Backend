"""
Configuration de base pour l'application Django
"""
import os
from pathlib import Path
from decouple import config

# Chemins du projet
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Clé secrète
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

# Mode debug
DEBUG = config('DEBUG', default=True, cast=bool)

# Hôtes autorisés
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', 
                      cast=lambda v: [s.strip() for s in v.split(',')])

# Applications installées
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
    'apps.foundation',
    'apps.studio',
]

# Middleware
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

# Configuration des URLs
ROOT_URLCONF = 'config.urls'

# Configuration de drf-spectacular
SPECTACULAR_SETTINGS = {
    'TITLE': 'NoCode Platform API',
    'DESCRIPTION': 'API pour la plateforme NoCode',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': r'/api/v[0-9]',
    'SCHEMA_PATH_PREFIX_TRIM': True,
    'TAGS_SORTER': 'alpha',
    'SERVE_PERMISSIONS': ['rest_framework.permissions.IsAuthenticated'],
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

# Configuration de DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S%z',
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

# Configuration de la base de données
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'nocode_platform',
        'USER': 'postgres',
        'PASSWORD': 'cicero',
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

# Configuration des logs
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

# Configuration par défaut des champs
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuration des sites Django
SITE_ID = 1

# Sécurité
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Configuration plateforme NoCode spécifique
NOCODE_CONFIG = {
    'MAX_TABLES_PER_PROJECT': config('MAX_TABLES_PER_PROJECT', default=50, cast=int),
    'MAX_FIELDS_PER_TABLE': config('MAX_FIELDS_PER_TABLE', default=100, cast=int),
    'MAX_PROJECTS_PER_ORG': config('MAX_PROJECTS_PER_ORG', default=10, cast=int),
    'GENERATED_APPS_DIR': BASE_DIR / 'generated_apps',
    'DOCKER_REGISTRY': config('DOCKER_REGISTRY', default='localhost:5000'),
    'KUBERNETES_NAMESPACE': config('KUBERNETES_NAMESPACE', default='nocode'),
    'DEFAULT_SUBDOMAIN': config('DEFAULT_SUBDOMAIN', default='app.nocode.local'),
}

# Créer les dossiers nécessaires
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
os.makedirs(NOCODE_CONFIG['GENERATED_APPS_DIR'], exist_ok=True)

# Modèle utilisateur personnalisé
AUTH_USER_MODEL = 'foundation.User'