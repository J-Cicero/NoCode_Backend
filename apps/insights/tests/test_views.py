"""
Tests pour les vues du module Insights.
"""
from unittest.mock import patch, MagicMock
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.foundation.models import Organization, Project
from apps.runtime.models import GeneratedApp
from ..models import UserActivity, SystemMetric, ApplicationMetric, UserMetric

User = get_user_model()

class UserActivityViewSetTest(APITestCase):
    """Tests pour le ViewSet UserActivityViewSet."""

    def setUp(self):
        """Configuration initiale pour les tests."""
        self.organization = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            organization=self.organization,
            is_active=True
        )
        self.other_org = Organization.objects.create(name="Other Org")
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            organization=self.other_org,
            is_active=True
        )

        # Créer des activités de test
        self.activity1 = UserActivity.objects.create(
            user=self.user,
            organization=self.organization,
            activity_type='user.login',
            description='Test login'
        )
        self.activity2 = UserActivity.objects.create(
            user=self.user,
            organization=self.organization,
            activity_type='project.created',
            description='Test project creation'
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_activities_authenticated(self):
        """Test de la liste des activités pour un utilisateur authentifié."""
        url = reverse('user-activity-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_list_activities_unauthorized_org(self):
        """Test d'accès aux activités d'une autre organisation."""
        self.client.force_authenticate(user=self.other_user)

        url = reverse('user-activity-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_filter_activities_by_type(self):
        """Test du filtrage des activités par type."""
        url = reverse('user-activity-filter')
        response = self.client.get(url, {'activity_type': 'user.login'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['activity_type'], 'user.login')

    def test_filter_activities_by_date_range(self):
        """Test du filtrage des activités par plage de dates."""
        url = reverse('user-activity-filter')
        start_date = (timezone.now() - timezone.timedelta(days=1)).strftime('%Y-%m-%d')
        end_date = (timezone.now() + timezone.timedelta(days=1)).strftime('%Y-%m-%d')

        response = self.client.get(url, {
            'start_date': start_date,
            'end_date': end_date
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_unauthenticated_access(self):
        """Test d'accès non authentifié."""
        self.client.force_authenticate(user=None)

        url = reverse('user-activity-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TrackEventTest(APITestCase):
    """Tests pour l'API de tracking d'événements."""

    def setUp(self):
        """Configuration initiale pour les tests."""
        self.organization = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            organization=self.organization,
            is_active=True
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_track_valid_event(self):
        """Test du tracking d'un événement valide."""
        url = reverse('track-event')
        data = {
            'event_type': 'button_click',
            'event_data': {
                'button_name': 'submit',
                'page': 'dashboard'
            }
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'tracked')
        self.assertIn('event_id', response.data)

        # Vérifier que l'activité a été créée
        activity = UserActivity.objects.filter(
            activity_type='tracking.button_click',
            user=self.user
        ).first()
        self.assertIsNotNone(activity)

    def test_track_invalid_event_type(self):
        """Test du tracking d'un type d'événement invalide."""
        url = reverse('track-event')
        data = {
            'event_type': 'invalid_event_type',
            'event_data': {}
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('event_type', response.data)

    def test_track_event_unauthenticated(self):
        """Test du tracking sans authentification."""
        self.client.force_authenticate(user=None)

        url = reverse('track-event')
        data = {
            'event_type': 'page_view',
            'event_data': {}
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AnalyticsReportTest(APITestCase):
    """Tests pour l'API de rapports d'analytics."""

    def setUp(self):
        """Configuration initiale pour les tests."""
        self.organization = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            organization=self.organization,
            is_active=True
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch('apps.insights.views.AnalyticsService.generate_analytics_report')
    def test_generate_analytics_report_success(self, mock_generate):
        """Test de génération réussie d'un rapport d'analytics."""
        # Configurer le mock
        mock_generate.return_value = {
            'organization_id': str(self.organization.id),
            'period': {'start': '2024-01-01', 'end': '2024-01-31'},
            'metrics': {'user_activity': {'total': 100}}
        }

        url = reverse('analytics-report')
        data = {
            'organization_id': str(self.organization.id),
            'start_date': '2024-01-01',
            'end_date': '2024-01-31'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('organization_id', response.data)
        self.assertIn('period', response.data)
        self.assertIn('metrics', response.data)

        # Vérifier que la méthode de service a été appelée
        mock_generate.assert_called_once()

    def test_generate_analytics_report_invalid_data(self):
        """Test de génération de rapport avec données invalides."""
        url = reverse('analytics-report')
        data = {
            'organization_id': 'invalid-uuid',
            'start_date': 'invalid-date',
            'end_date': '2024-01-31'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('apps.insights.views.AnalyticsService.generate_analytics_report')
    def test_generate_analytics_report_service_error(self, mock_generate):
        """Test de gestion d'erreur du service d'analytics."""
        # Configurer le mock pour lever une exception
        mock_generate.side_effect = Exception("Erreur de service")

        url = reverse('analytics-report')
        data = {
            'organization_id': str(self.organization.id),
            'start_date': '2024-01-01',
            'end_date': '2024-01-31'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)


class PerformanceReportTest(APITestCase):
    """Tests pour l'API de rapports de performance."""

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
            status="deployed"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch('apps.insights.views.AnalyticsService.generate_performance_report')
    def test_generate_performance_report_success(self, mock_generate):
        """Test de génération réussie d'un rapport de performance."""
        # Configurer le mock
        mock_generate.return_value = {
            'app_id': str(self.app.id),
            'period': {'start': '2024-01-01', 'end': '2024-01-31'},
            'performance': {'response_time': {'avg': 245}}
        }

        url = reverse('performance-report')
        data = {
            'app_id': str(self.app.id),
            'start_date': '2024-01-01',
            'end_date': '2024-01-31'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('app_id', response.data)
        self.assertIn('performance', response.data)

        # Vérifier que la méthode de service a été appelée
        mock_generate.assert_called_once()

    def test_generate_performance_report_unauthorized_app(self):
        """Test d'accès non autorisé à une application."""
        # Créer une autre organisation et application
        other_org = Organization.objects.create(name="Other Org")
        other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
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
            status="deployed"
        )

        url = reverse('performance-report')
        data = {
            'app_id': str(other_app.id),
            'start_date': '2024-01-01',
            'end_date': '2024-01-31'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('apps.insights.views.AnalyticsService.generate_performance_report')
    def test_generate_performance_report_app_not_found(self, mock_generate):
        """Test de génération de rapport pour une application inexistante."""
        # Configurer le mock pour lever une exception
        mock_generate.side_effect = ValueError("Application non trouvée")

        url = reverse('performance-report')
        data = {
            'app_id': '550e8400-e29b-41d4-a716-446655440000',  # UUID invalide
            'start_date': '2024-01-01',
            'end_date': '2024-01-31'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
