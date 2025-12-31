import pytest

from apps.automation.models import Workflow, Trigger
from apps.foundation.models import User, Organization
from apps.studio.models import Project
from apps.foundation.services.event_bus import EventBus


@pytest.mark.django_db
def test_studio_event_triggers_workflow(mocker):
    # Patch Celery delay
    delay = mocker.patch('apps.automation.tasks.execute_workflow_async.delay')

    user = User.objects.create_user(
        email='event@test.com',
        password='pass',
        nom='Test',
        prenom='Event',
        is_active=True,
    )
    org = Organization.objects.create(name='Org', owner=user, is_active=True, is_verified=True)
    project = Project.objects.create(name='P', organization=org, schema_name='schema_evt', created_by=user)

    wf = Workflow.objects.create(name='WF', organization=org, created_by=user, project=project, status='ACTIVE')
    Trigger.objects.create(workflow=wf, trigger_type='event', event_type='studio.page.created', is_active=True)

    # Simule un événement studio
    EventBus.publish(
        event_name='studio.page.created',
        event_data={'page_id': '123', 'project_id': project.id},
        user=user,
        source_module='test',
    )

    assert delay.call_count == 1
    args, kwargs = delay.call_args
    assert kwargs['workflow_id'] == str(wf.id)
