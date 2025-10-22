"""
Tests pour les tâches asynchrones du module runtime.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.foundation.models import Organization, Project
from ..models import GeneratedApp, DeploymentLog
from ..tasks import deploy_app_task

User = get_user_model()

class DeployAppTaskTest(TestCase):
    """Tests pour la tâche de déploiement d'application."""

    def setUp(self):
        self.organization = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            organization=self.organization
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

    @patch('apps.runtime.tasks.DeploymentManager')
    def test_deploy_app_task_success(self, mock_deployment_manager):
        """Test de la tâche de déploiement réussie."""
        # Configurer le mock pour simuler un déploiement réussi
        mock_manager = MagicMock()
        mock_deployment_manager.return_value = mock_manager
        mock_manager.deploy.return_value = True

        # Appeler la tâche
        result = deploy_app_task(self.deployment.id)

        # Vérifier les résultats
        self.assertEqual(result['status'], 'success')

        # Rafraîchir les objets depuis la base de données
        self.deployment.refresh_from_db()
        self.app.refresh_from_db()

        # Vérifier que le déploiement est marqué comme terminé
        self.assertEqual(self.deployment.status, 'completed')
        self.assertIsNotNone(self.deployment.completed_at)

        # Vérifier que l'application est marquée comme déployée
        self.assertEqual(self.app.status, 'deployed')
        self.assertEqual(self.app.last_deployed_at, self.deployment.completed_at)

    @patch('apps.runtime.tasks.DeploymentManager')
    def test_deploy_app_task_failure(self, mock_deployment_manager):
        """Test de la tâche de déploiement échoué."""
        # Configurer le mock pour simuler une exception
        mock_manager = MagicMock()
        mock_deployment_manager.return_value = mock_manager
        mock_manager.deploy.side_effect = Exception("Erreur de déploiement")

        # Appeler la tâche
        result = deploy_app_task(self.deployment.id)

        # Vérifier les résultats
        self.assertEqual(result['status'], 'error')

        # Rafraîchir les objets depuis la base de données
        self.deployment.refresh_from_db()
        self.app.refresh_from_db()

        # Vérifier que le déploiement est marqué comme échoué
        self.assertEqual(self.deployment.status, 'failed')
        self.assertIsNotNone(self.deployment.completed_at)
        self.assertIn('Erreur de déploiement', self.deployment.error_message)

        # Vérifier que l'application est marquée comme en erreur
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, 'error')

    def test_deploy_app_task_invalid_deployment(self):
        """Test de la tâche avec un ID de déploiement invalide."""
        # Appeler la tâche avec un ID qui n'existe pas
        result = deploy_app_task(9999)

        # Vérifier que la tâche retourne une erreur
        self.assertEqual(result['status'], 'error')
        self.assertIn('non trouvé', result['message'].lower())

    def test_deploy_app_task_with_retry_logic(self):
        """Test de la logique de retry dans la tâche."""
        # Configurer le mock pour simuler une exception qui se résout après retry
        mock_manager = MagicMock()
        mock_manager.deploy.side_effect = [
            Exception("Première erreur"),
            Exception("Deuxième erreur"),
            True  # Succès au troisième essai
        ]

        with patch('apps.runtime.tasks.DeploymentManager') as mock_deployment_manager:
            mock_deployment_manager.return_value = mock_manager

            # Appeler la tâche
            result = deploy_app_task(self.deployment.id)

            # Vérifier que la tâche a réussi après les retries
            self.assertEqual(result['status'], 'success')

            # Vérifier que deploy a été appelé 3 fois (retry automatique)
            self.assertEqual(mock_manager.deploy.call_count, 3)

    def test_deploy_app_task_with_details(self):
        """Test de la tâche avec détails de déploiement."""
        # Configurer le mock pour retourner des détails de déploiement
        mock_manager = MagicMock()
        mock_deployment_manager.return_value = mock_manager
        mock_manager.deploy.return_value = {
            'api_url': 'https://api.example.com',
            'admin_url': 'https://admin.example.com',
            'status': 'deployed'
        }

        # Appeler la tâche
        result = deploy_app_task(self.deployment.id)

        # Vérifier les résultats
        self.assertEqual(result['status'], 'success')

        # Vérifier que les détails sont sauvegardés
        self.deployment.refresh_from_db()
        self.assertIn('api_url', self.deployment.details)
        self.assertIn('admin_url', self.deployment.details)

        # Vérifier que l'application a été mise à jour avec les URLs
        self.app.refresh_from_db()
        self.assertEqual(self.app.api_base_url, 'https://api.example.com')
        self.assertEqual(self.app.admin_url, 'https://admin.example.com')
