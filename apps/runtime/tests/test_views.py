"""
Tests pour les vues du module runtime.
"""
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
    
    def test_list_apps(self):
        """Test de la liste des applications."""
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
            'status': 'draft'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GeneratedApp.objects.count(), 2)
        self.assertEqual(GeneratedApp.objects.get(id=response.data['id']).name, 'New Test App')


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
        self.client = APIClient()
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
        
        url = reverse('deployment-log-retry', args=[self.deployment.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(DeploymentLog.objects.count(), 2)
        self.assertEqual(DeploymentLog.objects.latest('id').status, 'pending')
