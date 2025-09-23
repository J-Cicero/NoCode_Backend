"""
Configuration de développement pour le module Foundation.
Permet les tests avec Postman et autres outils de développement.
"""
from django.conf import settings

# Configuration pour le développement
DEVELOPMENT_SETTINGS = {
    # CORS - Autoriser toutes les origines en développement
    'CORS_ALLOW_ALL_ORIGINS': True,
    'CORS_ALLOWED_ORIGINS': [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    'CORS_ALLOW_CREDENTIALS': True,
    'CORS_ALLOW_HEADERS': [
        'accept',
        'accept-encoding',
        'authorization',
        'content-type',
        'dnt',
        'origin',
        'user-agent',
        'x-csrftoken',
        'x-requested-with',
        'x-api-key',
        'stripe-signature',
    ],
    
    # CSRF - Désactiver en développement pour les tests API
    'CSRF_COOKIE_SECURE': False,
    'CSRF_COOKIE_HTTPONLY': False,
    'CSRF_USE_SESSIONS': False,
    'CSRF_TRUSTED_ORIGINS': [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    
    # Session
    'SESSION_COOKIE_SECURE': False,
    'SESSION_COOKIE_HTTPONLY': False,
    
    # Debug
    'DEBUG': True,
    'ALLOWED_HOSTS': ['*'],
    
    # Rate Limiting - Plus permissif en développement
    'RATE_LIMIT_REQUESTS_PER_MINUTE': 1000,
    'RATE_LIMIT_BURST_SIZE': 100,
    
    # JWT - Tokens plus longs en développement
    'JWT_ACCESS_TOKEN_LIFETIME_MINUTES': 60,  # 1 heure
    'JWT_REFRESH_TOKEN_LIFETIME_DAYS': 30,    # 30 jours
    
    # Email - Backend console pour les tests
    'EMAIL_BACKEND': 'django.core.mail.backends.console.EmailBackend',
    
    # Logging plus verbeux
    'LOG_LEVEL': 'DEBUG',
}

def apply_development_settings():
    """
    Applique les paramètres de développement.
    """
    for key, value in DEVELOPMENT_SETTINGS.items():
        setattr(settings, key, value)
