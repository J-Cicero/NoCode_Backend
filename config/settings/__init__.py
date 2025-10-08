
from decouple import config

# Déterminer l'environnement
ENVIRONMENT = config('ENVIRONMENT', default='development')

# Importer la configuration appropriée
if ENVIRONMENT == 'production':
    from config.settings.production import *
elif ENVIRONMENT == 'testing':
    from config.settings.testing import *
else:
    from config.settings.development import *