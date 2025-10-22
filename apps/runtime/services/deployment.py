"""
Gestion du déploiement des applications générées.

Ce module gère le déploiement des applications sur différents environnements
(local, staging, production) en utilisant différentes stratégies (Docker, Kubernetes, etc.).
"""
import os
import logging
import subprocess
import shutil
import docker
from pathlib import Path
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

class DeploymentTarget:
    """Interface pour les cibles de déploiement."""
    
    def deploy(self, app):
        """Déploie l'application sur la cible."""
        raise NotImplementedError("Méthode deploy() non implémentée")
    
    def get_status(self, app):
        """Récupère le statut de l'application déployée."""
        raise NotImplementedError("Méthode get_status() non implémentée")
    
    def get_logs(self, app, lines=100):
        """Récupère les logs de l'application déployée."""
        raise NotImplementedError("Méthode get_logs() non implémentée")


class LocalDeployment(DeploymentTarget):
    """Déploiement local avec Docker."""
    
    def __init__(self):
        self.client = docker.from_env()
        self.network_name = "no_code_network"
        self._ensure_network()
    
    def _ensure_network(self):
        """S'assure que le réseau Docker existe."""
        try:
            self.client.networks.get(self.network_name)
        except docker.errors.NotFound:
            logger.info(f"Création du réseau Docker: {self.network_name}")
            self.client.networks.create(self.network_name, driver="bridge")
    
    def deploy(self, app):
        """Déploie l'application localement avec Docker."""
        try:
            app_dir = os.path.join(settings.BASE_DIR, 'generated_apps', f"app_{app.project.id}")
            
            # Création du Dockerfile s'il n'existe pas
            self._create_dockerfile(app_dir, app)
            
            # Création du docker-compose.yml
            self._create_docker_compose(app_dir, app)
            
            # Construction de l'image Docker
            self._build_docker_image(app_dir, app)
            
            # Démarrage des conteneurs
            self._start_containers(app_dir)
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du déploiement local: {str(e)}")
            return False
    
    def _create_dockerfile(self, app_dir, app):
        """Crée le Dockerfile pour l'application."""
        dockerfile_path = os.path.join(app_dir, 'Dockerfile')
        
        if not os.path.exists(dockerfile_path):
            context = {
                'app_name': f"app_{app.project.id}",
                'python_version': '3.9',
                'requirements': [
                    'Django>=4.0',
                    'djangorestframework>=3.13',
                    'psycopg2-binary>=2.9',
                    'gunicorn>=20.1',
                ]
            }
            
            dockerfile_content = """# Dockerfile pour l'application générée
FROM python:{{ python_version }}-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code de l'application
COPY . .

# Commande par défaut
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "{{ app_name }}.wsgi:application"]
"""
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)
            
            # Création du fichier requirements.txt
            with open(os.path.join(app_dir, 'requirements.txt'), 'w') as f:
                for req in context['requirements']:
                    f.write(f"{req}\n")
    
    def _create_docker_compose(self, app_dir, app):
        """Crée le fichier docker-compose.yml pour l'application."""
        compose_path = os.path.join(app_dir, 'docker-compose.yml')
        
        context = {
            'app_name': f"app_{app.project.id}",
            'db_name': f"db_{app.project.id}",
            'db_user': 'postgres',
            'db_password': 'postgres',
            'db_port': 5432,
            'app_port': 8000,
            'network_name': self.network_name,
        }
        
        compose_content = """version: '3.8'

services:
  db:
    image: postgres:13
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_DB={{ db_name }}
      - POSTGRES_USER={{ db_user }}
      - POSTGRES_PASSWORD={{ db_password }}
    networks:
      - {{ network_name }}

  web:
    build: .
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn --bind 0.0.0.0:8000 --workers 3 {{ app_name }}.wsgi:application"
    volumes:
      - .:/app
    ports:
      - "{{ app_port }}:8000"
    depends_on:
      - db
    environment:
      - DATABASE_URL=postgresql://{{ db_user }}:{{ db_password }}@db:5432/{{ db_name }}
      - DEBUG=0
      - SECRET_KEY=your-secret-key-here
    networks:
      - {{ network_name }}

networks:
  {{ network_name }}:
    external: true

volumes:
  postgres_data:
"""
        
        with open(compose_path, 'w') as f:
            f.write(compose_content)
    
    def _build_docker_image(self, app_dir, app):
        """Construit l'image Docker de l'application."""
        try:
            subprocess.run(
                ['docker-compose', 'build'],
                cwd=app_dir,
                check=True,
                capture_output=True
            )
            logger.info(f"Image Docker construite pour l'application {app.project.name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur lors de la construction de l'image Docker: {e.stderr.decode()}")
            return False
    
    def _start_containers(self, app_dir):
        """Démarre les conteneurs Docker de l'application."""
        try:
            subprocess.run(
                ['docker-compose', 'up', '-d'],
                cwd=app_dir,
                check=True,
                capture_output=True
            )
            logger.info("Conteneurs Docker démarrés avec succès")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur lors du démarrage des conteneurs: {e.stderr.decode()}")
            return False
    
    def get_status(self, app):
        """Récupère le statut des conteneurs de l'application."""
        try:
            result = subprocess.run(
                ['docker-compose', 'ps'],
                cwd=os.path.join(settings.BASE_DIR, 'generated_apps', f"app_{app.project.id}"),
                capture_output=True,
                text=True
            )
            return result.stdout
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut: {str(e)}")
            return f"Erreur: {str(e)}"
    
    def get_logs(self, app, lines=100):
        """Récupère les logs des conteneurs de l'application."""
        try:
            result = subprocess.run(
                ['docker-compose', 'logs', '--tail', str(lines)],
                cwd=os.path.join(settings.BASE_DIR, 'generated_apps', f"app_{app.project.id}"),
                capture_output=True,
                text=True
            )
            return result.stdout or result.stderr
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des logs: {str(e)}")
            return f"Erreur: {str(e)}"


class KubernetesDeployment(DeploymentTarget):
    """Déploiement sur un cluster Kubernetes."""
    
    def __init__(self, kube_config=None):
        self.kube_config = kube_config or os.path.expanduser('~/.kube/config')
        self.namespace = 'no-code-apps'
    
    def deploy(self, app):
        """Déploie l'application sur Kubernetes."""
        try:
            # Implémentation du déploiement Kubernetes
            # (à compléter selon votre configuration Kubernetes)
            logger.info(f"Déploiement de l'application {app.project.name} sur Kubernetes")
            return True
        except Exception as e:
            logger.error(f"Erreur lors du déploiement Kubernetes: {str(e)}")
            return False
    
    def get_status(self, app):
        """Récupère le statut du déploiement Kubernetes."""
        try:
            # Implémentation de la récupération du statut
            return "Statut Kubernetes non implémenté"
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut: {str(e)}")
            return f"Erreur: {str(e)}"
    
    def get_logs(self, app, lines=100):
        """Récupère les logs du déploiement Kubernetes."""
        try:
            # Implémentation de la récupération des logs
            return "Logs Kubernetes non implémentés"
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des logs: {str(e)}")
            return f"Erreur: {str(e)}"


class DeploymentManager:
    """Gestionnaire de déploiement pour les applications générées."""
    
    def __init__(self, app):
        self.app = app
        self.target = self._get_deployment_target()
    
    def _get_deployment_target(self):
        """Retourne la cible de déploiement appropriée."""
        if self.app.deployment_target == 'local':
            return LocalDeployment()
        elif self.app.deployment_target == 'kubernetes':
            return KubernetesDeployment()
        else:
            raise ValueError(f"Cible de déploiement non supportée: {self.app.deployment_target}")
    
    def deploy(self):
        """Déploie l'application sur la cible de déploiement."""
        logger.info(f"Démarrage du déploiement de l'application {self.app.project.name}")
        
        try:
            success = self.target.deploy(self.app)
            if success:
                logger.info(f"Application {self.app.project.name} déployée avec succès")
            else:
                logger.error(f"Échec du déploiement de l'application {self.app.project.name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Erreur lors du déploiement: {str(e)}", exc_info=True)
            return False
    
    def get_status(self):
        """Récupère le statut du déploiement."""
        return self.target.get_status(self.app)
    
    def get_logs(self, lines=100):
        """Récupère les logs du déploiement."""
        return self.target.get_logs(self.app, lines)
    
    def rollback(self, version=None):
        """Effectue un rollback vers une version précédente."""
        # Implémentation du rollback
        pass
