"""
Tests pour les services du module Foundation.
"""
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from ..models import (
    Client, Entreprise, Organization, OrganizationMember, 
    Abonnement, DocumentVerification
)
from ..services.auth_service import AuthService
from ..services.organization_service import OrganizationService
from ..services.billing_service import BillingService
from ..services.verification_service import VerificationService
from ..services.event_bus import EventBus

User = get_user_model()


class AuthServiceTestCase(TestCase):
    """Tests pour AuthService."""
    
    def setUp(self):
        self.auth_service = AuthService()
        self.user_data = {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'user_type': 'CLIENT'
        }
    
    def test_register_client_user(self):
        """Test d'inscription d'un utilisateur client."""
        with patch.object(EventBus, 'publish') as mock_publish:
            result = self.auth_service.register_user(
                self.user_data,
                profile_data={
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'phone': '+33123456789'
                }
            )
            
            self.assertTrue(result['success'])
            self.assertIn('user', result)
            self.assertEqual(result['user'].email, 'test@example.com')
            self.assertEqual(result['user'].user_type, 'CLIENT')
            
            # Vérifier qu'un événement a été publié
            mock_publish.assert_called()
    
    def test_register_entreprise_user(self):
        """Test d'inscription d'un utilisateur entreprise."""
        entreprise_data = self.user_data.copy()
        entreprise_data['user_type'] = 'ENTREPRISE'
        
        with patch.object(EventBus, 'publish') as mock_publish:
            result = self.auth_service.register_user(
                entreprise_data,
                profile_data={
                    'company_name': 'Test Company',
                    'siret': '73282932000074',
                    'legal_form': 'SAS'
                }
            )
            
            self.assertTrue(result['success'])
            self.assertEqual(result['user'].user_type, 'ENTREPRISE')
            
            # Vérifier que le profil entreprise a été créé
            self.assertTrue(hasattr(result['user'], 'entreprise'))
    
    def test_authenticate_user_success(self):
        """Test d'authentification réussie."""
        # Créer un utilisateur
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!'
        )
        
        result = self.auth_service.authenticate_user('test@example.com', 'TestPass123!')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['user'], user)
        self.assertIn('tokens', result)
    
    def test_authenticate_user_failure(self):
        """Test d'authentification échouée."""
        result = self.auth_service.authenticate_user('wrong@example.com', 'wrongpass')
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_refresh_token(self):
        """Test de rafraîchissement de token."""
        # Créer un utilisateur et obtenir des tokens
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!'
        )
        
        auth_result = self.auth_service.authenticate_user('test@example.com', 'TestPass123!')
        refresh_token = auth_result['tokens']['refresh']
        
        result = self.auth_service.refresh_token(refresh_token)
        
        self.assertTrue(result['success'])
        self.assertIn('access', result['tokens'])


class OrganizationServiceTestCase(TestCase):
    """Tests pour OrganizationService."""
    
    def setUp(self):
        self.org_service = OrganizationService()
        self.owner = User.objects.create_user(
            email='owner@example.com',
            password='testpass123'
        )
    
    def test_create_organization(self):
        """Test de création d'organisation."""
        org_data = {
            'name': 'Test Organization',
            'description': 'A test organization',
            'organization_type': 'COMPANY'
        }
        
        with patch.object(EventBus, 'publish') as mock_publish:
            result = self.org_service.create_organization(self.owner, org_data)
            
            self.assertTrue(result['success'])
            self.assertIn('organization', result)
            self.assertEqual(result['organization'].name, 'Test Organization')
            self.assertEqual(result['organization'].owner, self.owner)
            
            # Vérifier qu'un événement a été publié
            mock_publish.assert_called()
    
    def test_add_member_to_organization(self):
        """Test d'ajout de membre à une organisation."""
        org = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            owner=self.owner
        )
        
        member = User.objects.create_user(
            email='member@example.com',
            password='testpass123'
        )
        
        with patch.object(EventBus, 'publish') as mock_publish:
            result = self.org_service.add_member(org.id, member.id, 'MEMBER')
            
            self.assertTrue(result['success'])
            self.assertIn('membership', result)
            self.assertEqual(result['membership'].user, member)
            self.assertEqual(result['membership'].role, 'MEMBER')
    
    def test_remove_member_from_organization(self):
        """Test de suppression de membre d'une organisation."""
        org = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            owner=self.owner
        )
        
        member = User.objects.create_user(
            email='member@example.com',
            password='testpass123'
        )
        
        membership = OrganizationMember.objects.create(
            organization=org,
            user=member,
            role='MEMBER'
        )
        
        with patch.object(EventBus, 'publish') as mock_publish:
            result = self.org_service.remove_member(org.id, member.id)
            
            self.assertTrue(result['success'])
            
            # Vérifier que le membre a été supprimé
            self.assertFalse(
                OrganizationMember.objects.filter(
                    organization=org,
                    user=member
                ).exists()
            )
    
    def test_update_member_role(self):
        """Test de mise à jour du rôle d'un membre."""
        org = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            owner=self.owner
        )
        
        member = User.objects.create_user(
            email='member@example.com',
            password='testpass123'
        )
        
        membership = OrganizationMember.objects.create(
            organization=org,
            user=member,
            role='MEMBER'
        )
        
        result = self.org_service.update_member_role(org.id, member.id, 'ADMIN')
        
        self.assertTrue(result['success'])
        
        # Vérifier que le rôle a été mis à jour
        membership.refresh_from_db()
        self.assertEqual(membership.role, 'ADMIN')


class BillingServiceTestCase(TestCase):
    """Tests pour BillingService."""
    
    def setUp(self):
        self.billing_service = BillingService()
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
        )
        self.org = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            owner=self.user
        )
    
    @patch('stripe.Customer.create')
    def test_create_subscription(self, mock_stripe_customer):
        """Test de création d'abonnement."""
        mock_stripe_customer.return_value = Mock(id='cus_test123')
        
        subscription_data = {
            'plan_name': 'Premium',
            'plan_price': Decimal('29.99'),
            'billing_cycle': 'MONTHLY'
        }
        
        with patch.object(EventBus, 'publish') as mock_publish:
            result = self.billing_service.create_subscription(
                self.org.id,
                subscription_data
            )
            
            self.assertTrue(result['success'])
            self.assertIn('subscription', result)
            self.assertEqual(result['subscription'].plan_name, 'Premium')
    
    def test_calculate_prorated_amount(self):
        """Test de calcul de montant proratisé."""
        from datetime import date, timedelta
        abonnement = Abonnement.objects.create(
            organization=self.org,
            type_abonnement_id=1,
            date_debut=date.today(),
            date_fin=date.today() + timedelta(days=30)
        )
        
        # Test avec 15 jours restants sur 30
        prorated = self.billing_service.calculate_prorated_amount(
            abonnement,
            days_remaining=15,
            total_days=30
        )
        
        self.assertEqual(prorated, Decimal('15.00'))
    
    def test_cancel_subscription(self):
        """Test d'annulation d'abonnement."""
        from datetime import date, timedelta
        abonnement = Abonnement.objects.create(
            organization=self.org,
            type_abonnement_id=1,
            date_debut=date.today(),
            date_fin=date.today() + timedelta(days=30),
            status='ACTIVE'
        )
        
        with patch.object(EventBus, 'publish') as mock_publish:
            result = self.billing_service.cancel_subscription(abonnement.id)
            
            self.assertTrue(result['success'])
            
            # Vérifier que l'abonnement a été annulé
            abonnement.refresh_from_db()
            self.assertEqual(abonnement.status, 'ANNULE')


class VerificationServiceTestCase(TestCase):
    """Tests pour VerificationService."""
    
    def setUp(self):
        self.verification_service = VerificationService()
        self.user = User.objects.create_user(
            email='entreprise@example.com',
            password='testpass123',
            user_type='ENTREPRISE'
        )
        self.entreprise = Entreprise.objects.create(
            user=self.user,
            company_name='Test Company',
            siret='73282932000074'
        )
    
    def test_start_verification_process(self):
        """Test de démarrage du processus de vérification."""
        with patch.object(EventBus, 'publish') as mock_publish:
            result = self.verification_service.start_verification(
                self.entreprise.id,
                'KYB_FULL'
            )
            
            self.assertTrue(result['success'])
            self.assertIn('verification_request', result)
            self.assertEqual(
                result['verification_request'].request_type,
                'KYB_FULL'
            )
            self.assertEqual(
                result['verification_request'].status,
                'PENDING'
            )
    
    def test_submit_verification_document(self):
        """Test de soumission de document de vérification."""
        verification = DocumentVerification.objects.create(
            entreprise=self.entreprise,
            type_verification='KYB_COMPLET'
        )
        
        # Mock du fichier
        mock_file = Mock()
        mock_file.name = 'kbis.pdf'
        mock_file.size = 1024
        
        with patch.object(EventBus, 'publish') as mock_publish:
            result = self.verification_service.submit_document(
                verification.id,
                'KBIS',
                mock_file
            )
            
            self.assertTrue(result['success'])
            self.assertIn('document', result)
    
    def test_approve_verification(self):
        """Test d'approbation de vérification."""
        verification = DocumentVerification.objects.create(
            entreprise=self.entreprise,
            type_verification='KYB_COMPLET',
            status='EN_COURS'
        )
        
        with patch.object(EventBus, 'publish') as mock_publish:
            result = self.verification_service.approve_verification(
                verification.id,
                'Verification approved'
            )
            
            self.assertTrue(result['success'])
            
            # Vérifier que la vérification a été approuvée
            verification.refresh_from_db()
            self.assertEqual(verification.status, 'APPROUVE')
            
            # Vérifier que l'entreprise est maintenant vérifiée
            self.entreprise.refresh_from_db()
            self.assertTrue(self.entreprise.is_verified)
    
    def test_reject_verification(self):
        """Test de rejet de vérification."""
        verification = DocumentVerification.objects.create(
            entreprise=self.entreprise,
            type_verification='KYB_COMPLET',
            status='EN_COURS'
        )
        
        with patch.object(EventBus, 'publish') as mock_publish:
            result = self.verification_service.reject_verification(
                verification.id,
                'Documents incomplets'
            )
            
            self.assertTrue(result['success'])
            
            # Vérifier que la vérification a été rejetée
            verification.refresh_from_db()
            self.assertEqual(verification.status, 'REJETE')


class EventBusTestCase(TestCase):
    """Tests pour EventBus."""
    
    def test_publish_event(self):
        """Test de publication d'événement."""
        event_data = {'test': 'data'}
        
        # Mock du logger
        with patch('logging.getLogger') as mock_logger:
            mock_log_instance = Mock()
            mock_logger.return_value = mock_log_instance
            
            EventBus.publish('test.event', event_data)
            
            # Vérifier que l'événement a été loggé
            mock_log_instance.info.assert_called()
    
    def test_subscribe_to_event(self):
        """Test d'abonnement à un événement."""
        callback_called = False
        
        def test_callback(event_type, data):
            nonlocal callback_called
            callback_called = True
        
        EventBus.subscribe('test.event', test_callback)
        EventBus.publish('test.event', {'test': 'data'})
        
        self.assertTrue(callback_called)
    
    def test_unsubscribe_from_event(self):
        """Test de désabonnement d'un événement."""
        callback_called = False
        
        def test_callback(event_type, data):
            nonlocal callback_called
            callback_called = True
        
        EventBus.subscribe('test.event', test_callback)
        EventBus.unsubscribe('test.event', test_callback)
        EventBus.publish('test.event', {'test': 'data'})
        
        self.assertFalse(callback_called)
