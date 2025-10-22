"""
Tests pour les vues du module runtime.
"""
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.foundation.models import Organization, Project
from ..models import GeneratedApp, DeploymentLog

User = get_user_model()

class GeneratedAppViewSetTest(APITestCase):
    """Tests pour le ViewSet GeneratedAppViewSet."""

    def setUp(self):
        """Configuration initiale pour les tests."""
        self.organization = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            organization=self.organization,
            is_active=True
        )
        self.project = Project.objects.create(
            name="Test Project",
            organization=self.organization,
            created_by=self.user
        )
        self.app = GeneratedApp.objects.create(
            name="Test App",
            project=self.project,
            status="draft"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_apps_authenticated(self):
        """Test de la liste des applications pour un utilisateur authentifié."""
        url = reverse('app-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test App')

    def test_create_app(self):
        """Test de création d'une application."""
        url = reverse('app-list')
        data = {
            'name': 'New Test App',
            'project': self.project.id,
            'status': 'draft',
            'config': {'key': 'value'}
        }

        with patch('apps.runtime.views.AppGenerator') as mock_generator:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = None
            mock_generator.return_value = mock_instance

            response = self.client.post(url, data, format='json')

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(GeneratedApp.objects.count(), 2)

            app = GeneratedApp.objects.latest('created_at')
            self.assertEqual(app.name, 'New Test App')
            self.assertEqual(app.status, 'generated')
            self.assertEqual(app.project, self.project)

    @patch('apps.runtime.views.AppGenerator')
    def test_deploy_app(self, mock_generator):
        """Test du déploiement d'une application."""
        # Préparer l'application dans un état déployable
        self.app.status = 'generated'
        self.app.save()

        url = reverse('app-deploy', args=[self.app.id])
        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data['status'], 'déploiement démarré')

        # Vérifier qu'un journal de déploiement a été créé
        deployment = DeploymentLog.objects.first()
        self.assertIsNotNone(deployment)
        self.assertEqual(deployment.app, self.app)
        self.assertEqual(deployment.status, 'pending')

        # Vérifier que l'application est en attente de déploiement
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, 'deployment_pending')

    def test_deploy_app_not_generated(self):
        """Test du déploiement d'une application non générée."""
        url = reverse('app-deploy', args=[self.app.id])
        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_unauthorized_access(self):
        """Test d'accès non autorisé à une application d'une autre organisation."""
        # Créer un autre utilisateur dans une autre organisation
        other_org = Organization.objects.create(name="Autre Organisation")
        other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            organization=other_org,
            is_active=True
        )

        # Se connecter en tant que l'autre utilisateur
        self.client.force_authenticate(user=other_user)

        # Essayer d'accéder à l'application
        url = reverse('app-detail', args=[self.app.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_superuser_access_all_apps(self):
        """Test que les superutilisateurs peuvent voir toutes les applications."""
        # Créer un superutilisateur
        superuser = User.objects.create_superuser(
            email="admin@test.com",
            password="admin123"
        )

        # Créer une application dans une autre organisation
        other_org = Organization.objects.create(name="Autre Org")
        other_user = User.objects.create_user(
            email="other@test.com",
            password="test123",
            organization=other_org
        )
        other_project = Project.objects.create(
            name="Other Project",
            organization=other_org,
            created_by=other_user
        )
        other_app = GeneratedApp.objects.create(
            name="Other App",
            project=other_project,
            status="draft"
        )

        # Se connecter en tant que superutilisateur
        self.client.force_authenticate(user=superuser)

        # Vérifier qu'il voit toutes les applications
        url = reverse('app-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_unauthenticated_access(self):
        """Test d'accès non authentifié."""
        # Se déconnecter
        self.client.force_authenticate(user=None)

        url = reverse('app-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DeploymentLogViewSetTest(APITestCase):
    """Tests pour le ViewSet DeploymentLogViewSet."""

    def setUp(self):
        """Configuration initiale pour les tests."""
        self.organization = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            email="deploy@example.com",
            password="testpass123",
            organization=self.organization,
            is_active=True
        )
        self.project = Project.objects.create(
            name="Test Project",
            organization=self.organization,
            created_by=self.user
        )
        self.app = GeneratedApp.objects.create(
            name="Test App",
            project=self.project,
            status="generated"
        )
        self.deployment = DeploymentLog.objects.create(
            app=self.app,
            status="pending",
            performed_by=self.user
        )
        self.client = APITestCase()
        self.client.force_authenticate(user=self.user)

    def test_list_deployments(self):
        """Test de la liste des déploiements."""
        url = reverse('deployment-log-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['status'], 'pending')

    def test_retry_deployment(self):
        """Test de relance d'un déploiement."""
        self.deployment.status = 'failed'
        self.deployment.save()

        with patch('apps.runtime.views.deploy_app_task.delay') as mock_task:
            mock_task.return_value = MagicMock(id='task-123')

            url = reverse('deployment-log-retry', args=[self.deployment.id])
            response = self.client.post(url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(DeploymentLog.objects.count(), 2)

            # Vérifier qu'une nouvelle entrée de journal a été créée
            new_deployment = DeploymentLog.objects.latest('started_at')
            self.assertEqual(new_deployment.status, 'pending')
            self.assertEqual(new_deployment.app, self.app)

            # Vérifier que la tâche a été planifiée
            mock_task.assert_called_once_with(new_deployment.id)

    def test_retry_not_failed_deployment(self):
        """Test de relance d'un déploiement qui n'a pas échoué."""
        self.deployment.status = 'completed'
        self.deployment.save()

        url = reverse('deployment-log-retry', args=[self.deployment.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_unauthorized_deployment_retry(self):
        """Test de relance non autorisée d'un déploiement."""
        # Créer un utilisateur dans une autre organisation
        other_org = Organization.objects.create(name="Autre Org")
        other_user = User.objects.create_user(
            email="other@test.com",
            password="test123",
            organization=other_org
        )

        self.client.force_authenticate(user=other_user)

        url = reverse('deployment-log-retry', args=[self.deployment.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_superuser_access_all_deployments(self):
        """Test que les superutilisateurs peuvent voir tous les déploiements."""
        # Créer un superutilisateur
        superuser = User.objects.create_superuser(
            email="admin@test.com",
            password="admin123"
        )

        # Créer un déploiement dans une autre organisation
        other_org = Organization.objects.create(name="Autre Org")
        other_user = User.objects.create_user(
            email="other@test.com",
            password="test123",
            organization=other_org
        )
        other_project = Project.objects.create(
            name="Other Project",
            organization=other_org,
            created_by=other_user
        )
        other_app = GeneratedApp.objects.create(
            name="Other App",
            project=other_project,
            status="generated"
        )
        other_deployment = DeploymentLog.objects.create(
            app=other_app,
            status="pending",
            performed_by=other_user
        )

        # Se connecter en tant que superutilisateur
        self.client.force_authenticate(user=superuser)

        # Vérifier qu'il voit tous les déploiements
        url = reverse('deployment-log-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
