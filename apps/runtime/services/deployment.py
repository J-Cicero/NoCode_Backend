
import os
import logging
import subprocess
import shutil
from pathlib import Path
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

class DeploymentTarget:
    
    def deploy(self, app):
        raise NotImplementedError("Méthode deploy() non implémentée")
    
    def get_status(self, app):
        raise NotImplementedError("Méthode get_status() non implémentée")
    
    def get_logs(self, app, lines=100):
        raise NotImplementedError("Méthode get_logs() non implémentée")


class LocalDeployment(DeploymentTarget):
    """Déploiement local simple (fichiers uniquement, sans Docker)."""
    
    def __init__(self):
        self.deployment_dir = os.path.join(settings.BASE_DIR, 'generated_apps')
    
    def deploy(self, app):
        try:
            app_dir = os.path.join(self.deployment_dir, f"app_{app.project.id}")
            
            os.makedirs(app_dir, exist_ok=True)
            
            self._generate_app_files(app_dir, app)
            
            logger.info(f"Application {app.name} déployée localement dans {app_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du déploiement local: {e}")
            return False
    
    def _generate_app_files(self, app_dir, app):
        os.makedirs(os.path.join(app_dir, 'static'), exist_ok=True)
        os.makedirs(os.path.join(app_dir, 'templates'), exist_ok=True)
        
        requirements = [
            'Django>=4.0',
            'djangorestframework>=3.13',
            'psycopg2-binary>=2.9',
            'gunicorn>=20.1',
        ]
        
        requirements_path = os.path.join(app_dir, 'requirements.txt')
        with open(requirements_path, 'w') as f:
            f.write('\n'.join(requirements))
    
    def get_status(self, app):
        """Récupère le statut de l'application déployée."""
        app_dir = os.path.join(self.deployment_dir, f"app_{app.project.id}")
        return os.path.exists(app_dir)
    
    def get_logs(self, app, lines=100):
        """Récupère les logs de l'application déployée."""
        return ["Logs non disponibles pour le déploiement local sans Docker"]


class DockerDeployment(DeploymentTarget):
    """Déploiement Docker avec conteneurs isolés."""
    
    def __init__(self):
        pass
    
    def deploy(self, app):
        """Déploie l'application dans un conteneur Docker."""
        from .docker_deployment import DockerDeploymentService
        
        try:
            service = DockerDeploymentService(app)
            return service.deploy()
        except Exception as e:
            logger.error(f"Erreur lors du déploiement Docker: {e}")
            return False
    
    def get_status(self, app):
        """Récupère le statut du conteneur Docker."""
        from .docker_deployment import DockerDeploymentService
        
        try:
            service = DockerDeploymentService(app)
            return service.get_status()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_logs(self, app, lines=100):
        """Récupère les logs du conteneur Docker."""
        from .docker_deployment import DockerDeploymentService
        
        try:
            service = DockerDeploymentService(app)
            return service.get_logs(lines=lines)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des logs: {e}")
            return [f"Erreur: {str(e)}"]


class KubernetesDeployment(DeploymentTarget):
    """Déploiement sur Kubernetes (production)."""
    
    def __init__(self, namespace="default"):
        self.namespace = namespace
    
    def deploy(self, app):
        """Déploie l'application sur Kubernetes."""
        # Implémentation Kubernetes à venir
        logger.info(f"Déploiement Kubernetes de {app.name} non implémenté")
        return False
    
    def get_status(self, app):
        """Récupère le statut de l'application sur Kubernetes."""
        return "Non implémenté"
    
    def get_logs(self, app, lines=100):
        """Récupère les logs depuis Kubernetes."""
        return ["Logs Kubernetes non disponibles"]


class DeploymentManager:
    """Gestionnaire principal des déploiements.

    API unique utilisée par:
    - GeneratedApp.deploy()
    - runtime.views (status/logs)
    - runtime.tasks (deploy_app_task)
    """

    def __init__(self, app=None, deployment_strategy: DeploymentTarget | None = None):
        self.app = app
        self.targets = {
            'local': LocalDeployment(),
            'docker': DockerDeployment(),
            'staging': DockerDeployment(),
            'production': KubernetesDeployment(),
            'kubernetes': KubernetesDeployment(),
        }
        self.deployment_strategy = deployment_strategy

    def _resolve_target(self, app, target: str | None = None) -> DeploymentTarget:
        if self.deployment_strategy is not None:
            return self.deployment_strategy

        target_key = target or getattr(app, 'deployment_target', None) or 'local'
        if target_key not in self.targets:
            raise ValueError(f"Cible de déploiement non supportée: {target_key}")
        return self.targets[target_key]

    def deploy(self, app=None, target: str | None = None):
        app = app or self.app
        if app is None:
            raise ValueError('Missing app for deployment')
        strategy = self._resolve_target(app, target)
        return strategy.deploy(app)

    def get_status(self, app=None, target: str | None = None):
        app = app or self.app
        if app is None:
            raise ValueError('Missing app for status')
        strategy = self._resolve_target(app, target)
        return strategy.get_status(app)

    def get_logs(self, app=None, lines: int = 100, target: str | None = None):
        app = app or self.app
        if app is None:
            raise ValueError('Missing app for logs')
        strategy = self._resolve_target(app, target)
        return strategy.get_logs(app, lines=lines)

    def get_deployment_target(self, target):
        return self.targets.get(target)
