from django.apps import AppConfig


class AutomationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.automation'

    def ready(self):
        """Initialisation de l'app automation.

        - Charge les signaux Django.
        - S'abonne aux événements Studio via EventBus pour déclencher les workflows.
        """
        import apps.automation.signals  # noqa: F401

        # Abonnement aux événements Studio (NoCode builder)
        from apps.foundation.services.event_bus import EventBus

        def _studio_event_handler(payload):
            """Déclenche les workflows automation liés à un event Studio."""
            from .models import Trigger
            from .tasks import execute_workflow_async

            event_name = payload.get('event_name')
            event_data = payload.get('event_data') or payload.get('data') or {}
            user_id = payload.get('user_id')

            if not event_name:
                return

            triggers = Trigger.objects.select_related('workflow').filter(
                trigger_type='event',
                is_active=True,
                event_type=event_name,
                workflow__status='ACTIVE',
            )

            for trigger in triggers:
                execute_workflow_async.delay(
                    workflow_id=str(trigger.workflow.id),
                    input_data={
                        'event_name': event_name,
                        'event_data': event_data,
                        'trigger_id': str(trigger.id),
                    },
                    user_id=user_id,
                )

        # EventBus ne supporte pas le wildcard: on s'abonne explicitement.
        for _evt in (
            'studio.page.created',
            'studio.page.updated',
            'studio.page.deleted',
            'studio.component_instance.created',
            'studio.component_instance.updated',
            'studio.component_instance.deleted',
        ):
            EventBus.subscribe(_evt, _studio_event_handler)

