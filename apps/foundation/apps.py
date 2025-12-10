
from django.apps import AppConfig
from django.db.models.signals import post_migrate
import logging

logger = logging.getLogger(__name__)


class FoundationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.foundation'
    verbose_name = 'Foundation'

    def ready(self):
        """Initialisation du module Foundation."""
        try:
            # from . import signals  # noqa
            logger.info("Signaux Foundation désactivés temporairement")
        except ImportError as e:
            logger.warning(f"Impossible de charger les signaux: {e}")
            
        # Enregistrer le signal post_migrate pour créer les données initiales
        # post_migrate.connect(self._create_initial_data, sender=self)  # Temporairement désactivé

    
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
        """Crée les types d'abonnement par défaut."""
        try:
            from .models import TypeAbonnement

            # Plan FREE
            free_plan, created = TypeAbonnement.objects.get_or_create(
                nom='FREE',
                categorie_utilisateur='CLIENT',
                defaults={
                    'description': 'Plan gratuit avec fonctionnalités de base',
                    'tarif': 0.00,
                    'is_active': True
                }
            )
            if created:
                logger.info("Plan FREE créé")

            # Plan MENSUEL
            monthly_plan, created = TypeAbonnement.objects.get_or_create(
                nom='MENSUEL',
                categorie_utilisateur='CLIENT', 
                defaults={
                    'description': 'Plan mensuel',
                    'tarif': 29.99,
                    'is_active': True
                }
            )
            if created:
                logger.info("Plan MENSUEL créé")

            # Plan ANNUEL pour organisations
            yearly_plan, created = TypeAbonnement.objects.get_or_create(
                nom='ANNUEL',
                categorie_utilisateur='ORGANIZATION',
                defaults={
                    'description': 'Plan annuel pour organisations',
                    'tarif': 299.99,
                    'is_active': True
                }
            )
            if created:
                logger.info("Plan ANNUEL créé")

        except Exception as e:
            logger.error(f"Erreur lors de la création des types d'abonnement: {e}")

    def _create_default_notification_preferences(self):
        """Crée les préférences de notification par défaut."""
        # Pour l'instant, on ne fait rien - à implémenter plus tard
        
