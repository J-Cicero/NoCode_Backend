"""
Tests pour les projets Studio
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.foundation.models import User, Organization
from apps.studio.models import Project


@pytest.mark.django_db
class TestProjectCRUD:
    """Tests CRUD des projets"""
    
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
        
        self.client_user = User.objects.create_user(
            email='client@test.com',
            password='Pass123!',
            first_name='Client',
            last_name='User',
            role='CLIENT',
            organization=self.org
        )
        
        self.project = Project.objects.create(
            name='Test Project',
            description='A test project',
            organization=self.org,
            created_by=self.owner
        )
        
        self.list_url = reverse('studio:project-list')
        self.detail_url = reverse('studio:project-detail', kwargs={'pk': self.project.id})
        
    def test_list_projects_authenticated(self):
        """Test liste des projets pour utilisateur authentifié"""
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.get(self.list_url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0
        
    def test_list_projects_unauthenticated(self):
        """Test liste des projets sans authentification"""
        response = self.client.get(self.list_url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    def test_create_project_as_owner(self):
        """Test création de projet par owner"""
        self.client.force_authenticate(user=self.owner)
        
        data = {
            'name': 'New Project',
            'description': 'A new test project'
        }
        
        response = self.client.post(self.list_url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Project'
        assert Project.objects.filter(name='New Project').exists()
        
    def test_create_project_as_client(self):
        """Test création de projet par client (devrait échouer)"""
        self.client.force_authenticate(user=self.client_user)
        
        data = {
            'name': 'New Project',
            'description': 'A new test project'
        }
        
        response = self.client.post(self.list_url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_project_detail(self):
        """Test récupération détails projet"""
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.get(self.detail_url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Test Project'
        
    def test_update_project_as_owner(self):
        """Test modification projet par owner"""
        self.client.force_authenticate(user=self.owner)
        
        data = {'name': 'Updated Project'}
        response = self.client.patch(self.detail_url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Project'
        
    def test_delete_project_as_owner(self):
        """Test suppression projet par owner"""
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.delete(self.detail_url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Project.objects.filter(id=self.project.id).exists()
        
    def test_client_can_view_project(self):
        """Test que le client peut voir le projet"""
        self.client.force_authenticate(user=self.client_user)
        
        response = self.client.get(self.detail_url)
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestProjectGeneration:
    """Tests génération de code pour les projets"""
    
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
        
    def test_generate_project_code(self):
        """Test génération de code pour le projet"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('studio:project-generate', kwargs={'pk': self.project.id})
        response = self.client.post(url, format='json')
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]
        
    def test_generate_project_without_tables(self):
        """Test génération sans tables (devrait échouer ou avertir)"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('studio:project-generate', kwargs={'pk': self.project.id})
        response = self.client.post(url, format='json')
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST
        ]


@pytest.mark.django_db
class TestProjectFilters:
    """Tests filtres et recherche de projets"""
    
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
        
        Project.objects.create(
            name='Active Project',
            status='active',
            organization=self.org,
            created_by=self.owner
        )
        
        Project.objects.create(
            name='Archived Project',
            status='archived',
            organization=self.org,
            created_by=self.owner
        )
        
        self.list_url = reverse('studio:project-list')
        
    def test_filter_projects_by_status(self):
        """Test filtrage par statut"""
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.get(self.list_url, {'status': 'active'})
        
        assert response.status_code == status.HTTP_200_OK
        for project in response.data['results']:
            assert project['status'] == 'active'
            
    def test_search_projects_by_name(self):
        """Test recherche par nom"""
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.get(self.list_url, {'search': 'Active'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0
        assert 'Active' in response.data['results'][0]['name']
