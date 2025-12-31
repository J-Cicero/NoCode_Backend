"""
Tests pour le système RBAC (Role-Based Access Control)
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.foundation.models import User, Organization
from apps.foundation.permissions.rbac import has_permission, check_organization_access


@pytest.mark.django_db
class TestRBACPermissions:
    """Tests du système de permissions RBAC"""
    
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
        
        self.admin = User.objects.create_user(
            email='admin@test.com',
            password='Pass123!',
            first_name='Admin',
            last_name='User',
            role='ADMIN',
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
        
        self.other_org = Organization.objects.create(name='Other Organization')
        self.other_user = User.objects.create_user(
            email='other@test.com',
            password='Pass123!',
            first_name='Other',
            last_name='User',
            role='CLIENT',
            organization=self.other_org
        )
        
    def test_owner_has_all_permissions(self):
        """Test que l'owner a toutes les permissions"""
        assert has_permission(self.owner, 'create', 'project')
        assert has_permission(self.owner, 'update', 'project')
        assert has_permission(self.owner, 'delete', 'project')
        assert has_permission(self.owner, 'view', 'project')
        assert has_permission(self.owner, 'manage_users', 'organization')
        assert has_permission(self.owner, 'manage_billing', 'organization')
        
    def test_admin_has_management_permissions(self):
        """Test que l'admin a les permissions de gestion"""
        assert has_permission(self.admin, 'create', 'project')
        assert has_permission(self.admin, 'update', 'project')
        assert has_permission(self.admin, 'delete', 'project')
        assert has_permission(self.admin, 'view', 'project')
        assert has_permission(self.admin, 'manage_users', 'organization')
        
    def test_admin_cannot_manage_billing(self):
        """Test que l'admin ne peut pas gérer la facturation"""
        assert not has_permission(self.admin, 'manage_billing', 'organization')
        
    def test_client_has_limited_permissions(self):
        """Test que le client a des permissions limitées"""
        assert has_permission(self.client_user, 'view', 'project')
        assert not has_permission(self.client_user, 'create', 'project')
        assert not has_permission(self.client_user, 'delete', 'project')
        assert not has_permission(self.client_user, 'manage_users', 'organization')
        assert not has_permission(self.client_user, 'manage_billing', 'organization')
        
    def test_organization_access_control(self):
        """Test que l'accès est limité à l'organisation"""
        assert check_organization_access(self.owner, self.org)
        assert check_organization_access(self.admin, self.org)
        assert check_organization_access(self.client_user, self.org)
        assert not check_organization_access(self.other_user, self.org)
        
    def test_cross_organization_access_denied(self):
        """Test qu'un utilisateur ne peut pas accéder aux ressources d'une autre org"""
        assert not check_organization_access(self.owner, self.other_org)
        assert not check_organization_access(self.admin, self.other_org)


@pytest.mark.django_db
class TestOrganizationPermissions:
    """Tests des permissions au niveau organisation"""
    
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
        
        self.org_list_url = reverse('foundation:organization-list')
        self.org_detail_url = reverse('foundation:organization-detail', kwargs={'pk': self.org.id})
        
    def test_owner_can_update_organization(self):
        """Test que l'owner peut modifier l'organisation"""
        self.client.force_authenticate(user=self.owner)
        
        data = {'name': 'Updated Name'}
        response = self.client.patch(self.org_detail_url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
    def test_client_cannot_update_organization(self):
        """Test que le client ne peut pas modifier l'organisation"""
        self.client.force_authenticate(user=self.client_user)
        
        data = {'name': 'Updated Name'}
        response = self.client.patch(self.org_detail_url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_owner_can_invite_users(self):
        """Test que l'owner peut inviter des utilisateurs"""
        self.client.force_authenticate(user=self.owner)
        
        invite_url = reverse('foundation:organization-invite-user', kwargs={'pk': self.org.id})
        data = {
            'email': 'newuser@test.com',
            'role': 'CLIENT'
        }
        
        response = self.client.post(invite_url, data, format='json')
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]
        
    def test_client_cannot_invite_users(self):
        """Test que le client ne peut pas inviter des utilisateurs"""
        self.client.force_authenticate(user=self.client_user)
        
        invite_url = reverse('foundation:organization-invite-user', kwargs={'pk': self.org.id})
        data = {
            'email': 'newuser@test.com',
            'role': 'CLIENT'
        }
        
        response = self.client.post(invite_url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestUserPermissions:
    """Tests des permissions au niveau utilisateur"""
    
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
        
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            password='Pass123!',
            first_name='User1',
            last_name='Test',
            role='CLIENT',
            organization=self.org
        )
        
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            password='Pass123!',
            first_name='User2',
            last_name='Test',
            role='CLIENT',
            organization=self.org
        )
        
    def test_user_can_view_own_profile(self):
        """Test qu'un utilisateur peut voir son propre profil"""
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('foundation:user-detail', kwargs={'pk': self.user1.id})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'user1@test.com'
        
    def test_user_can_update_own_profile(self):
        """Test qu'un utilisateur peut modifier son propre profil"""
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('foundation:user-detail', kwargs={'pk': self.user1.id})
        data = {'first_name': 'UpdatedName'}
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
    def test_user_cannot_update_other_user(self):
        """Test qu'un utilisateur ne peut pas modifier un autre utilisateur"""
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('foundation:user-detail', kwargs={'pk': self.user2.id})
        data = {'first_name': 'Hacked'}
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_owner_can_update_any_user(self):
        """Test que l'owner peut modifier n'importe quel utilisateur de son org"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('foundation:user-detail', kwargs={'pk': self.user1.id})
        data = {'role': 'ADMIN'}
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
    def test_user_cannot_change_own_role(self):
        """Test qu'un utilisateur ne peut pas changer son propre rôle"""
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('foundation:user-detail', kwargs={'pk': self.user1.id})
        data = {'role': 'OWNER'}
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN]
