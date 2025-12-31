"""
Tests pour les nodes et edges (système de graphe)
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.foundation.models import User, Organization
from apps.studio.models import Project
from apps.automation.models import Workflow, Node, Edge


@pytest.mark.django_db
class TestNodeCRUD:
    """Tests CRUD des nodes"""
    
    def setup_method(self):
        """Setup exécuté avant chaque test"""
        self.client = APIClient()
        
        self.org = Organization.objects.create(name='Test Organization')
        
        self.owner = User.objects.create_user(
            email='owner@test.com',
            password='Pass123!',
            first_name='Owner',
            last_name='User',
            role='OWNER',
            organization=self.org
        )
        
        self.project = Project.objects.create(
            name='Test Project',
            organization=self.org,
            created_by=self.owner
        )
        
        self.workflow = Workflow.objects.create(
            name='Test Workflow',
            organization=self.org,
            project=self.project
        )
        
    def test_create_trigger_node(self):
        """Test création d'un node trigger"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('automation:node-create', kwargs={'workflow_id': self.workflow.id})
        data = {
            'node_id': 'trigger_1',
            'node_type': 'trigger',
            'label': 'Webhook Trigger',
            'position_x': 100,
            'position_y': 100,
            'config': {'event_type': 'webhook', 'path': '/trigger'}
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['node_type'] == 'trigger'
        assert Node.objects.filter(node_id='trigger_1').exists()
        
    def test_create_action_node(self):
        """Test création d'un node action"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('automation:node-create', kwargs={'workflow_id': self.workflow.id})
        data = {
            'node_id': 'action_1',
            'node_type': 'action',
            'label': 'Send Email',
            'position_x': 300,
            'position_y': 100,
            'config': {
                'action': 'send_email',
                'to': '{{user.email}}',
                'subject': 'Test'
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['node_type'] == 'action'
        
    def test_create_condition_node(self):
        """Test création d'un node condition"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('automation:node-create', kwargs={'workflow_id': self.workflow.id})
        data = {
            'node_id': 'condition_1',
            'node_type': 'condition',
            'label': 'Check Age',
            'position_x': 200,
            'position_y': 100,
            'config': {
                'condition': '{{user.age}} > 18',
                'operator': 'greater_than',
                'value': 18
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['node_type'] == 'condition'
        
    def test_update_node_position(self):
        """Test modification de la position d'un node"""
        node = Node.objects.create(
            workflow=self.workflow,
            node_id='node_1',
            node_type='action',
            label='Test Node',
            position_x=100,
            position_y=100
        )
        
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('automation:node-detail', kwargs={
            'workflow_id': self.workflow.id,
            'pk': node.id
        })
        data = {
            'position_x': 200,
            'position_y': 200
        }
        
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['position_x'] == 200
        assert response.data['position_y'] == 200
        
    def test_update_node_config(self):
        """Test modification de la configuration d'un node"""
        node = Node.objects.create(
            workflow=self.workflow,
            node_id='node_1',
            node_type='action',
            label='Test Node',
            position_x=100,
            position_y=100,
            config={'key': 'old_value'}
        )
        
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('automation:node-detail', kwargs={
            'workflow_id': self.workflow.id,
            'pk': node.id
        })
        data = {
            'config': {'key': 'new_value', 'new_key': 'new_data'}
        }
        
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['config']['key'] == 'new_value'
        
    def test_delete_node(self):
        """Test suppression d'un node"""
        node = Node.objects.create(
            workflow=self.workflow,
            node_id='node_1',
            node_type='action',
            label='Test Node',
            position_x=100,
            position_y=100
        )
        
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('automation:node-detail', kwargs={
            'workflow_id': self.workflow.id,
            'pk': node.id
        })
        response = self.client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Node.objects.filter(id=node.id).exists()


@pytest.mark.django_db
class TestEdgeCRUD:
    """Tests CRUD des edges (connexions)"""
    
    def setup_method(self):
        """Setup exécuté avant chaque test"""
        self.client = APIClient()
        
        self.org = Organization.objects.create(name='Test Organization')
        
        self.owner = User.objects.create_user(
            email='owner@test.com',
            password='Pass123!',
            first_name='Owner',
            last_name='User',
            role='OWNER',
            organization=self.org
        )
        
        self.project = Project.objects.create(
            name='Test Project',
            organization=self.org,
            created_by=self.owner
        )
        
        self.workflow = Workflow.objects.create(
            name='Test Workflow',
            organization=self.org,
            project=self.project
        )
        
        self.source_node = Node.objects.create(
            workflow=self.workflow,
            node_id='source_1',
            node_type='trigger',
            label='Source',
            position_x=100,
            position_y=100
        )
        
        self.target_node = Node.objects.create(
            workflow=self.workflow,
            node_id='target_1',
            node_type='action',
            label='Target',
            position_x=300,
            position_y=100
        )
        
    def test_create_edge(self):
        """Test création d'une connexion entre nodes"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('automation:edge-create', kwargs={'workflow_id': self.workflow.id})
        data = {
            'source_node_id': self.source_node.id,
            'target_node_id': self.target_node.id,
            'source_port': 'output',
            'target_port': 'input'
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Edge.objects.filter(
            source_node=self.source_node,
            target_node=self.target_node
        ).exists()
        
    def test_create_edge_with_condition_ports(self):
        """Test création edge avec ports success/error"""
        condition_node = Node.objects.create(
            workflow=self.workflow,
            node_id='condition_1',
            node_type='condition',
            label='Condition',
            position_x=200,
            position_y=100
        )
        
        success_node = Node.objects.create(
            workflow=self.workflow,
            node_id='success_1',
            node_type='action',
            label='Success Action',
            position_x=300,
            position_y=50
        )
        
        error_node = Node.objects.create(
            workflow=self.workflow,
            node_id='error_1',
            node_type='action',
            label='Error Action',
            position_x=300,
            position_y=150
        )
        
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('automation:edge-create', kwargs={'workflow_id': self.workflow.id})
        
        success_data = {
            'source_node_id': condition_node.id,
            'target_node_id': success_node.id,
            'source_port': 'success',
            'target_port': 'input'
        }
        response1 = self.client.post(url, success_data, format='json')
        
        error_data = {
            'source_node_id': condition_node.id,
            'target_node_id': error_node.id,
            'source_port': 'error',
            'target_port': 'input'
        }
        response2 = self.client.post(url, error_data, format='json')
        
        assert response1.status_code == status.HTTP_201_CREATED
        assert response2.status_code == status.HTTP_201_CREATED
        assert Edge.objects.filter(source_node=condition_node).count() == 2
        
    def test_delete_edge(self):
        """Test suppression d'une connexion"""
        edge = Edge.objects.create(
            workflow=self.workflow,
            source_node=self.source_node,
            target_node=self.target_node
        )
        
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('automation:edge-detail', kwargs={
            'workflow_id': self.workflow.id,
            'pk': edge.id
        })
        response = self.client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Edge.objects.filter(id=edge.id).exists()
        
    def test_prevent_circular_edges(self):
        """Test prévention des boucles infinies"""
        Edge.objects.create(
            workflow=self.workflow,
            source_node=self.source_node,
            target_node=self.target_node
        )
        
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('automation:edge-create', kwargs={'workflow_id': self.workflow.id})
        data = {
            'source_node_id': self.target_node.id,
            'target_node_id': self.source_node.id
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestNodeTypes:
    """Tests des différents types de nodes"""
    
    def setup_method(self):
        """Setup exécuté avant chaque test"""
        self.client = APIClient()
        
        self.org = Organization.objects.create(name='Test Organization')
        
        self.owner = User.objects.create_user(
            email='owner@test.com',
            password='Pass123!',
            first_name='Owner',
            last_name='User',
            role='OWNER',
            organization=self.org
        )
        
        self.project = Project.objects.create(
            name='Test Project',
            organization=self.org,
            created_by=self.owner
        )
        
        self.workflow = Workflow.objects.create(
            name='Test Workflow',
            organization=self.org,
            project=self.project
        )
        
    def test_create_math_node(self):
        """Test création node mathématique"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('automation:node-create', kwargs={'workflow_id': self.workflow.id})
        data = {
            'node_id': 'math_1',
            'node_type': 'math',
            'label': 'Calculate Total',
            'position_x': 200,
            'position_y': 100,
            'config': {
                'operation': 'add',
                'operands': ['{{price}}', '{{tax}}']
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        
    def test_create_string_node(self):
        """Test création node manipulation de texte"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('automation:node-create', kwargs={'workflow_id': self.workflow.id})
        data = {
            'node_id': 'string_1',
            'node_type': 'string',
            'label': 'Format Name',
            'position_x': 200,
            'position_y': 100,
            'config': {
                'operation': 'concat',
                'parts': ['{{first_name}}', ' ', '{{last_name}}']
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        
    def test_create_api_node(self):
        """Test création node appel API"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('automation:node-create', kwargs={'workflow_id': self.workflow.id})
        data = {
            'node_id': 'api_1',
            'node_type': 'api',
            'label': 'Call External API',
            'position_x': 200,
            'position_y': 100,
            'config': {
                'method': 'POST',
                'url': 'https://api.example.com/endpoint',
                'headers': {'Authorization': 'Bearer token'},
                'body': {'key': '{{value}}'}
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        
    def test_create_delay_node(self):
        """Test création node temporisation"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('automation:node-create', kwargs={'workflow_id': self.workflow.id})
        data = {
            'node_id': 'delay_1',
            'node_type': 'delay',
            'label': 'Wait 5 seconds',
            'position_x': 200,
            'position_y': 100,
            'config': {
                'duration': 5,
                'unit': 'seconds'
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestWorkflowGraph:
    """Tests du graphe complet (nodes + edges)"""
    
    def setup_method(self):
        """Setup exécuté avant chaque test"""
        self.client = APIClient()
        
        self.org = Organization.objects.create(name='Test Organization')
        
        self.owner = User.objects.create_user(
            email='owner@test.com',
            password='Pass123!',
            first_name='Owner',
            last_name='User',
            role='OWNER',
            organization=self.org
        )
        
        self.project = Project.objects.create(
            name='Test Project',
            organization=self.org,
            created_by=self.owner
        )
        
        self.workflow = Workflow.objects.create(
            name='Test Workflow',
            organization=self.org,
            project=self.project
        )
        
    def test_get_workflow_graph(self):
        """Test récupération du graphe complet"""
        trigger = Node.objects.create(
            workflow=self.workflow,
            node_id='trigger_1',
            node_type='trigger',
            label='Trigger',
            position_x=100,
            position_y=100
        )
        
        action = Node.objects.create(
            workflow=self.workflow,
            node_id='action_1',
            node_type='action',
            label='Action',
            position_x=300,
            position_y=100
        )
        
        Edge.objects.create(
            workflow=self.workflow,
            source_node=trigger,
            target_node=action
        )
        
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('automation:workflow-graph', kwargs={'pk': self.workflow.id})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'nodes' in response.data
        assert 'edges' in response.data
        assert len(response.data['nodes']) == 2
        assert len(response.data['edges']) == 1
