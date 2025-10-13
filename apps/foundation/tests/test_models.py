"""
Tests pour les modèles du module Foundation.
"""
from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from ..models import (
    Client, Organization, OrganizationMember, OrganizationInvitation,
    Abonnement, Facture, MoyenDePaiement, DocumentVerification, DocumentUpload
)

User = get_user_model()


class UserModelTestCase(TestCase):
    """Tests pour le modèle User personnalisé."""
    
    def test_create_client_user(self):
        """Test de création d'un utilisateur client."""
        user = User.objects.create_user(
            email='client@example.com',
            password='testpass123',
            user_type='CLIENT'
        )
        
        self.assertEqual(user.email, 'client@example.com')
        self.assertEqual(user.user_type, 'CLIENT')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_create_entreprise_user(self):
        """Test de création d'un utilisateur entreprise."""
        user = User.objects.create_user(
            email='entreprise@example.com',
            password='testpass123',
            user_type='ENTREPRISE'
        )
        
        self.assertEqual(user.user_type, 'ENTREPRISE')
        self.assertTrue(user.is_active)
    
    def test_unique_email_constraint(self):
        """Test de contrainte d'unicité sur l'email."""
        User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email='test@example.com',
                password='testpass456'
            )


class ClientModelTestCase(TestCase):
    """Tests pour le modèle Client."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='client@example.com',
            password='testpass123',
            user_type='CLIENT'
        )
    
    def test_create_client(self):
        """Test de création d'un profil client."""
        client = Client.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            phone='+33123456789',
            date_of_birth='1990-01-01'
        )
        
        self.assertEqual(client.user, self.user)
        self.assertEqual(client.first_name, 'John')
        self.assertEqual(client.last_name, 'Doe')
        self.assertEqual(str(client), 'John Doe')
    
    def test_client_full_name_property(self):
        """Test de la propriété full_name."""
        client = Client.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe'
        )
        
        self.assertEqual(client.full_name, 'John Doe')




class OrganizationModelTestCase(TestCase):
    """Tests pour le modèle Organization."""
    
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com',
            password='testpass123'
        )
    
    def test_create_organization(self):
        """Test de création d'une organisation."""
        org = Organization.objects.create(
            name='Test Organization',
            slug='test-organization',
            owner=self.owner,
            organization_type='COMPANY'
        )
        
        self.assertEqual(org.name, 'Test Organization')
        self.assertEqual(org.slug, 'test-organization')
        self.assertEqual(org.owner, self.owner)
        self.assertTrue(org.is_active)
        self.assertEqual(str(org), 'Test Organization')
    
    def test_organization_member_count(self):
        """Test du comptage des membres."""
        org = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            owner=self.owner
        )
        
        # Le propriétaire est automatiquement membre
        self.assertEqual(org.member_count, 0)  # Pas encore de membres ajoutés
        
        # Ajouter un membre
        member = User.objects.create_user(
            email='member@example.com',
            password='testpass123'
        )
        
        OrganizationMember.objects.create(
            organization=org,
            user=member,
            role='MEMBER'
        )
        
        self.assertEqual(org.member_count, 1)


class OrganizationMemberTestCase(TestCase):
    """Tests pour le modèle OrganizationMember."""
    
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com',
            password='testpass123'
        )
        self.member = User.objects.create_user(
            email='member@example.com',
            password='testpass123'
        )
        self.org = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            owner=self.owner
        )
    
    def test_create_organization_member(self):
        """Test de création d'un membre d'organisation."""
        membership = OrganizationMember.objects.create(
            organization=self.org,
            user=self.member,
            role='MEMBER'
        )
        
        self.assertEqual(membership.organization, self.org)
        self.assertEqual(membership.user, self.member)
        self.assertEqual(membership.role, 'MEMBER')
        self.assertEqual(membership.status, 'ACTIVE')
        self.assertEqual(str(membership), f'{self.member.email} - Test Organization (MEMBER)')
    
    def test_unique_organization_member(self):
        """Test de contrainte d'unicité organisation-utilisateur."""
        OrganizationMember.objects.create(
            organization=self.org,
            user=self.member,
            role='MEMBER'
        )
        
        with self.assertRaises(IntegrityError):
            OrganizationMember.objects.create(
                organization=self.org,
                user=self.member,
                role='ADMIN'
            )


class AbonnementModelTestCase(TestCase):
    """Tests pour le modèle Abonnement."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
        )
        self.org = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            owner=self.user
        )
    
    def test_create_abonnement(self):
        """Test de création d'un abonnement."""
        abonnement = Abonnement.objects.create(
            organization=self.org,
            type_abonnement_id=1,
            date_debut=datetime.now().date(),
            date_fin=datetime.now().date() + timedelta(days=30)
        )
        
        self.assertEqual(abonnement.organization, self.org)
        self.assertEqual(abonnement.status, 'ACTIVE')
        self.assertTrue(abonnement.is_active)
    
    def test_abonnement_expiry(self):
        """Test de l'expiration d'abonnement."""
        past_date = datetime.now().date() - timedelta(days=1)
        abonnement = Abonnement.objects.create(
            organization=self.org,
            type_abonnement_id=1,
            date_debut=past_date - timedelta(days=30),
            date_fin=past_date
        )
        
        self.assertTrue(abonnement.is_expired)


class FactureModelTestCase(TestCase):
    """Tests pour le modèle Facture."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
        )
        self.org = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            owner=self.user
        )
    
    def test_create_facture(self):
        """Test de création d'une facture."""
        facture = Facture.objects.create(
            organization=self.org,
            numero_facture='INV-2024-001',
            montant_ht=Decimal('24.99'),
            montant_tva=Decimal('5.00'),
            montant_ttc=Decimal('29.99')
        )
        
        self.assertEqual(facture.organization, self.org)
        self.assertEqual(facture.montant_ttc, Decimal('29.99'))
        self.assertEqual(facture.status, 'BROUILLON')
        self.assertEqual(str(facture), 'INV-2024-001 - Test Organization')
    
    def test_facture_total_calculation(self):
        """Test du calcul du total de facture."""
        facture = Facture.objects.create(
            organization=self.org,
            numero_facture='INV-2024-001',
            montant_ht=Decimal('100.00'),
            montant_tva=Decimal('20.00'),
            montant_ttc=Decimal('120.00')
        )
        
        self.assertEqual(facture.montant_ht + facture.montant_tva, facture.montant_ttc)


class DocumentVerificationTestCase(TestCase):
    """Tests pour le modèle DocumentVerification."""
    
    def setUp(self):
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
    
    def test_create_document_verification(self):
        """Test de création d'une demande de vérification."""
        verification = DocumentVerification.objects.create(
            entreprise=self.entreprise,
            type_verification='KYB_COMPLET'
        )
        
        self.assertEqual(verification.entreprise, self.entreprise)
        self.assertEqual(verification.type_verification, 'KYB_COMPLET')
        self.assertEqual(verification.status, 'EN_ATTENTE')
        self.assertEqual(str(verification), f'KYB_COMPLET - {self.entreprise.company_name}')
    
    def test_verification_completion(self):
        """Test de finalisation de vérification."""
        verification = DocumentVerification.objects.create(
            entreprise=self.entreprise,
            type_verification='KYB_COMPLET'
        )
        
        verification.status = 'APPROUVE'
        verification.date_finalisation = datetime.now()
        verification.save()
        
        self.assertEqual(verification.status, 'APPROUVE')
        self.assertIsNotNone(verification.date_finalisation)


class DocumentUploadTestCase(TestCase):
    """Tests pour le modèle DocumentUpload."""
    
    def setUp(self):
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
        self.verification = DocumentVerification.objects.create(
            entreprise=self.entreprise,
            type_verification='KYB_COMPLET'
        )
    
    def test_create_document_upload(self):
        """Test de création d'un document uploadé."""
        document = DocumentUpload.objects.create(
            verification=self.verification,
            type_document='KBIS',
            nom_fichier='kbis.pdf',
            taille_fichier=1024,
            chemin_fichier='/documents/kbis.pdf'
        )
        
        self.assertEqual(document.verification, self.verification)
        self.assertEqual(document.type_document, 'KBIS')
        self.assertEqual(document.nom_fichier, 'kbis.pdf')
        self.assertEqual(document.status, 'UPLOADE')
        self.assertEqual(str(document), 'KBIS - kbis.pdf')
    
    def test_document_validation(self):
        """Test de validation de document."""
        document = DocumentUpload.objects.create(
            verification=self.verification,
            type_document='KBIS',
            nom_fichier='kbis.pdf',
            taille_fichier=1024,
            chemin_fichier='/documents/kbis.pdf'
        )
        
        document.status = 'VALIDE'
        document.date_validation = datetime.now()
        document.save()
        
        self.assertEqual(document.status, 'VALIDE')
        self.assertIsNotNone(document.date_validation)
