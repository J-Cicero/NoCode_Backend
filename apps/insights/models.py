
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from .base import BaseModel

class UserActivity(BaseModel):

    ACTIVITY_TYPES = [
        # Actions utilisateur
        ('user.login', 'Connexion utilisateur'),
        ('user.logout', 'Déconnexion utilisateur'),
        ('user.register', 'Inscription utilisateur'),
        ('user.profile_update', 'Mise à jour profil'),

        # Actions projet
        ('project.created', 'Création de projet'),
        ('project.updated', 'Modification de projet'),
        ('project.deleted', 'Suppression de projet'),
        ('project.shared', 'Partage de projet'),

        # Actions application
        ('app.created', 'Création d\'application'),
        ('app.updated', 'Modification d\'application'),
        ('app.deployed', 'Déploiement d\'application'),
        ('app.deleted', 'Suppression d\'application'),

        # Actions workflow
        ('workflow.created', 'Création de workflow'),
        ('workflow.executed', 'Exécution de workflow'),
        ('workflow.failed', 'Échec de workflow'),

        # Actions intégration
        ('integration.created', 'Création d\'intégration'),
        ('integration.updated', 'Modification d\'intégration'),
        ('integration.failed', 'Échec d\'intégration'),

        # Actions sécurité
        ('security.permission_changed', 'Changement de permissions'),
        ('security.password_changed', 'Changement de mot de passe'),
        ('security.2fa_enabled', '2FA activée'),
        ('security.2fa_disabled', '2FA désactivée'),

        # Actions système
        ('system.backup', 'Sauvegarde système'),
        ('system.maintenance', 'Maintenance système'),
        ('system.error', 'Erreur système'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities',
        verbose_name="Utilisateur"
    )

    organization = models.ForeignKey(
        'foundation.Organization',
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name="Organisation"
    )

    activity_type = models.CharField(
        max_length=50,
        choices=ACTIVITY_TYPES,
        verbose_name="Type d'activité"
    )

    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées"
    )

    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Type de contenu"
    )

    object_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name="ID de l'objet"
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Adresse IP"
    )

    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent"
    )

    session_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="ID de session"
    )

    class Meta:
        verbose_name = "Activité utilisateur"
        verbose_name_plural = "Activités utilisateur"
        db_table = 'insights_user_activity'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['organization', 'created_at']),
            models.Index(fields=['activity_type', 'created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.user} - {self.activity_type} - {self.created_at}"

    @property
    def content_object(self):
        """Retourne l'objet générique associé."""
        if self.content_type and self.object_id:
            try:
                return self.content_type.get_object_for_this_type(id=self.object_id)
            except:
                return None
        return None


class SystemMetric(BaseModel):

    METRIC_TYPES = [
        ('cpu.usage', 'Utilisation CPU (%)'),
        ('memory.usage', 'Utilisation mémoire (%)'),
        ('disk.usage', 'Utilisation disque (%)'),
        ('network.in', 'Trafic réseau entrant (bytes/s)'),
        ('network.out', 'Trafic réseau sortant (bytes/s)'),
        ('requests.count', 'Nombre de requêtes'),
        ('requests.latency', 'Latence des requêtes (ms)'),
        ('errors.count', 'Nombre d\'erreurs'),
        ('active.users', 'Utilisateurs actifs'),
        ('database.connections', 'Connexions base de données'),
        ('cache.hit_rate', 'Taux de succès cache (%)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    metric_type = models.CharField(
        max_length=50,
        choices=METRIC_TYPES,
        verbose_name="Type de métrique"
    )

    # Valeur de la métrique
    value = models.FloatField(
        verbose_name="Valeur"
    )

    unit = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Unité"
    )

    tags = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Étiquettes"
    )

    hostname = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Nom d'hôte"
    )

    service = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Service"
    )

    class Meta:
        verbose_name = "Métrique système"
        verbose_name_plural = "Métriques système"
        db_table = 'insights_system_metric'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['metric_type', 'created_at']),
            models.Index(fields=['hostname', 'service']),
        ]


class ApplicationMetric(BaseModel):

    METRIC_TYPES = [
        ('response.time', 'Temps de réponse (ms)'),
        ('requests.count', 'Nombre de requêtes'),
        ('errors.count', 'Nombre d\'erreurs'),
        ('uptime', 'Disponibilité (%)'),
        ('cpu.usage', 'Utilisation CPU (%)'),
        ('memory.usage', 'Utilisation mémoire (%)'),
        ('users.active', 'Utilisateurs actifs'),
        ('api.calls', 'Appels API'),
        ('database.queries', 'Requêtes base de données'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    app = models.ForeignKey(
        'runtime.GeneratedApp',
        on_delete=models.CASCADE,
        related_name='metrics',
        verbose_name="Application"
    )

    metric_type = models.CharField(
        max_length=50,
        choices=METRIC_TYPES,
        verbose_name="Type de métrique"
    )

    value = models.FloatField(
        verbose_name="Valeur"
    )

    unit = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Unité"
    )

    environment = models.CharField(
        max_length=50,
        default='production',
        verbose_name="Environnement"
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées"
    )

    class Meta:
        verbose_name = "Métrique d'application"
        verbose_name_plural = "Métriques d'application"
        db_table = 'insights_application_metric'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['app', 'created_at']),
            models.Index(fields=['metric_type', 'created_at']),
            models.Index(fields=['environment', 'created_at']),
        ]


class UserMetric(BaseModel):
    METRIC_TYPES = [
        ('session.duration', 'Durée de session (minutes)'),
        ('pages.visited', 'Pages visitées'),
        ('actions.performed', 'Actions effectuées'),
        ('projects.created', 'Projets créés'),
        ('apps.deployed', 'Applications déployées'),
        ('time.spent', 'Temps passé (heures)'),
        ('features.used', 'Fonctionnalités utilisées'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='metrics',
        verbose_name="Utilisateur"
    )

    organization = models.ForeignKey(
        'foundation.Organization',
        on_delete=models.CASCADE,
        related_name='user_metrics',
        verbose_name="Organisation"
    )

    metric_type = models.CharField(
        max_length=50,
        choices=METRIC_TYPES,
        verbose_name="Type de métrique"
    )

    value = models.FloatField(
        verbose_name="Valeur"
    )

    date = models.DateField(
        default=timezone.now,
        verbose_name="Date"
    )

    context = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Contexte"
    )

    class Meta:
        verbose_name = "Métrique utilisateur"
        verbose_name_plural = "Métriques utilisateur"
        db_table = 'insights_user_metric'
        ordering = ['-date', '-created_at']
        unique_together = ('user', 'metric_type', 'date')
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['organization', 'date']),
            models.Index(fields=['metric_type', 'date']),
        ]


class PerformanceMetric(BaseModel):
    
    METRIC_CATEGORIES = [
        ('frontend', 'Interface utilisateur'),
        ('backend', 'Serveur backend'),
        ('database', 'Base de données'),
        ('external', 'Services externes'),
        ('network', 'Réseau'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    category = models.CharField(
        max_length=20,
        choices=METRIC_CATEGORIES,
        verbose_name="Catégorie"
    )

    name = models.CharField(
        max_length=100,
        verbose_name="Nom de la métrique"
    )

    value = models.FloatField(
        verbose_name="Valeur"
    )

    unit = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Unité"
    )

    timestamp = models.DateTimeField(
        default=timezone.now,
        verbose_name="Horodatage"
    )

    organization = models.ForeignKey(
        'foundation.Organization',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='performance_metrics',
        verbose_name="Organisation"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='performance_metrics',
        verbose_name="Utilisateur"
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées"
    )

    class Meta:
        verbose_name = "Métrique de performance"
        verbose_name_plural = "Métriques de performance"
        db_table = 'insights_performance_metric'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['category', 'timestamp']),
            models.Index(fields=['name', 'timestamp']),
            models.Index(fields=['organization', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]
