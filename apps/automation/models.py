"""
Modèles pour le module Automation
"""
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.foundation.models import User, Organization
from apps.studio.models import Project
import uuid


class Workflow(models.Model):
    """
    Définit un workflow automatisé avec des étapes et des conditions.
    """
    STATUS_CHOICES = [
        ('DRAFT', 'Brouillon'),
        ('ACTIVE', 'Actif'),
        ('PAUSED', 'En pause'),
        ('ARCHIVED', 'Archivé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name='Nom du workflow')
    description = models.TextField(blank=True, verbose_name='Description')
    
    # Propriétaire
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='workflows',
        verbose_name='Organisation'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='workflows_created',
        verbose_name='Créé par'
    )
    
    # Projet Studio lié (optionnel)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='workflows',
        verbose_name='Projet'
    )
    
    # Configuration
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        verbose_name='Statut'
    )
    
    # Métadonnées
    config = models.JSONField(
        default=dict,
        verbose_name='Configuration',
        help_text='Configuration générale du workflow'
    )
    variables = models.JSONField(
        default=dict,
        verbose_name='Variables',
        help_text='Variables globales du workflow'
    )
    
    # Statistiques
    execution_count = models.IntegerField(default=0, verbose_name='Nombre d\'exécutions')
    success_count = models.IntegerField(default=0, verbose_name='Exécutions réussies')
    failure_count = models.IntegerField(default=0, verbose_name='Exécutions échouées')
    last_executed_at = models.DateTimeField(null=True, blank=True, verbose_name='Dernière exécution')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Modifié le')
    
    class Meta:
        verbose_name = 'Workflow'
        verbose_name_plural = 'Workflows'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['project']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    @property
    def success_rate(self):
        """Calcule le taux de succès des exécutions."""
        if self.execution_count == 0:
            return 0
        return (self.success_count / self.execution_count) * 100
    
    @property
    def is_active(self):
        """Vérifie si le workflow est actif."""
        return self.status == 'ACTIVE'
    
    def increment_execution_stats(self, success: bool):
        """Incrémente les statistiques d'exécution."""
        self.execution_count += 1
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        self.last_executed_at = timezone.now()
        self.save(update_fields=['execution_count', 'success_count', 'failure_count', 'last_executed_at'])


class WorkflowStep(models.Model):
    """
    Représente une étape dans un workflow.
    """
    ACTION_TYPES = [
        ('validate_data', 'Validation de données'),
        ('database_save', 'Sauvegarde en base'),
        ('database_query', 'Requête base de données'),
        ('integration_call', 'Appel d\'intégration'),
        ('send_email', 'Envoi d\'email'),
        ('send_webhook', 'Envoi de webhook'),
        ('transform_data', 'Transformation de données'),
        ('conditional', 'Condition'),
        ('loop', 'Boucle'),
        ('wait', 'Attente'),
        ('custom_code', 'Code personnalisé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='steps',
        verbose_name='Workflow'
    )
    
    # Identification de l'étape
    name = models.CharField(max_length=255, verbose_name='Nom de l\'étape')
    step_id = models.CharField(
        max_length=100,
        verbose_name='Identifiant unique',
        help_text='Identifiant unique pour référencer l\'étape'
    )
    
    # Type et action
    action_type = models.CharField(
        max_length=50,
        choices=ACTION_TYPES,
        verbose_name='Type d\'action'
    )
    
    # Configuration
    params = models.JSONField(
        default=dict,
        verbose_name='Paramètres',
        help_text='Paramètres de l\'action'
    )
    
    # Intégration liée (si applicable)
    integration = models.ForeignKey(
        'Integration',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workflow_steps',
        verbose_name='Intégration'
    )
    
    # Ordre d'exécution
    order = models.IntegerField(default=0, verbose_name='Ordre')
    
    # Conditions d'exécution
    condition = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Condition',
        help_text='Condition pour exécuter cette étape'
    )
    
    # Gestion d'erreurs
    on_error = models.CharField(
        max_length=20,
        choices=[
            ('stop', 'Arrêter le workflow'),
            ('continue', 'Continuer'),
            ('retry', 'Réessayer'),
            ('goto', 'Aller à une étape'),
        ],
        default='stop',
        verbose_name='En cas d\'erreur'
    )
    retry_count = models.IntegerField(default=3, verbose_name='Nombre de tentatives')
    retry_delay = models.IntegerField(
        default=60,
        verbose_name='Délai entre tentatives (secondes)'
    )
    
    # Métadonnées
    metadata = models.JSONField(default=dict, blank=True, verbose_name='Métadonnées')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Modifié le')
    
    class Meta:
        verbose_name = 'Étape de Workflow'
        verbose_name_plural = 'Étapes de Workflow'
        ordering = ['workflow', 'order']
        unique_together = [['workflow', 'step_id']]
        indexes = [
            models.Index(fields=['workflow', 'order']),
        ]
    
    def __str__(self):
        return f"{self.workflow.name} - {self.name}"


class Trigger(models.Model):
    """
    Définit un déclencheur pour un workflow.
    """
    TRIGGER_TYPES = [
        ('manual', 'Manuel'),
        ('event', 'Événement système'),
        ('webhook', 'Webhook'),
        ('schedule', 'Planification (cron)'),
        ('form_submit', 'Soumission de formulaire'),
        ('data_change', 'Modification de données'),
        ('api_call', 'Appel API'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='triggers',
        verbose_name='Workflow'
    )
    
    # Type de déclencheur
    trigger_type = models.CharField(
        max_length=50,
        choices=TRIGGER_TYPES,
        verbose_name='Type de déclencheur'
    )
    
    # Configuration
    config = models.JSONField(
        default=dict,
        verbose_name='Configuration',
        help_text='Configuration spécifique au type de déclencheur'
    )
    
    # Pour les webhooks
    webhook_url = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='URL du webhook',
        help_text='URL générée automatiquement pour recevoir les webhooks'
    )
    webhook_secret = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Secret du webhook'
    )
    
    # Pour les planifications
    cron_expression = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Expression cron',
        help_text='Expression cron pour la planification (ex: 0 9 * * *)'
    )
    
    # Pour les événements
    event_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Type d\'événement',
        help_text='Type d\'événement à écouter (ex: project.created)'
    )
    
    # État
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    
    # Métadonnées
    metadata = models.JSONField(default=dict, blank=True, verbose_name='Métadonnées')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Modifié le')
    
    class Meta:
        verbose_name = 'Déclencheur'
        verbose_name_plural = 'Déclencheurs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow', 'trigger_type']),
            models.Index(fields=['event_type']),
        ]
    
    def __str__(self):
        return f"{self.workflow.name} - {self.get_trigger_type_display()}"


class Integration(models.Model):
    """
    Définit une intégration avec un service externe.
    """
    INTEGRATION_TYPES = [
        ('email', 'Email (SMTP/SendGrid)'),
        ('stripe', 'Stripe'),
        ('webhook', 'Webhook HTTP'),
        ('database', 'Base de données'),
        ('storage', 'Stockage (S3, etc.)'),
        ('notification', 'Notifications (SMS, Push)'),
        ('api', 'API REST personnalisée'),
        ('slack', 'Slack'),
        ('zapier', 'Zapier'),
        ('custom', 'Personnalisée'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Erreur'),
        ('testing', 'En test'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name='Nom de l\'intégration')
    integration_type = models.CharField(
        max_length=50,
        choices=INTEGRATION_TYPES,
        verbose_name='Type d\'intégration'
    )
    
    # Propriétaire
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='integrations',
        verbose_name='Organisation'
    )
    
    # Configuration
    config = models.JSONField(
        default=dict,
        verbose_name='Configuration',
        help_text='Configuration générale de l\'intégration'
    )
    
    # État
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='inactive',
        verbose_name='Statut'
    )
    
    # Statistiques
    total_calls = models.IntegerField(default=0, verbose_name='Appels totaux')
    successful_calls = models.IntegerField(default=0, verbose_name='Appels réussis')
    failed_calls = models.IntegerField(default=0, verbose_name='Appels échoués')
    last_used_at = models.DateTimeField(null=True, blank=True, verbose_name='Dernière utilisation')
    
    # Rate limiting
    rate_limit = models.IntegerField(
        default=100,
        verbose_name='Limite de requêtes',
        help_text='Nombre maximum de requêtes par heure'
    )
    
    # Métadonnées
    metadata = models.JSONField(default=dict, blank=True, verbose_name='Métadonnées')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Modifié le')
    
    class Meta:
        verbose_name = 'Intégration'
        verbose_name_plural = 'Intégrations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['integration_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_integration_type_display()})"
    
    @property
    def success_rate(self):
        """Calcule le taux de succès des appels."""
        if self.total_calls == 0:
            return 0
        return (self.successful_calls / self.total_calls) * 100
    
    def increment_call_stats(self, success: bool):
        """Incrémente les statistiques d'appels."""
        self.total_calls += 1
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=['total_calls', 'successful_calls', 'failed_calls', 'last_used_at'])


class IntegrationCredential(models.Model):
    """
    Stocke les credentials de manière sécurisée pour les intégrations.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    integration = models.ForeignKey(
        Integration,
        on_delete=models.CASCADE,
        related_name='credentials',
        verbose_name='Intégration'
    )
    
    # Credentials encryptés
    credential_type = models.CharField(
        max_length=50,
        verbose_name='Type de credential',
        help_text='api_key, oauth_token, username_password, etc.'
    )
    encrypted_data = models.BinaryField(verbose_name='Données encryptées')
    
    # Métadonnées
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Expire le',
        help_text='Pour les tokens avec expiration'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Modifié le')
    
    class Meta:
        verbose_name = 'Credential d\'intégration'
        verbose_name_plural = 'Credentials d\'intégration'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.integration.name} - {self.credential_type}"
    
    @property
    def is_expired(self):
        """Vérifie si le credential a expiré."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class WorkflowExecution(models.Model):
    """
    Enregistre l'exécution d'un workflow.
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('running', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
        ('cancelled', 'Annulé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='executions',
        verbose_name='Workflow'
    )
    
    # Déclencheur
    trigger = models.ForeignKey(
        Trigger,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='executions',
        verbose_name='Déclencheur'
    )
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workflow_executions',
        verbose_name='Déclenché par'
    )
    
    # État
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Statut'
    )
    
    # Données d'entrée et de sortie
    input_data = models.JSONField(
        default=dict,
        verbose_name='Données d\'entrée',
        help_text='Données fournies au démarrage du workflow'
    )
    output_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Données de sortie',
        help_text='Résultat de l\'exécution'
    )
    
    # Context d'exécution
    context = models.JSONField(
        default=dict,
        verbose_name='Contexte',
        help_text='Variables et état durant l\'exécution'
    )
    
    # Erreurs
    error_message = models.TextField(blank=True, verbose_name='Message d\'erreur')
    error_details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Détails de l\'erreur'
    )
    
    # Progression
    current_step_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Étape actuelle'
    )
    completed_steps = models.JSONField(
        default=list,
        verbose_name='Étapes complétées'
    )
    
    # Durée
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='Démarré le')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Terminé le')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Modifié le')
    
    class Meta:
        verbose_name = 'Exécution de Workflow'
        verbose_name_plural = 'Exécutions de Workflow'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.workflow.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def duration(self):
        """Calcule la durée d'exécution."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_running(self):
        """Vérifie si l'exécution est en cours."""
        return self.status in ['pending', 'running']
    
    def mark_as_started(self):
        """Marque l'exécution comme démarrée."""
        self.status = 'running'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def mark_as_completed(self, output_data=None):
        """Marque l'exécution comme terminée."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if output_data:
            self.output_data = output_data
        self.save(update_fields=['status', 'completed_at', 'output_data'])
    
    def mark_as_failed(self, error_message, error_details=None):
        """Marque l'exécution comme échouée."""
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.error_message = error_message
        if error_details:
            self.error_details = error_details
        self.save(update_fields=['status', 'completed_at', 'error_message', 'error_details'])


class WorkflowExecutionLog(models.Model):
    """
    Logs détaillés de l'exécution d'un workflow.
    """
    LOG_LEVELS = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution = models.ForeignKey(
        WorkflowExecution,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name='Exécution'
    )
    
    # Étape concernée
    step = models.ForeignKey(
        WorkflowStep,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='execution_logs',
        verbose_name='Étape'
    )
    step_id = models.CharField(max_length=100, blank=True, verbose_name='ID de l\'étape')
    
    # Log
    level = models.CharField(
        max_length=20,
        choices=LOG_LEVELS,
        default='INFO',
        verbose_name='Niveau'
    )
    message = models.TextField(verbose_name='Message')
    details = models.JSONField(default=dict, blank=True, verbose_name='Détails')
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    
    class Meta:
        verbose_name = 'Log d\'exécution'
        verbose_name_plural = 'Logs d\'exécution'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['execution', 'created_at']),
            models.Index(fields=['level']),
        ]
    
    def __str__(self):
        return f"{self.execution.id} - {self.level}: {self.message[:50]}"


class ActionTemplate(models.Model):
    """
    Templates d'actions réutilisables.
    """
    CATEGORY_CHOICES = [
        ('data', 'Données'),
        ('communication', 'Communication'),
        ('integration', 'Intégration'),
        ('logic', 'Logique'),
        ('utility', 'Utilitaire'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name='Nom du template')
    description = models.TextField(verbose_name='Description')
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        verbose_name='Catégorie'
    )
    
    # Configuration du template
    action_type = models.CharField(max_length=50, verbose_name='Type d\'action')
    default_params = models.JSONField(
        default=dict,
        verbose_name='Paramètres par défaut'
    )
    
    # Validation
    param_schema = models.JSONField(
        default=dict,
        verbose_name='Schéma de validation',
        help_text='JSON Schema pour valider les paramètres'
    )
    
    # Visibilité
    is_public = models.BooleanField(default=False, verbose_name='Public')
    is_system = models.BooleanField(default=False, verbose_name='Template système')
    
    # Propriétaire (null si template système)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='action_templates',
        verbose_name='Organisation'
    )
    
    # Métadonnées
    icon = models.CharField(max_length=50, blank=True, verbose_name='Icône')
    tags = models.JSONField(default=list, blank=True, verbose_name='Tags')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Modifié le')
    
    class Meta:
        verbose_name = 'Template d\'action'
        verbose_name_plural = 'Templates d\'actions'
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category', 'is_public']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
