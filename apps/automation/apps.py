from django.apps import AppConfig


class AutomationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.automation'
    
    def ready(self):
        """
        Importer les signaux Django quand l'application est prête.
        Django ne charge pas automatiquement les fichiers signals.py.
        """
        import apps.automation.signals
