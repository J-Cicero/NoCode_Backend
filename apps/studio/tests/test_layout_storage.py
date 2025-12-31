import pytest

from apps.studio.models import Project, Page, Component, ComponentInstance
from apps.foundation.models import User, Organization
from apps.studio.serializers import ComponentInstanceSerializer


@pytest.mark.django_db
def test_component_instance_layout_fields_serialized():
    user = User.objects.create_user(
        email='layout@test.com',
        password='pass',
        nom='Test',
        prenom='Layout',
        is_active=True,
    )
    org = Organization.objects.create(name='Org', owner=user, is_active=True, is_verified=True)

    project = Project.objects.create(name='P', organization=org, schema_name='schema_p', created_by=user)
    page = Page.objects.create(project=project, name='Home', route='/')

    comp = Component.objects.create(name='container', display_name='Container')
    child_comp = Component.objects.create(name='text', display_name='Text')

    parent = ComponentInstance.objects.create(
        page=page,
        component=comp,
        position={'x': 0, 'y': 0, 'w': 12, 'h': 6},
        config={'bg': 'white'},
    )
    child = ComponentInstance.objects.create(
        page=page,
        component=child_comp,
        parent=parent,
        slot='content',
        position={'x': 1, 'y': 1, 'w': 6, 'h': 1},
        config={'text': 'Hello'},
    )

    data = ComponentInstanceSerializer(child).data
    assert data['parent'] == parent.id
    assert data['slot'] == 'content'
    assert data['position']['w'] == 6
