"""
Tests pour les vues du module Foundation.
"""
import json
from unittest.mock import Mock, patch
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from ..models import Organization, OrganizationMember, Subscription, VerificationRequest
from ..views.stripe_webhook_view import StripeWebhookView

User = get_user_model()


class AuthViewsTestCase(APITestCase):
    """Tests pour les vues d'authentification."""
    
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/login/'
        self.refresh_url = '/api/auth/refresh/'
    
    def test_register_client_user(self):
        """Test d'inscription d'un utilisateur client."""
        data = {
            'email': 'client@example.com',
            'password': 'TestPass123!',
            'user_type': 'CLIENT',
            'profile_data': {
                'first_name': 'John',
                'last_name': 'Doe',
                'phone': '+33123456789'
            }
        }
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['email'], 'client@example.com')
    
    def test_register_entreprise_user(self):
        """Test d'inscription d'un utilisateur entreprise."""
        data = {
            'email': 'entreprise@example.com',
            'password': 'TestPass123!',
            'user_type': 'ENTREPRISE',
            'profile_data': {
                'company_name': 'Test Company',
                'siret': '73282932000074',
                'legal_form': 'SAS'
            }
        }
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['user_type'], 'ENTREPRISE')
    
    def test_login_user(self):
        """Test de connexion utilisateur."""
        # Créer un utilisateur
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!'
        )
        
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('user', response.data)
    
    def test_login_invalid_credentials(self):
        """Test de connexion avec identifiants invalides."""
        data = {
            'email': 'wrong@example.com',
            'password': 'wrongpass'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class OrganizationViewsTestCase(APITestCase):
    """Tests pour les vues d'organisation."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.org_list_url = '/api/organizations/'
        self.org_create_url = '/api/organizations/'
    
    def test_create_organization(self):
        """Test de création d'organisation."""
        data = {
            'name': 'Test Organization',
            'description': 'A test organization',
            'organization_type': 'COMPANY'
        }
        
        response = self.client.post(self.org_create_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test Organization')
        self.assertEqual(response.data['owner'], self.user.id)
    
    def test_list_organizations(self):
        """Test de listage des organisations."""
        # Créer une organisation
        org = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            owner=self.user
        )
        
        response = self.client.get(self.org_list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Organization')
    
    def test_add_member_to_organization(self):
        """Test d'ajout de membre à une organisation."""
        org = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            owner=self.user
        )
        
        member = User.objects.create_user(
            email='member@example.com',
            password='testpass123'
        )
        
        data = {
            'user_id': member.id,
            'role': 'MEMBER'
        }
        
        url = f'/api/organizations/{org.id}/members/'
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], member.id)
        self.assertEqual(response.data['role'], 'MEMBER')
    
    def test_unauthorized_access(self):
        """Test d'accès non autorisé."""
        self.client.force_authenticate(user=None)
        
        response = self.client.get(self.org_list_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BillingViewsTestCase(APITestCase):
    """Tests pour les vues de facturation."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
        )
        self.org = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            owner=self.user
        )
        self.client.force_authenticate(user=self.user)
        
        self.subscription_url = f'/api/organizations/{self.org.id}/subscription/'
    
    def test_create_subscription(self):
        """Test de création d'abonnement."""
        data = {
            'plan_name': 'Premium',
            'plan_price': '29.99',
            'billing_cycle': 'MONTHLY'
        }
        
        with patch('stripe.Customer.create') as mock_stripe:
            mock_stripe.return_value = Mock(id='cus_test123')
            
            response = self.client.post(self.subscription_url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data['plan_name'], 'Premium')
    
    def test_get_subscription_details(self):
        """Test de récupération des détails d'abonnement."""
        subscription = Subscription.objects.create(
            organization=self.org,
            plan_name='Premium',
            plan_price=29.99
        )
        
        response = self.client.get(self.subscription_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['plan_name'], 'Premium')
    
    def test_cancel_subscription(self):
        """Test d'annulation d'abonnement."""
        subscription = Subscription.objects.create(
            organization=self.org,
            plan_name='Premium',
            plan_price=29.99,
            status='ACTIVE'
        )
        
        url = f'/api/organizations/{self.org.id}/subscription/cancel/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier que l'abonnement a été annulé
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, 'CANCELED')


class VerificationViewsTestCase(APITestCase):
    """Tests pour les vues de vérification."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='entreprise@example.com',
            password='testpass123',
            user_type='ENTREPRISE'
        )
        self.client.force_authenticate(user=self.user)
        
        self.verification_url = '/api/verification/'
    
    def test_start_verification_process(self):
        """Test de démarrage du processus de vérification."""
        data = {
            'request_type': 'KYB_FULL'
        }
        
        response = self.client.post(self.verification_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['request_type'], 'KYB_FULL')
        self.assertEqual(response.data['status'], 'PENDING')
    
    def test_submit_verification_document(self):
        """Test de soumission de document de vérification."""
        # Créer une demande de vérification
        verification = VerificationRequest.objects.create(
            entreprise=self.user.entreprise,
            request_type='KYB_FULL'
        )
        
        # Mock d'un fichier
        from django.core.files.uploadedfile import SimpleUploadedFile
        test_file = SimpleUploadedFile(
            "kbis.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        data = {
            'document_type': 'KBIS',
            'file': test_file
        }
        
        url = f'/api/verification/{verification.id}/documents/'
        response = self.client.post(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['document_type'], 'KBIS')


class StripeWebhookViewTestCase(TestCase):
    """Tests pour la vue webhook Stripe."""
    
    def setUp(self):
        self.client = Client()
        self.webhook_url = '/api/webhooks/stripe/'
    
    @patch('stripe.Webhook.construct_event')
    def test_valid_webhook_signature(self, mock_construct_event):
        """Test avec une signature webhook valide."""
        mock_event = {
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': 'pi_test123',
                    'amount': 2999,
                    'currency': 'eur'
                }
            }
        }
        mock_construct_event.return_value = mock_event
        
        payload = json.dumps(mock_event)
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='test_signature'
        )
        
        self.assertEqual(response.status_code, 200)
    
    @patch('stripe.Webhook.construct_event')
    def test_invalid_webhook_signature(self, mock_construct_event):
        """Test avec une signature webhook invalide."""
        mock_construct_event.side_effect = ValueError("Invalid signature")
        
        payload = json.dumps({'type': 'test'})
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='invalid_signature'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_missing_signature_header(self):
        """Test sans header de signature."""
        payload = json.dumps({'type': 'test'})
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)


class PermissionsTestCase(APITestCase):
    """Tests pour les permissions."""
    
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            email='owner@example.com',
            password='testpass123'
        )
        self.member = User.objects.create_user(
            email='member@example.com',
            password='testpass123'
        )
        self.outsider = User.objects.create_user(
            email='outsider@example.com',
            password='testpass123'
        )
        
        self.org = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            owner=self.owner
        )
        
        # Ajouter le membre à l'organisation
        OrganizationMember.objects.create(
            organization=self.org,
            user=self.member,
            role='MEMBER'
        )
    
    def test_owner_can_access_organization(self):
        """Test que le propriétaire peut accéder à l'organisation."""
        self.client.force_authenticate(user=self.owner)
        
        url = f'/api/organizations/{self.org.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_member_can_access_organization(self):
        """Test que le membre peut accéder à l'organisation."""
        self.client.force_authenticate(user=self.member)
        
        url = f'/api/organizations/{self.org.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_outsider_cannot_access_organization(self):
        """Test qu'un utilisateur externe ne peut pas accéder à l'organisation."""
        self.client.force_authenticate(user=self.outsider)
        
        url = f'/api/organizations/{self.org.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_only_owner_can_delete_organization(self):
        """Test que seul le propriétaire peut supprimer l'organisation."""
        # Test avec le membre
        self.client.force_authenticate(user=self.member)
        
        url = f'/api/organizations/{self.org.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test avec le propriétaire
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
