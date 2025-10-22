"""
Tests pour les modèles du module Insights.
"""
import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from apps.foundation.models import Organization, Project
from apps.runtime.models import GeneratedApp
from ..models import UserActivity, SystemMetric, ApplicationMetric, UserMetric, PerformanceMetric

User = get_user_model()

class UserActivityModelTest(TestCase):
    """Tests pour le modèle UserActivity."""

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

    def test_create_user_activity(self):
        """Test de création d'une activité utilisateur."""
        activity = UserActivity.objects.create(
            user=self.user,
            organization=self.organization,
            activity_type='user.login',
            description='Test de connexion',
            metadata={'test': True},
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )

        self.assertEqual(activity.user, self.user)
        self.assertEqual(activity.organization, self.organization)
        self.assertEqual(activity.activity_type, 'user.login')
        self.assertEqual(activity.description, 'Test de connexion')
        self.assertEqual(activity.metadata, {'test': True})
        self.assertEqual(activity.ip_address, '127.0.0.1')
        self.assertEqual(activity.user_agent, 'Test Agent')
        self.assertIsNotNone(activity.created_at)

    def test_activity_with_content_object(self):
        """Test d'activité avec objet générique associé."""
        activity = UserActivity.objects.create(
            user=self.user,
            organization=self.organization,
            activity_type='project.created',
            content_type=ContentType.objects.get_for_model(Project),
            object_id=self.project.id
        )

        self.assertEqual(activity.content_object, self.project)

    def test_activity_str_representation(self):
        """Test de la représentation string d'une activité."""
        activity = UserActivity.objects.create(
            user=self.user,
            organization=self.organization,
            activity_type='user.login'
        )

        expected_str = f"{self.user} - user.login - {activity.created_at.strftime('%Y-%m-%d')}"
        self.assertIn(str(activity), expected_str)


class SystemMetricModelTest(TestCase):
    """Tests pour le modèle SystemMetric."""

    def test_create_system_metric(self):
        """Test de création d'une métrique système."""
        metric = SystemMetric.objects.create(
            metric_type='cpu.usage',
            value=45.5,
            unit='%',
            hostname='localhost',
            service='web'
        )

        self.assertEqual(metric.metric_type, 'cpu.usage')
        self.assertEqual(metric.value, 45.5)
        self.assertEqual(metric.unit, '%')
        self.assertEqual(metric.hostname, 'localhost')
        self.assertEqual(metric.service, 'web')
        self.assertIsNotNone(metric.created_at)


class ApplicationMetricModelTest(TestCase):
    """Tests pour le modèle ApplicationMetric."""

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
        self.app = GeneratedApp.objects.create(
            name="Test App",
            project=self.project,
            status="generated"
        )

    def test_create_application_metric(self):
        """Test de création d'une métrique d'application."""
        metric = ApplicationMetric.objects.create(
            app=self.app,
            metric_type='response.time',
            value=245.5,
            unit='ms',
            environment='production',
            metadata={'endpoint': '/api/test'}
        )

        self.assertEqual(metric.app, self.app)
        self.assertEqual(metric.metric_type, 'response.time')
        self.assertEqual(metric.value, 245.5)
        self.assertEqual(metric.unit, 'ms')
        self.assertEqual(metric.environment, 'production')
        self.assertEqual(metric.metadata, {'endpoint': '/api/test'})
        self.assertIsNotNone(metric.created_at)


class UserMetricModelTest(TestCase):
    """Tests pour le modèle UserMetric."""

    def setUp(self):
        """Configuration initiale pour les tests."""
        self.organization = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            organization=self.organization
        )

    def test_create_user_metric(self):
        """Test de création d'une métrique utilisateur."""
        today = timezone.now().date()
        metric = UserMetric.objects.create(
            user=self.user,
            organization=self.organization,
            metric_type='session.duration',
            value=25.5,
            date=today,
            context={'page': 'dashboard'}
        )

        self.assertEqual(metric.user, self.user)
        self.assertEqual(metric.organization, self.organization)
        self.assertEqual(metric.metric_type, 'session.duration')
        self.assertEqual(metric.value, 25.5)
        self.assertEqual(metric.date, today)
        self.assertEqual(metric.context, {'page': 'dashboard'})
        self.assertIsNotNone(metric.created_at)

    def test_user_metric_unique_constraint(self):
        """Test de la contrainte d'unicité par utilisateur, type et date."""
        today = timezone.now().date()

        # Créer une première métrique
        UserMetric.objects.create(
            user=self.user,
            organization=self.organization,
            metric_type='pages.visited',
            value=10,
            date=today
        )

        # Tenter de créer une deuxième métrique identique (devrait échouer)
        with self.assertRaises(Exception):  # Django va lever une exception d'intégrité
            UserMetric.objects.create(
                user=self.user,
                organization=self.organization,
                metric_type='pages.visited',
                value=15,
                date=today
            )


class PerformanceMetricModelTest(TestCase):
    """Tests pour le modèle PerformanceMetric."""

    def setUp(self):
        """Configuration initiale pour les tests."""
        self.organization = Organization.objects.create(name="Test Org")

    def test_create_performance_metric(self):
        """Test de création d'une métrique de performance."""
        now = timezone.now()
        metric = PerformanceMetric.objects.create(
            category='backend',
            name='response_time',
            value=245.5,
            unit='ms',
            timestamp=now,
            organization=self.organization,
            metadata={'endpoint': '/api/test'}
        )

        self.assertEqual(metric.category, 'backend')
        self.assertEqual(metric.name, 'response_time')
        self.assertEqual(metric.value, 245.5)
        self.assertEqual(metric.unit, 'ms')
        self.assertEqual(metric.timestamp, now)
        self.assertEqual(metric.organization, self.organization)
        self.assertEqual(metric.metadata, {'endpoint': '/api/test'})
        self.assertIsNotNone(metric.created_at)
