"""
Tests pour les modèles du module runtime.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.foundation.models import Organization, Project
from ..models import GeneratedApp, DeploymentLog

User = get_user_model()

class GeneratedAppModelTest(TestCase):
    """Tests pour le modèle GeneratedApp."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
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
    
    def test_create_generated_app(self):
        """Test de création d'une application générée."""
        app = GeneratedApp.objects.create(
            name="Test App",
            project=self.project,
            status="draft"
        )
        
        self.assertEqual(app.name, "Test App")
        self.assertEqual(app.status, "draft")
        self.assertEqual(app.project, self.project)
        self.assertIsNotNone(app.created_at)
        self.assertIsNotNone(app.updated_at)

    def test_generate_code_failure(self):
        """Test de l'échec de la génération de code."""
        app = GeneratedApp.objects.create(
            name="Test App",
            project=self.project,
            status="draft"
        )

        # Mock de AppGenerator.generate() pour simuler un échec
        original_generate = app.generate_code
        def mock_generate():
            raise Exception("Erreur de génération")
        app.generate_code = mock_generate

        with self.assertRaises(Exception):
            app.generate_code()
        self.assertEqual(app.status, "error")

        # Restaurer la méthode originale
        app.generate_code = original_generate

    def test_deploy_method_success(self):
        """Test de déploiement réussi."""
        app = GeneratedApp.objects.create(
            name="Test App",
            project=self.project,
            status="generated"
        )

        # Mock des services de déploiement
        with patch('apps.runtime.models.AppGenerator') as mock_generator, \
             patch('apps.runtime.models.DeploymentManager') as mock_manager:

            mock_gen_instance = MagicMock()
            mock_gen_instance.generate.return_value = None
            mock_generator.return_value = mock_gen_instance

            mock_dep_instance = MagicMock()
            mock_dep_instance.deploy.return_value = True
            mock_manager.return_value = mock_dep_instance

            result = app.deploy()

            self.assertTrue(result)
            self.assertEqual(app.status, "deployed")
            self.assertIsNotNone(app.last_deployed_at)

    def test_deploy_method_failure(self):
        """Test de déploiement échoué."""
        app = GeneratedApp.objects.create(
            name="Test App",
            project=self.project,
            status="generated"
        )

        # Mock des services de déploiement pour simuler un échec
        with patch('apps.runtime.models.DeploymentManager') as mock_manager:
            mock_dep_instance = MagicMock()
            mock_dep_instance.deploy.side_effect = Exception("Erreur de déploiement")
            mock_manager.return_value = mock_dep_instance

            result = app.deploy()

            self.assertFalse(result)
            self.assertEqual(app.status, "error")


class DeploymentLogModelTest(TestCase):
    """Tests pour le modèle DeploymentLog."""

    def setUp(self):
        """Configuration initiale pour les tests."""
        self.organization = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            email="deploy@example.com",
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
            status="draft"
        )

    def test_create_deployment_log(self):
        """Test de création d'un journal de déploiement."""
        deployment = DeploymentLog.objects.create(
            app=self.app,
            status="pending",
            performed_by=self.user
        )

        self.assertEqual(deployment.app, self.app)
        self.assertEqual(deployment.status, "pending")
        self.assertEqual(deployment.performed_by, self.user)
        self.assertIsNotNone(deployment.started_at)

    def test_mark_completed_success(self):
        """Test de marquage d'un déploiement comme réussi."""
        deployment = DeploymentLog.objects.create(
            app=self.app,
            status="in_progress",
            performed_by=self.user
        )

        deployment.mark_completed(
            success=True,
            log_output="Déploiement réussi",
            error_message=""
        )

        self.assertEqual(deployment.status, "completed")
        self.assertIsNotNone(deployment.completed_at)
        self.assertEqual(deployment.log_output, "Déploiement réussi")
        self.assertEqual(deployment.error_message, "")

        # Vérifier que l'application a été mise à jour
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "deployed")
        self.assertEqual(self.app.last_deployed_at, deployment.completed_at)

    def test_mark_completed_failure(self):
        """Test de marquage d'un déploiement comme échoué."""
        deployment = DeploymentLog.objects.create(
            app=self.app,
            status="in_progress",
            performed_by=self.user
        )

        deployment.mark_completed(
            success=False,
            log_output="Échec du déploiement",
            error_message="Erreur de connexion"
        )

        self.assertEqual(deployment.status, "failed")
        self.assertIsNotNone(deployment.completed_at)
        self.assertEqual(deployment.log_output, "Échec du déploiement")
        self.assertEqual(deployment.error_message, "Erreur de connexion")

        # Vérifier que l'application a été marquée comme en erreur
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "error")
