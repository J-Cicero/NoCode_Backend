"""
Configuration des settings Django

Ce module importe automatiquement la bonne configuration
selon la variable d'environnement DJANGO_SETTINGS_MODULE
"""
import os
from decouple import config

# Déterminer l'environnement
ENVIRONMENT = config('ENVIRONMENT', default='development')

# Importer la configuration appropriée
if ENVIRONMENT == 'production':
    from .production import *
elif ENVIRONMENT == 'testing':
    from .testing import *
else:
    from .development import *