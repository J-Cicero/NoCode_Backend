"""
Commande Django pour configurer l'environnement de développement.
Crée des utilisateurs de test et configure les permissions pour Postman.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.foundation.models import Organization, Client, Entreprise

User = get_user_model()


class Command(BaseCommand):
    help = 'Configure l\'environnement de développement avec des données de test'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Supprime et recrée les données de test',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('🗑️  Suppression des données de test existantes...')
            User.objects.filter(email__endswith='@test.dev').delete()

        self.stdout.write('🚀 Configuration de l\'environnement de développement...')
        
        with transaction.atomic():
            # Créer un utilisateur client de test
            client_user = self.create_client_user()
            
            # Créer un utilisateur entreprise de test
            entreprise_user = self.create_entreprise_user()
            
            # Créer une organisation de test
            org = self.create_test_organization(client_user)
            
            # Afficher les informations de connexion
            self.display_test_credentials(client_user, entreprise_user)

    def create_client_user(self):
        """Crée un utilisateur client de test."""
        self.stdout.write('👤 Création d\'un utilisateur client de test...')
        
        user, created = User.objects.get_or_create(
            email='client@test.dev',
            defaults={
                'user_type': 'CLIENT',
                'is_active': True,
                'is_email_verified': True
            }
        )
        
        if created:
            user.set_password('TestPass123!')
            user.save()
            
            # Créer le profil client
            Client.objects.create(
                user=user,
                first_name='John',
                last_name='Doe',
                phone='+33123456789',
                date_of_birth='1990-01-01'
            )
            
            self.stdout.write(
                self.style.SUCCESS('✅ Utilisateur client créé: client@test.dev')
            )
        else:
            self.stdout.write('ℹ️  Utilisateur client existant: client@test.dev')
        
        return user

    def create_entreprise_user(self):
        """Crée un utilisateur entreprise de test."""
        self.stdout.write('🏢 Création d\'un utilisateur entreprise de test...')
        
        user, created = User.objects.get_or_create(
            email='entreprise@test.dev',
            defaults={
                'user_type': 'ENTREPRISE',
                'is_active': True,
                'is_email_verified': True
            }
        )
        
        if created:
            user.set_password('TestPass123!')
            user.save()
            
            # Créer le profil entreprise
            Entreprise.objects.create(
                user=user,
                company_name='Test Company SAS',
                siret='73282932000074',
                legal_form='SAS',
                address='123 Rue de Test',
                postal_code='75001',
                city='Paris',
                country='France',
                is_verified=True  # Pré-vérifiée pour les tests
            )
            
            self.stdout.write(
                self.style.SUCCESS('✅ Utilisateur entreprise créé: entreprise@test.dev')
            )
        else:
            self.stdout.write('ℹ️  Utilisateur entreprise existant: entreprise@test.dev')
        
        return user

    def create_test_organization(self, owner):
        """Crée une organisation de test."""
        self.stdout.write('🏛️  Création d\'une organisation de test...')
        
        org, created = Organization.objects.get_or_create(
            slug='test-organization',
            defaults={
                'name': 'Test Organization',
                'description': 'Organisation de test pour le développement',
                'owner': owner,
                'organization_type': 'COMPANY',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('✅ Organisation créée: Test Organization')
            )
        else:
            self.stdout.write('ℹ️  Organisation existante: Test Organization')
        
        return org

    def display_test_credentials(self, client_user, entreprise_user):
        """Affiche les informations de connexion pour les tests."""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('🎯 INFORMATIONS POUR LES TESTS POSTMAN'))
        self.stdout.write('='*60)
        
        self.stdout.write('\n📋 UTILISATEURS DE TEST:')
        self.stdout.write(f'   👤 Client:')
        self.stdout.write(f'      Email: client@test.dev')
        self.stdout.write(f'      Password: TestPass123!')
        
        self.stdout.write(f'   🏢 Entreprise:')
        self.stdout.write(f'      Email: entreprise@test.dev')
        self.stdout.write(f'      Password: TestPass123!')
        
        self.stdout.write('\n🔗 ENDPOINTS PRINCIPAUX:')
        self.stdout.write('   POST /api/auth/register/ - Inscription')
        self.stdout.write('   POST /api/auth/login/ - Connexion')
        self.stdout.write('   POST /api/auth/refresh/ - Rafraîchir token')
        self.stdout.write('   GET  /api/organizations/ - Liste organisations')
        self.stdout.write('   POST /api/organizations/ - Créer organisation')
        
        self.stdout.write('\n🔑 AUTHENTIFICATION:')
        self.stdout.write('   1. POST /api/auth/login/ avec email/password')
        self.stdout.write('   2. Récupérer le token "access" de la réponse')
        self.stdout.write('   3. Ajouter header: Authorization: Bearer <token>')
        
        self.stdout.write('\n⚠️  CONFIGURATION CORS:')
        self.stdout.write('   - CORS activé pour localhost')
        self.stdout.write('   - CSRF désactivé en développement')
        self.stdout.write('   - Rate limiting permissif')
        
        self.stdout.write('\n' + '='*60)
