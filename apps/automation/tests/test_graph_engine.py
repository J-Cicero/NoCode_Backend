import pytest

from apps.automation.models import Workflow, Node, Edge
from apps.automation.services.workflow_engine import WorkflowEngine
from apps.foundation.models import Organization, User


@pytest.mark.django_db
def test_graph_condition_routes_true_branch(mocker):
    # Patch pour éviter d’exécuter de vraies actions (email/http/sql)
    execute_action = mocker.patch(
        'apps.automation.services.workflow_engine.ActionExecutor.execute_action',
        autospec=True,
        side_effect=lambda self, action_type, params, integration=None, context=None: {
            'success': True,
            'action_type': action_type,
            'params': params,
        },
    )

    user = User.objects.create_user(
        email='user@test.com',
        password='pass',
        nom='Test',
        prenom='User',
        is_active=True,
    )
    org = Organization.objects.create(name='Org', owner=user, is_active=True, is_verified=True)

    wf = Workflow.objects.create(
        name='WF',
        organization=org,
        created_by=user,
        status='ACTIVE',
    )

    trigger = Node.objects.create(workflow=wf, node_id='n_trigger', node_type='trigger', label='Trigger')
    cond = Node.objects.create(
        workflow=wf,
        node_id='n_cond',
        node_type='condition',
        label='Cond',
        config={'condition': {'field': 'input.price', 'operator': '>', 'value': 100}},
    )
    yes = Node.objects.create(
        workflow=wf,
        node_id='n_yes',
        node_type='action',
        label='Yes',
        config={'action_type': 'transform_data', 'params': {'data': {'tier': 'vip'}}},
    )
    no = Node.objects.create(
        workflow=wf,
        node_id='n_no',
        node_type='action',
        label='No',
        config={'action_type': 'transform_data', 'params': {'data': {'tier': 'normal'}}},
    )

    Edge.objects.create(workflow=wf, source_node=trigger, target_node=cond, source_port='output', target_port='input')
    Edge.objects.create(workflow=wf, source_node=cond, target_node=yes, source_port='true', target_port='input')
    Edge.objects.create(workflow=wf, source_node=cond, target_node=no, source_port='false', target_port='input')

    engine = WorkflowEngine(wf)
    execution = engine.execute(input_data={'price': 150}, triggered_by=user)

    assert execution.status == 'completed'
    assert engine.context['steps']['n_cond']['condition_result'] is True

    # yes/no nodes: only one action node should have been executed based on routing
    executed_action_nodes = [k for k in engine.context['steps'].keys() if k in {'n_yes', 'n_no'}]
    assert executed_action_nodes == ['n_yes']

    assert execute_action.call_count == 1


@pytest.mark.django_db
def test_graph_condition_routes_false_branch(mocker):
    mocker.patch(
        'apps.automation.services.workflow_engine.ActionExecutor.execute_action',
        autospec=True,
        side_effect=lambda self, action_type, params, integration=None, context=None: {
            'success': True,
            'action_type': action_type,
            'params': params,
        },
    )

    user = User.objects.create_user(
        email='user2@test.com',
        password='pass',
        nom='Test',
        prenom='User',
        is_active=True,
    )
    org = Organization.objects.create(name='Org2', owner=user, is_active=True, is_verified=True)

    wf = Workflow.objects.create(
        name='WF2',
        organization=org,
        created_by=user,
        status='ACTIVE',
    )

    trigger = Node.objects.create(workflow=wf, node_id='t', node_type='trigger', label='Trigger')
    cond = Node.objects.create(
        workflow=wf,
        node_id='c',
        node_type='condition',
        label='Cond',
        config={'condition': {'field': 'input.price', 'operator': '>', 'value': 100}},
    )
    yes = Node.objects.create(
        workflow=wf,
        node_id='y',
        node_type='action',
        label='Yes',
        config={'action_type': 'transform_data', 'params': {'data': {'tier': 'vip'}}},
    )
    no = Node.objects.create(
        workflow=wf,
        node_id='n',
        node_type='action',
        label='No',
        config={'action_type': 'transform_data', 'params': {'data': {'tier': 'normal'}}},
    )

    Edge.objects.create(workflow=wf, source_node=trigger, target_node=cond)
    Edge.objects.create(workflow=wf, source_node=cond, target_node=yes, source_port='true')
    Edge.objects.create(workflow=wf, source_node=cond, target_node=no, source_port='false')

    engine = WorkflowEngine(wf)
    execution = engine.execute(input_data={'price': 50}, triggered_by=user)

    assert execution.status == 'completed'
    assert engine.context['steps']['c']['condition_result'] is False

    executed_action_nodes = [k for k in engine.context['steps'].keys() if k in {'y', 'n'}]
    assert executed_action_nodes == ['n']
