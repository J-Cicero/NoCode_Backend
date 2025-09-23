"""
Configuration de test pour le module Foundation.
"""
from django.test import override_settings

# Configuration de test pour les tests du module Foundation
TEST_SETTINGS = {
    'DATABASES': {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
    'USE_TZ': True,
    'SECRET_KEY': 'test-secret-key-for-foundation-module',
    'INSTALLED_APPS': [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'rest_framework',
        'rest_framework_simplejwt',
        'apps.foundation',
    ],
    'REST_FRAMEWORK': {
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'rest_framework_simplejwt.authentication.JWTAuthentication',
        ],
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.IsAuthenticated',
        ],
        'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    },
    'AUTH_USER_MODEL': 'foundation.User',
    'CELERY_TASK_ALWAYS_EAGER': True,
    'CELERY_TASK_EAGER_PROPAGATES': True,
    'EMAIL_BACKEND': 'django.core.mail.backends.locmem.EmailBackend',
    'STRIPE_PUBLISHABLE_KEY': 'pk_test_fake_key',
    'STRIPE_SECRET_KEY': 'sk_test_fake_key',
    'STRIPE_WEBHOOK_SECRET': 'whsec_test_fake_secret',
    'ENCRYPTION_KEY': 'test-encryption-key-32-chars-long',
    'FRONTEND_URL': 'http://localhost:3000',
}


def apply_test_settings():
    """
    Applique les paramètres de test.
    """
    return override_settings(**TEST_SETTINGS)
