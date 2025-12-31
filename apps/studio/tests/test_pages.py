"""
Tests pour les pages Studio
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.foundation.models import User, Organization
from apps.studio.models import Project, Page, Component, ComponentInstance


@pytest.mark.django_db
class TestPageCRUD:
    """Tests CRUD des pages"""
    
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
        
        self.page = Page.objects.create(
            project=self.project,
            name='Home',
            route='/home',
            config={'layout': 'grid'}
        )
        
    def test_create_page_success(self):
        """Test création de page avec succès"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('studio:page-list', kwargs={'project_id': self.project.id})
        data = {
            'name': 'About',
            'route': '/about',
            'config': {'layout': 'flex'}
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'About'
        assert Page.objects.filter(name='About').exists()
        
    def test_create_page_with_duplicate_route(self):
        """Test création avec route déjà existante"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('studio:page-list', kwargs={'project_id': self.project.id})
        data = {
            'name': 'Another Home',
            'route': '/home',
            'config': {}
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_get_page_detail(self):
        """Test récupération détails page"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('studio:page-detail', kwargs={
            'project_id': self.project.id,
            'pk': self.page.id
        })
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Home'
        
    def test_update_page_config(self):
        """Test modification de la configuration de page"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('studio:page-detail', kwargs={
            'project_id': self.project.id,
            'pk': self.page.id
        })
        data = {
            'config': {
                'layout': 'grid',
                'columns': 12,
                'theme': 'dark'
            }
        }
        
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['config']['theme'] == 'dark'
        
    def test_delete_page(self):
        """Test suppression page"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('studio:page-detail', kwargs={
            'project_id': self.project.id,
            'pk': self.page.id
        })
        response = self.client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Page.objects.filter(id=self.page.id).exists()


@pytest.mark.django_db
class TestComponentInstance:
    """Tests instances de composants sur les pages"""
    
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
        
        self.page = Page.objects.create(
            project=self.project,
            name='Home',
            route='/home'
        )
        
        self.component = Component.objects.create(
            name='DataTable',
            component_type='table',
            category='data'
        )
        
    def test_add_component_to_page(self):
        """Test ajout d'un composant à une page"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('studio:component-instance-create', kwargs={
            'project_id': self.project.id,
            'page_id': self.page.id
        })
        data = {
            'component_id': self.component.id,
            'position': {'x': 100, 'y': 200, 'width': 400, 'height': 300},
            'config': {'columns': ['name', 'email']}
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert ComponentInstance.objects.filter(page=self.page).exists()
        
    def test_update_component_position(self):
        """Test modification de position d'un composant"""
        instance = ComponentInstance.objects.create(
            page=self.page,
            component=self.component,
            position={'x': 100, 'y': 100}
        )
        
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('studio:component-instance-detail', kwargs={
            'project_id': self.project.id,
            'page_id': self.page.id,
            'pk': instance.id
        })
        data = {
            'position': {'x': 200, 'y': 200}
        }
        
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['position']['x'] == 200
        
    def test_delete_component_instance(self):
        """Test suppression d'une instance de composant"""
        instance = ComponentInstance.objects.create(
            page=self.page,
            component=self.component,
            position={'x': 100, 'y': 100}
        )
        
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('studio:component-instance-detail', kwargs={
            'project_id': self.project.id,
            'page_id': self.page.id,
            'pk': instance.id
        })
        response = self.client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ComponentInstance.objects.filter(id=instance.id).exists()


@pytest.mark.django_db
class TestPageLayout:
    """Tests layout et organisation des pages"""
    
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
        
    def test_create_page_with_grid_layout(self):
        """Test création page avec layout grille"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('studio:page-list', kwargs={'project_id': self.project.id})
        data = {
            'name': 'Grid Page',
            'route': '/grid',
            'config': {
                'layout': 'grid',
                'columns': 12,
                'gap': 16
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['config']['layout'] == 'grid'
        
    def test_create_page_with_flex_layout(self):
        """Test création page avec layout flex"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('studio:page-list', kwargs={'project_id': self.project.id})
        data = {
            'name': 'Flex Page',
            'route': '/flex',
            'config': {
                'layout': 'flex',
                'direction': 'row',
                'justify': 'center'
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['config']['layout'] == 'flex'
