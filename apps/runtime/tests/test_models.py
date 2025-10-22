"""
Tests pour les modèles du module runtime.
"""
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
        self.assertIsNotNone(deployment.created_at)
