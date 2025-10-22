"""
Modèles pour le module Runtime.
Gère les applications générées, leurs déploiements et leur configuration.
"""
from django.db import models
from django.utils import timezone
from django.conf import settings
from apps.studio.models import Project
import uuid
import logging

logger = logging.getLogger(__name__)


class GeneratedApp(models.Model):
    """
    Représente une application générée à partir d'un projet Studio.
    """
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('generated', 'Générée'),
        ('deployed', 'Déployée'),
        ('error', 'Erreur'),
        ('archived', 'Archivée'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name='generated_app',
        verbose_name='Projet associé'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Statut'
    )
    version = models.CharField(max_length=50, default='1.0.0', verbose_name='Version')
    api_base_url = models.URLField(blank=True, verbose_name='URL de base de l\'API')
    admin_url = models.URLField(blank=True, verbose_name='URL d\'administration')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Mis à jour le')
    last_deployed_at = models.DateTimeField(null=True, blank=True, verbose_name='Dernier déploiement')
    
    # Configuration du déploiement
    deployment_target = models.CharField(
        max_length=100,
        default='local',
        choices=[
            ('local', 'Local'),
            ('staging', 'Environnement de test'),
            ('production', 'Production')
        ],
        verbose_name='Environnement de déploiement'
    )
    
    # Métadonnées techniques
    config = models.JSONField(default=dict, verbose_name='Configuration technique')
    
    class Meta:
        verbose_name = 'Application générée'
        verbose_name_plural = 'Applications générées'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.project.name} ({self.get_status_display()}) v{self.version}"
    
    def generate_code(self):
        """Génère le code source de l'application."""
        from .services.code_generator import AppGenerator
        try:
            generator = AppGenerator(self.project)
            generator.generate()
            self.status = 'generated'
            self.save()
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la génération de l'application {self.id}: {str(e)}")
            self.status = 'error'
            self.save()
            return False
    
    def deploy(self):
        """Déploie l'application sur l'environnement cible."""
        from .services.deployment import DeploymentManager
        try:
            if self.status != 'generated':
                if not self.generate_code():
                    return False
            
            manager = DeploymentManager(self)
            success = manager.deploy()
            
            if success:
                self.status = 'deployed'
                self.last_deployed_at = timezone.now()
                self.save()
            else:
                self.status = 'error'
                self.save()
                
            return success
            
        except Exception as e:
            logger.error(f"Erreur lors du déploiement de l'application {self.id}: {str(e)}")
            self.status = 'error'
            self.save()
            return False


class DeploymentLog(models.Model):
    """
    Journal des déploiements pour le suivi des mises à jour.
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échec'),
        ('rolled_back', 'Annulé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    app = models.ForeignKey(
        GeneratedApp,
        on_delete=models.CASCADE,
        related_name='deployment_logs',
        verbose_name='Application'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Statut'
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Début')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Fin')
    log_output = models.TextField(blank=True, verbose_name='Sortie du journal')
    error_message = models.TextField(blank=True, verbose_name='Message d\'erreur')
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Effectué par'
    )
    
    class Meta:
        verbose_name = 'Journal de déploiement'
        verbose_name_plural = 'Journaux de déploiement'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Déploiement de {self.app} - {self.get_status_display()} à {self.started_at}"
    
    def mark_completed(self, success=True, log_output='', error_message=''):
        """Marque le déploiement comme terminé."""
        self.status = 'completed' if success else 'failed'
        self.completed_at = timezone.now()
        self.log_output = log_output
        self.error_message = error_message
        self.save()
        
        # Mise à jour du statut de l'application
        if success:
            self.app.status = 'deployed'
            self.app.last_deployed_at = self.completed_at
        else:
            self.app.status = 'error'
        self.app.save()
        
        return self
