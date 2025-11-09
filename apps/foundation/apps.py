
from django.apps import AppConfig
from django.db.models.signals import post_migrate
import logging

logger = logging.getLogger(__name__)


class FoundationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.foundation'
    verbose_name = 'Foundation'

    def ready(self):
        try:
            from .signals import user_signals, organization_signals  # noqa
            logger.info("Signaux Foundation chargés avec succès")
        except ImportError as e:
            logger.warning(f"Impossible de charger les signaux Foundation: {e}")

        try:
            from . import tasks  # noqa
            logger.info("Tâches Celery Foundation chargées avec succès")
        except ImportError as e:
            logger.warning(f"Impossible de charger les tâches Celery Foundation: {e}")
            
        try:
            from django.apps import apps
            if apps.is_installed('django.contrib.auth'):
                self._setup_organization_settings()
        except Exception as e:
            logger.warning(f"Erreur lors de la configuration des paramètres d'organisation: {e}")

        # Configurer les permissions personnalisées
        self._setup_permissions();

        # Connecter le signal post_migrate pour les données initiales
        post_migrate.connect(self._create_initial_data, sender=self)

    """def _setup_permissions(self):
        try:
            from .permissions import setup_custom_permissions
            setup_custom_permissions()
            logger.info("Permissions personnalisées configurées")
        except Exception as e:
            logger.warning(f"Erreur lors de la configuration des permissions: {e}")
      """
    def _setup_organization_settings(self):
        from .models import Organization, OrganizationSettings
        
        # Créer des paramètres par défaut pour les organisations existantes qui n'en ont pas
        for org in Organization.objects.all():
            OrganizationSettings.objects.get_or_create(organization=org)
            
        logger.info("Configuration des paramètres d'organisation terminée")

    def _create_initial_data(self, sender, **kwargs):

        if sender.name != self.name:
            return

        try:
            self._create_default_subscription_types()
            self._create_default_notification_preferences()
            logger.info("Données initiales Foundation créées avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la création des données initiales: {e}")

    def _create_default_subscription_types(self):
        try:
            from .models import TypeAbonnement

            # Type d'abonnement gratuit
            free_plan, created = TypeAbonnement.objects.get_or_create(
                nom='Gratuit',
                defaults={
                    'description': 'Plan gratuit avec fonctionnalités de base',
                    'prix_mensuel': 0.00,
                    'prix_annuel': 0.00,
                    'max_users': 1,
                    'max_projects': 3,
                    'max_storage_gb': 1,
                    'is_active': True
                }
            )
            if created:
                logger.info("Plan gratuit créé")

            # Type d'abonnement professionnel
            pro_plan, created = TypeAbonnement.objects.get_or_create(
                nom='Professionnel',
                defaults={
                    'description': 'Plan professionnel avec fonctionnalités avancées',
                    'prix_mensuel': 29.99,
                    'prix_annuel': 299.99,
                    'max_users': 10,
                    'max_projects': 50,
                    'max_storage_gb': 100,
                    'is_active': True
                }
            )
            if created:
                logger.info("Plan professionnel créé")

            enterprise_plan, created = TypeAbonnement.objects.get_or_create(
                nom='Entreprise',
                defaults={
                    'description': 'Plan entreprise avec fonctionnalités complètes',
                    'prix_mensuel': 99.99,
                    'prix_annuel': 999.99,
                    'max_users': -1,  # Illimité
                    'max_projects': -1,  # Illimité
                    'max_storage_gb': 1000,
                    'is_active': True
                }
            )
            if created:
                logger.info("Plan entreprise créé")

        except Exception as e:
            logger.error(f"Erreur lors de la création des types d'abonnement: {e}")

    def _create_default_notification_preferences(self):
        try:
            from django.contrib.auth import get_user_model
            from .models import NotificationPreference

            User = get_user_model()

            # Créer les préférences pour les utilisateurs qui n'en ont pas
            users_without_prefs = User.objects.filter(
                notification_preferences__isnull=True
            )

            for user in users_without_prefs:
                NotificationPreference.objects.get_or_create(
                    user=user,
                    defaults={
                        'email_notifications': True,
                        'push_notifications': True,
                        'sms_notifications': False,
                        'marketing_emails': False,
                        'security_alerts': True,
                        'billing_notifications': True
                    }
                )

            if users_without_prefs.exists():
                logger.info(f"Préférences de notification créées pour {users_without_prefs.count()} utilisateurs")

        except Exception as e:
            logger.error(f"Erreur lors de la création des préférences de notification: {e}")

    @staticmethod
    def get_version():
        return "1.0.0"

    @staticmethod
    def get_features():
        return [
            'user_management',
            'organization_management',
            'subscription_billing',
            'document_verification',
            'activity_logging',
            'notification_system',
            'admin_interface'
        ]

    def __str__(self):
        return f"Foundation App v{self.get_version()}"
