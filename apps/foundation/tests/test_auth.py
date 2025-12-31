"""
Tests pour l'authentification (login, register, JWT)
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.foundation.models import User, Organization


@pytest.mark.django_db
class TestAuthentication:
    """Tests d'authentification JWT"""
    
    def setup_method(self):
        """Setup exécuté avant chaque test"""
        self.client = APIClient()
        self.register_owner_url = reverse('auth:register-owner')
        self.register_client_url = reverse('auth:register-client')
        self.login_url = reverse('auth:login')
        self.logout_url = reverse('auth:logout')
        
    def test_register_owner_success(self):
        """Test inscription owner avec succès"""
        data = {
            'email': 'owner@test.com',
            'password': 'TestPass123!',
            'first_name': 'John',
            'last_name': 'Doe',
            'organization_name': 'Test Corp'
        }
        
        response = self.client.post(self.register_owner_url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert 'tokens' in response.data
        assert 'organization' in response.data
        assert response.data['user']['email'] == 'owner@test.com'
        assert response.data['user']['role'] == 'OWNER'
        assert User.objects.filter(email='owner@test.com').exists()
        assert Organization.objects.filter(name='Test Corp').exists()
        
    def test_register_owner_missing_fields(self):
        """Test inscription owner avec champs manquants"""
        data = {
            'email': 'owner@test.com',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(self.register_owner_url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_register_owner_duplicate_email(self):
        """Test inscription avec email déjà existant"""
        User.objects.create_user(
            email='existing@test.com',
            password='Pass123!',
            first_name='Existing',
            last_name='User'
        )
        
        data = {
            'email': 'existing@test.com',
            'password': 'NewPass123!',
            'first_name': 'New',
            'last_name': 'User',
            'organization_name': 'New Corp'
        }
        
        response = self.client.post(self.register_owner_url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_register_owner_weak_password(self):
        """Test inscription avec mot de passe faible"""
        data = {
            'email': 'owner@test.com',
            'password': '123',
            'first_name': 'John',
            'last_name': 'Doe',
            'organization_name': 'Test Corp'
        }
        
        response = self.client.post(self.register_owner_url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_login_success(self):
        """Test connexion avec succès"""
        user = User.objects.create_user(
            email='user@test.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        
        data = {
            'email': 'user@test.com',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'tokens' in response.data
        assert 'access' in response.data['tokens']
        assert 'refresh' in response.data['tokens']
        assert 'user' in response.data
        
    def test_login_invalid_credentials(self):
        """Test connexion avec mauvais identifiants"""
        User.objects.create_user(
            email='user@test.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        
        data = {
            'email': 'user@test.com',
            'password': 'WrongPassword'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    def test_login_nonexistent_user(self):
        """Test connexion avec utilisateur inexistant"""
        data = {
            'email': 'nonexistent@test.com',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    def test_logout_success(self):
        """Test déconnexion avec succès"""
        user = User.objects.create_user(
            email='user@test.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        
        login_data = {
            'email': 'user@test.com',
            'password': 'TestPass123!'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        access_token = login_response.data['tokens']['access']
        refresh_token = login_response.data['tokens']['refresh']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        logout_data = {'refresh_token': refresh_token}
        response = self.client.post(self.logout_url, logout_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
    def test_logout_without_token(self):
        """Test déconnexion sans token"""
        response = self.client.post(self.logout_url, {}, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestPasswordManagement:
    """Tests gestion des mots de passe"""
    
    def setup_method(self):
        """Setup exécuté avant chaque test"""
        self.client = APIClient()
        self.password_change_url = reverse('auth:password-change')
        self.password_reset_request_url = reverse('auth:password-reset-request')
        self.password_reset_confirm_url = reverse('auth:password-reset-confirm')
        
        self.user = User.objects.create_user(
            email='user@test.com',
            password='OldPass123!',
            first_name='Test',
            last_name='User'
        )
        
    def test_password_change_success(self):
        """Test changement de mot de passe avec succès"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewPass123!'
        }
        
        response = self.client.post(self.password_change_url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        self.user.refresh_from_db()
        assert self.user.check_password('NewPass123!')
        
    def test_password_change_wrong_old_password(self):
        """Test changement avec mauvais ancien mot de passe"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'old_password': 'WrongOldPass!',
            'new_password': 'NewPass123!'
        }
        
        response = self.client.post(self.password_change_url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_password_change_unauthenticated(self):
        """Test changement sans authentification"""
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewPass123!'
        }
        
        response = self.client.post(self.password_change_url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    def test_password_reset_request_success(self):
        """Test demande de réinitialisation réussie"""
        data = {'email': 'user@test.com'}
        
        response = self.client.post(self.password_reset_request_url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
    def test_password_reset_request_nonexistent_email(self):
        """Test demande avec email inexistant (doit retourner 200 pour sécurité)"""
        data = {'email': 'nonexistent@test.com'}
        
        response = self.client.post(self.password_reset_request_url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestTokenRefresh:
    """Tests renouvellement des tokens JWT"""
    
    def setup_method(self):
        """Setup exécuté avant chaque test"""
        self.client = APIClient()
        self.login_url = reverse('auth:login')
        self.refresh_url = reverse('auth:token-refresh')
        
        self.user = User.objects.create_user(
            email='user@test.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        
    def test_token_refresh_success(self):
        """Test renouvellement de token avec succès"""
        login_data = {
            'email': 'user@test.com',
            'password': 'TestPass123!'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        refresh_token = login_response.data['tokens']['refresh']
        
        data = {'refresh': refresh_token}
        response = self.client.post(self.refresh_url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        
    def test_token_refresh_invalid_token(self):
        """Test renouvellement avec token invalide"""
        data = {'refresh': 'invalid_token_xyz'}
        
        response = self.client.post(self.refresh_url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
