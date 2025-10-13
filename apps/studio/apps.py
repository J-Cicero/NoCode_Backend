from django.apps import AppConfig


class StudioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.studio'
    verbose_name = 'Studio NoCode'

    def ready(self):
        import apps.studio.signals  # noqa
