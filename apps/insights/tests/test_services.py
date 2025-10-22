"""
Tests pour les services du module Insights.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache
from apps.foundation.models import Organization, Project
from apps.runtime.models import GeneratedApp
from ..models import UserActivity, SystemMetric, ApplicationMetric, UserMetric, PerformanceMetric
from ..services import MetricsCollector, AnalyticsService, ActivityTracker

User = get_user_model()

class MetricsCollectorTest(TestCase):
    """Tests pour le service MetricsCollector."""

    def setUp(self):
        """Configuration initiale pour les tests."""
        self.organization = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            organization=self.organization
        )

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_collect_system_metrics(self, mock_disk, mock_memory, mock_cpu):
        """Test de collecte des métriques système."""
        # Configurer les mocks
        mock_cpu.return_value = 45.5
        mock_memory.return_value.percent = 67.8
        mock_disk.return_value.percent = 23.1

        # Appeler la méthode
        MetricsCollector.collect_system_metrics()

        # Vérifier que les métriques ont été créées
        cpu_metric = SystemMetric.objects.filter(metric_type='cpu.usage').first()
        memory_metric = SystemMetric.objects.filter(metric_type='memory.usage').first()
        disk_metric = SystemMetric.objects.filter(metric_type='disk.usage').first()

        self.assertIsNotNone(cpu_metric)
        self.assertIsNotNone(memory_metric)
        self.assertIsNotNone(disk_metric)

        self.assertEqual(cpu_metric.value, 45.5)
        self.assertEqual(memory_metric.value, 67.8)
        self.assertEqual(disk_metric.value, 23.1)

    def test_collect_event_metric(self):
        """Test de collecte de métrique d'événement."""
        metadata = {'page': 'dashboard', 'action': 'button_click'}

        MetricsCollector.collect_event_metric(
            event_type='button_click',
            user=self.user,
            organization=self.organization,
            metadata=metadata
        )

        # Vérifier que la métrique utilisateur a été créée
        metric = UserMetric.objects.filter(
            user=self.user,
            metric_type='events.button_click'
        ).first()

        self.assertIsNotNone(metric)
        self.assertEqual(metric.value, 1)
        self.assertEqual(metric.context, metadata)

    def test_collect_application_metrics(self):
        """Test de collecte de métriques d'application."""
        project = Project.objects.create(
            name="Test Project",
            organization=self.organization,
            created_by=self.user
        )
        app = GeneratedApp.objects.create(
            name="Test App",
            project=project,
            status="deployed"
        )

        metrics_data = {
            'response.time': {'value': 245, 'unit': 'ms'},
            'requests.count': {'value': 100, 'unit': 'count'}
        }

        MetricsCollector.collect_application_metrics(app, metrics_data)

        # Vérifier que les métriques ont été créées
        response_time = ApplicationMetric.objects.filter(
            app=app,
            metric_type='response.time'
        ).first()
        requests_count = ApplicationMetric.objects.filter(
            app=app,
            metric_type='requests.count'
        ).first()

        self.assertIsNotNone(response_time)
        self.assertIsNotNone(requests_count)

        self.assertEqual(response_time.value, 245)
        self.assertEqual(requests_count.value, 100)

    def test_collect_performance_metrics(self):
        """Test de collecte de métriques de performance."""
        metadata = {'endpoint': '/api/test'}

        MetricsCollector.collect_performance_metrics(
            category='backend',
            name='response_time',
            value=245.5,
            unit='ms',
            metadata=metadata
        )

        # Vérifier que la métrique a été créée
        metric = PerformanceMetric.objects.filter(
            category='backend',
            name='response_time'
        ).first()

        self.assertIsNotNone(metric)
        self.assertEqual(metric.value, 245.5)
        self.assertEqual(metric.metadata, metadata)


class AnalyticsServiceTest(TestCase):
    """Tests pour le service AnalyticsService."""

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

        # Créer des données de test
        self.start_date = timezone.now().date() - timezone.timedelta(days=7)
        self.end_date = timezone.now().date()

        # Créer quelques activités
        for i in range(5):
            UserActivity.objects.create(
                user=self.user,
                organization=self.organization,
                activity_type='user.login',
                created_at=timezone.now() - timezone.timedelta(days=i)
            )

    def test_generate_analytics_report_user_activity(self):
        """Test de génération de rapport avec métriques d'activité utilisateur."""
        report = AnalyticsService.generate_analytics_report(
            organization_id=str(self.organization.id),
            start_date=self.start_date,
            end_date=self.end_date,
            metrics=['user_activity']
        )

        self.assertIn('organization_id', report)
        self.assertIn('period', report)
        self.assertIn('metrics', report)
        self.assertIn('user_activity', report['metrics'])

        user_activity = report['metrics']['user_activity']
        self.assertIn('total', user_activity)
        self.assertIn('unique_users', user_activity)
        self.assertGreater(user_activity['total'], 0)

    def test_generate_analytics_report_system_performance(self):
        """Test de génération de rapport avec métriques système."""
        # Créer des métriques système
        for i in range(3):
            SystemMetric.objects.create(
                metric_type='cpu.usage',
                value=40 + i * 10,
                created_at=timezone.now() - timezone.timedelta(days=i)
            )

        report = AnalyticsService.generate_analytics_report(
            organization_id=str(self.organization.id),
            start_date=self.start_date,
            end_date=self.end_date,
            metrics=['system_performance']
        )

        self.assertIn('system_performance', report['metrics'])
        system_perf = report['metrics']['system_performance']
        self.assertIn('total_measurements', system_perf)
        self.assertIn('by_metric', system_perf)

    def test_generate_performance_report(self):
        """Test de génération de rapport de performance d'application."""
        app = GeneratedApp.objects.create(
            name="Test App",
            project=self.project,
            status="deployed"
        )

        # Créer des métriques d'application
        for i in range(3):
            ApplicationMetric.objects.create(
                app=app,
                metric_type='response.time',
                value=200 + i * 20,
                created_at=timezone.now() - timezone.timedelta(days=i)
            )

        report = AnalyticsService.generate_performance_report(
            app_id=str(app.id),
            start_date=self.start_date,
            end_date=self.end_date,
            metrics=['response_time']
        )

        self.assertIn('app_id', report)
        self.assertIn('performance', report)
        self.assertIn('response_time', report['performance'])

        response_time = report['performance']['response_time']
        self.assertIn('avg', response_time)
        self.assertIn('min', response_time)
        self.assertIn('max', response_time)


class ActivityTrackerTest(TestCase):
    """Tests pour le service ActivityTracker."""

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

    def test_track_user_action(self):
        """Test de tracking d'action utilisateur."""
        metadata = {'extra': 'data'}

        ActivityTracker.track_user_action(
            user=self.user,
            action_type='project.created',
            description='Création de projet',
            metadata=metadata,
            content_object=self.project
        )

        # Vérifier que l'activité a été créée
        activity = UserActivity.objects.filter(
            user=self.user,
            activity_type='project.created'
        ).first()

        self.assertIsNotNone(activity)
        self.assertEqual(activity.description, 'Création de projet')
        self.assertEqual(activity.metadata, metadata)
        self.assertEqual(activity.content_object, self.project)

    def test_track_login(self):
        """Test de tracking de connexion."""
        request = MagicMock()
        request.META = {'REMOTE_ADDR': '127.0.0.1'}

        ActivityTracker.track_login(self.user, request)

        # Vérifier que l'activité de connexion a été créée
        activity = UserActivity.objects.filter(
            user=self.user,
            activity_type='user.login'
        ).first()

        self.assertIsNotNone(activity)
        self.assertEqual(activity.ip_address, '127.0.0.1')

    def test_track_logout(self):
        """Test de tracking de déconnexion."""
        ActivityTracker.track_logout(self.user)

        # Vérifier que l'activité de déconnexion a été créée
        activity = UserActivity.objects.filter(
            user=self.user,
            activity_type='user.logout'
        ).first()

        self.assertIsNotNone(activity)

    def test_track_project_action(self):
        """Test de tracking d'action sur projet."""
        ActivityTracker.track_project_action(
            user=self.user,
            project=self.project,
            action_type='updated'
        )

        # Vérifier que l'activité a été créée avec le bon type
        activity = UserActivity.objects.filter(
            activity_type='project.updated'
        ).first()

        self.assertIsNotNone(activity)
        self.assertEqual(activity.content_object, self.project)

    def test_track_app_action(self):
        """Test de tracking d'action sur application."""
        app = GeneratedApp.objects.create(
            name="Test App",
            project=self.project,
            status="generated"
        )

        ActivityTracker.track_app_action(
            user=self.user,
            app=app,
            action_type='deployed'
        )

        # Vérifier que l'activité a été créée
        activity = UserActivity.objects.filter(
            activity_type='app.deployed'
        ).first()

        self.assertIsNotNone(activity)
        self.assertEqual(activity.content_object, app)
