"""
Tests pour les workflows d'automatisation
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.foundation.models import User, Organization
from apps.studio.models import Project
from apps.automation.models import Workflow, Node, Edge


@pytest.mark.django_db
class TestWorkflowCRUD:
    """Tests CRUD des workflows"""
    
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
            description='A test workflow',
            organization=self.org,
            project=self.project,
            status='INACTIVE'
        )
        
        self.list_url = reverse('automation:workflow-list')
        self.detail_url = reverse('automation:workflow-detail', kwargs={'pk': self.workflow.id})
        
    def test_list_workflows(self):
        """Test liste des workflows"""
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.get(self.list_url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0
        
    def test_create_workflow(self):
        """Test création de workflow"""
        self.client.force_authenticate(user=self.owner)
        
        data = {
            'name': 'New Workflow',
            'description': 'A new test workflow',
            'project_id': self.project.id
        }
        
        response = self.client.post(self.list_url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Workflow'
        assert Workflow.objects.filter(name='New Workflow').exists()
        
    def test_get_workflow_detail(self):
        """Test récupération détails workflow"""
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.get(self.detail_url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Test Workflow'
        
    def test_update_workflow(self):
        """Test modification workflow"""
        self.client.force_authenticate(user=self.owner)
        
        data = {'name': 'Updated Workflow'}
        response = self.client.patch(self.detail_url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Workflow'
        
    def test_delete_workflow(self):
        """Test suppression workflow"""
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.delete(self.detail_url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Workflow.objects.filter(id=self.workflow.id).exists()


@pytest.mark.django_db
class TestWorkflowActivation:
    """Tests activation/désactivation des workflows"""
    
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
            project=self.project,
            status='INACTIVE'
        )
        
        trigger = Node.objects.create(
            workflow=self.workflow,
            node_id='trigger_1',
            node_type='trigger',
            label='Trigger',
            position_x=100,
            position_y=100,
            config={'event_type': 'test'}
        )
        
        action = Node.objects.create(
            workflow=self.workflow,
            node_id='action_1',
            node_type='action',
            label='Action',
            position_x=300,
            position_y=100,
            config={'action': 'log'}
        )
        
        Edge.objects.create(
            workflow=self.workflow,
            source_node=trigger,
            target_node=action
        )
        
    def test_activate_workflow_success(self):
        """Test activation workflow avec succès"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('automation:workflow-activate', kwargs={'pk': self.workflow.id})
        response = self.client.post(url, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        self.workflow.refresh_from_db()
        assert self.workflow.status == 'ACTIVE'
        
    def test_activate_workflow_without_trigger(self):
        """Test activation sans trigger (devrait échouer)"""
        workflow_no_trigger = Workflow.objects.create(
            name='No Trigger Workflow',
            organization=self.org,
            status='INACTIVE'
        )
        
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('automation:workflow-activate', kwargs={'pk': workflow_no_trigger.id})
        response = self.client.post(url, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_deactivate_workflow(self):
        """Test désactivation workflow"""
        self.workflow.status = 'ACTIVE'
        self.workflow.save()
        
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('automation:workflow-deactivate', kwargs={'pk': self.workflow.id})
        response = self.client.post(url, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        self.workflow.refresh_from_db()
        assert self.workflow.status == 'INACTIVE'


@pytest.mark.django_db
class TestWorkflowExecution:
    """Tests exécution des workflows"""
    
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
            project=self.project,
            status='ACTIVE'
        )
        
        trigger = Node.objects.create(
            workflow=self.workflow,
            node_id='trigger_1',
            node_type='trigger',
            label='Trigger',
            position_x=100,
            position_y=100,
            config={'event_type': 'manual'}
        )
        
        action = Node.objects.create(
            workflow=self.workflow,
            node_id='action_1',
            node_type='action',
            label='Action',
            position_x=300,
            position_y=100,
            config={'action': 'log'}
        )
        
        Edge.objects.create(
            workflow=self.workflow,
            source_node=trigger,
            target_node=action
        )
        
    def test_execute_workflow_manually(self):
        """Test exécution manuelle du workflow"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('automation:workflow-test', kwargs={'pk': self.workflow.id})
        data = {'test_data': {'key': 'value'}}
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
    def test_get_workflow_execution_history(self):
        """Test récupération historique des exécutions"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('automation:workflow-executions', kwargs={'pk': self.workflow.id})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data


@pytest.mark.django_db
class TestWorkflowFilters:
    """Tests filtres des workflows"""
    
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
        
        Workflow.objects.create(
            name='Active Workflow',
            organization=self.org,
            project=self.project,
            status='ACTIVE'
        )
        
        Workflow.objects.create(
            name='Inactive Workflow',
            organization=self.org,
            project=self.project,
            status='INACTIVE'
        )
        
        self.list_url = reverse('automation:workflow-list')
        
    def test_filter_workflows_by_status(self):
        """Test filtrage par statut"""
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.get(self.list_url, {'status': 'ACTIVE'})
        
        assert response.status_code == status.HTTP_200_OK
        for workflow in response.data['results']:
            assert workflow['status'] == 'ACTIVE'
            
    def test_filter_workflows_by_project(self):
        """Test filtrage par projet"""
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.get(self.list_url, {'project_id': self.project.id})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 2
