"""
Tests pour les organisations
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.foundation.models import User, Organization


@pytest.mark.django_db
class TestOrganizationCRUD:
    """Tests CRUD des organisations"""
    
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
        
        self.list_url = reverse('foundation:organization-list')
        self.detail_url = reverse('foundation:organization-detail', kwargs={'pk': self.org.id})
        
    def test_list_organizations_authenticated(self):
        """Test liste des organisations pour utilisateur authentifié"""
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.get(self.list_url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0
        
    def test_list_organizations_unauthenticated(self):
        """Test liste des organisations sans authentification"""
        response = self.client.get(self.list_url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    def test_create_organization_success(self):
        """Test création d'organisation avec succès"""
        self.client.force_authenticate(user=self.owner)
        
        data = {
            'name': 'New Organization',
            'description': 'A new test organization'
        }
        
        response = self.client.post(self.list_url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Organization'
        assert Organization.objects.filter(name='New Organization').exists()
        
    def test_get_organization_detail(self):
        """Test récupération détails organisation"""
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.get(self.detail_url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Test Organization'
        
    def test_update_organization_as_owner(self):
        """Test modification organisation par owner"""
        self.client.force_authenticate(user=self.owner)
        
        data = {'name': 'Updated Organization'}
        response = self.client.patch(self.detail_url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Organization'
        
        self.org.refresh_from_db()
        assert self.org.name == 'Updated Organization'
        
    def test_delete_organization_as_owner(self):
        """Test suppression organisation par owner"""
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.delete(self.detail_url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Organization.objects.filter(id=self.org.id).exists()


@pytest.mark.django_db
class TestOrganizationMembers:
    """Tests gestion des membres d'une organisation"""
    
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
        
        self.member = User.objects.create_user(
            email='member@test.com',
            password='Pass123!',
            first_name='Member',
            last_name='User',
            role='CLIENT',
            organization=self.org
        )
        
    def test_list_organization_members(self):
        """Test liste des membres de l'organisation"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('foundation:organization-members', kwargs={'pk': self.org.id})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 2
        
    def test_invite_user_to_organization(self):
        """Test invitation d'un utilisateur"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('foundation:organization-invite-user', kwargs={'pk': self.org.id})
        data = {
            'email': 'newuser@test.com',
            'role': 'CLIENT',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]
        
    def test_remove_member_from_organization(self):
        """Test suppression d'un membre"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('foundation:organization-remove-member', kwargs={'pk': self.org.id})
        data = {'user_id': self.member.id}
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]
        
    def test_change_member_role(self):
        """Test changement de rôle d'un membre"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('foundation:organization-change-role', kwargs={'pk': self.org.id})
        data = {
            'user_id': self.member.id,
            'role': 'ADMIN'
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        self.member.refresh_from_db()
        assert self.member.role == 'ADMIN'


@pytest.mark.django_db
class TestOrganizationSettings:
    """Tests paramètres de l'organisation"""
    
    def setup_method(self):
        """Setup exécuté avant chaque test"""
        self.client = APIClient()
        
        self.org = Organization.objects.create(
            name='Test Organization',
            settings={
                'notifications_enabled': True,
                'default_language': 'fr'
            }
        )
        
        self.owner = User.objects.create_user(
            email='owner@test.com',
            password='Pass123!',
            first_name='Owner',
            last_name='User',
            role='OWNER',
            organization=self.org
        )
        
    def test_get_organization_settings(self):
        """Test récupération des paramètres"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('foundation:organization-detail', kwargs={'pk': self.org.id})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'settings' in response.data
        assert response.data['settings']['notifications_enabled'] is True
        
    def test_update_organization_settings(self):
        """Test mise à jour des paramètres"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('foundation:organization-detail', kwargs={'pk': self.org.id})
        data = {
            'settings': {
                'notifications_enabled': False,
                'default_language': 'en'
            }
        }
        
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        self.org.refresh_from_db()
        assert self.org.settings['notifications_enabled'] is False
        assert self.org.settings['default_language'] == 'en'
