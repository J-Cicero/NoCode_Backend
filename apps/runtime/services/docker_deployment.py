"""
Service de déploiement Docker pour les applications générées.
Crée des conteneurs Docker isolés pour chaque application NoCode.
"""

import os
import logging
import subprocess
import tempfile
from pathlib import Path
from django.conf import settings
from django.template import Template, Context

logger = logging.getLogger(__name__)


class DockerDeploymentService:
    """Service de déploiement Docker pour les applications générées."""
    
    def __init__(self, generated_app):
        self.app = generated_app
        self.project = generated_app.project
        self.app_name = f"app_{self.project.id}"
        self.container_name = f"nocode_{self.app_name}"
        self.base_dir = os.path.join(settings.BASE_DIR, 'generated_apps', self.app_name)
        
    def deploy(self):
        """Déploie l'application dans un conteneur Docker."""
        try:
            logger.info(f"Démarrage du déploiement Docker pour {self.app_name}")
            
            # 1. Générer la structure de l'application
            self._ensure_app_structure()
            
            # 2. Créer le Dockerfile
            self._create_dockerfile()
            
            # 3. Créer docker-compose.yml
            self._create_docker_compose()
            
            # 4. Créer requirements.txt
            self._create_requirements()
            
            # 5. Créer entrypoint.sh
            self._create_entrypoint()
            
            # 6. Build l'image Docker
            if not self._build_docker_image():
                return False
            
            # 7. Démarrer le conteneur
            if not self._start_container():
                return False
            
            # 8. Mettre à jour l'URL de l'application
            self._update_app_urls()
            
            logger.info(f"Déploiement Docker réussi pour {self.app_name}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du déploiement Docker: {e}", exc_info=True)
            return False
    
    def _ensure_app_structure(self):
        """Crée la structure de base de l'application."""
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, 'static'), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, 'media'), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, 'logs'), exist_ok=True)
    
    def _create_dockerfile(self):
        """Crée le Dockerfile pour l'application."""
        dockerfile_content = f"""# Dockerfile généré automatiquement pour {self.app_name}
FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings.production

# Installer les dépendances système
RUN apt-get update && apt-get install -y \\
    postgresql-client \\
    gettext \\
    && rm -rf /var/lib/apt/lists/*

# Créer le répertoire de l'application
WORKDIR /app

# Copier requirements et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY . .

# Collecter les fichiers statiques
RUN python manage.py collectstatic --noinput || true

# Rendre le script entrypoint exécutable
RUN chmod +x entrypoint.sh

# Exposer le port
EXPOSE 8000

# Point d'entrée
ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
"""
        
        dockerfile_path = os.path.join(self.base_dir, 'Dockerfile')
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        
        logger.info(f"Dockerfile créé: {dockerfile_path}")
    
    def _create_docker_compose(self):
        """Crée le fichier docker-compose.yml."""
        # Port dynamique basé sur l'ID du projet
        port = 8000 + (hash(str(self.project.id)) % 1000)
        
        compose_content = f"""version: '3.8'

services:
  web:
    build: .
    container_name: {self.container_name}
    ports:
      - "{port}:8000"
    environment:
      - DATABASE_URL=postgresql://nocode:nocode@db:5432/{self.app_name}
      - DJANGO_SECRET_KEY=${{DJANGO_SECRET_KEY:-change-me-in-production}}
      - DJANGO_DEBUG=False
      - ALLOWED_HOSTS=localhost,127.0.0.1,*
    depends_on:
      - db
    volumes:
      - ./static:/app/static
      - ./media:/app/media
      - ./logs:/app/logs
    restart: unless-stopped
    networks:
      - nocode_network

  db:
    image: postgres:15-alpine
    container_name: {self.container_name}_db
    environment:
      - POSTGRES_DB={self.app_name}
      - POSTGRES_USER=nocode
      - POSTGRES_PASSWORD=nocode
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - nocode_network
    restart: unless-stopped

volumes:
  postgres_data:

networks:
  nocode_network:
    driver: bridge
"""
        
        compose_path = os.path.join(self.base_dir, 'docker-compose.yml')
        with open(compose_path, 'w') as f:
            f.write(compose_content)
        
        logger.info(f"docker-compose.yml créé: {compose_path}")
        return port
    
    def _create_requirements(self):
        """Crée le fichier requirements.txt."""
        requirements = [
            "Django>=4.2,<5.0",
            "djangorestframework>=3.14",
            "psycopg2-binary>=2.9",
            "gunicorn>=21.2",
            "whitenoise>=6.5",
            "django-cors-headers>=4.3",
            "drf-spectacular>=0.26",
            "celery>=5.3",
            "redis>=5.0",
        ]
        
        req_path = os.path.join(self.base_dir, 'requirements.txt')
        with open(req_path, 'w') as f:
            f.write('\n'.join(requirements))
        
        logger.info(f"requirements.txt créé: {req_path}")
    
    def _create_entrypoint(self):
        """Crée le script entrypoint.sh."""
        entrypoint_content = """#!/bin/bash
set -e

echo "Attente de la base de données..."
until PGPASSWORD=nocode psql -h db -U nocode -d postgres -c "\\q" 2>/dev/null; do
  echo "Postgres n'est pas encore prêt - attente..."
  sleep 2
done

echo "Base de données prête !"

echo "Application des migrations..."
python manage.py migrate --noinput

echo "Création du superuser si nécessaire..."
python manage.py createsuperuser --noinput --username admin --email admin@example.com || true

echo "Démarrage de l'application..."
exec "$@"
"""
        
        entrypoint_path = os.path.join(self.base_dir, 'entrypoint.sh')
        with open(entrypoint_path, 'w') as f:
            f.write(entrypoint_content)
        
        # Rendre exécutable
        os.chmod(entrypoint_path, 0o755)
        
        logger.info(f"entrypoint.sh créé: {entrypoint_path}")
    
    def _build_docker_image(self):
        """Build l'image Docker."""
        try:
            logger.info(f"Build de l'image Docker pour {self.app_name}")
            
            result = subprocess.run(
                ['docker', 'build', '-t', f'nocode/{self.app_name}:latest', '.'],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                logger.error(f"Erreur lors du build Docker: {result.stderr}")
                return False
            
            logger.info(f"Image Docker buildée avec succès: nocode/{self.app_name}:latest")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout lors du build Docker")
            return False
        except FileNotFoundError:
            logger.error("Docker n'est pas installé ou n'est pas dans le PATH")
            return False
        except Exception as e:
            logger.error(f"Erreur lors du build Docker: {e}")
            return False
    
    def _start_container(self):
        """Démarre le conteneur Docker."""
        try:
            logger.info(f"Démarrage du conteneur {self.container_name}")
            
            # Arrêter le conteneur existant s'il existe
            subprocess.run(
                ['docker-compose', 'down'],
                cwd=self.base_dir,
                capture_output=True,
                timeout=60
            )
            
            # Démarrer le nouveau conteneur
            result = subprocess.run(
                ['docker-compose', 'up', '-d'],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                logger.error(f"Erreur lors du démarrage du conteneur: {result.stderr}")
                return False
            
            logger.info(f"Conteneur démarré avec succès: {self.container_name}")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout lors du démarrage du conteneur")
            return False
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du conteneur: {e}")
            return False
    
    def _update_app_urls(self):
        """Met à jour les URLs de l'application dans GeneratedApp."""
        port = 8000 + (hash(str(self.project.id)) % 1000)
        self.app.api_base_url = f"http://localhost:{port}/api/v1/"
        self.app.admin_url = f"http://localhost:{port}/admin/"
        self.app.save(update_fields=['api_base_url', 'admin_url'])
    
    def stop(self):
        """Arrête le conteneur Docker."""
        try:
            logger.info(f"Arrêt du conteneur {self.container_name}")
            
            result = subprocess.run(
                ['docker-compose', 'down'],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.error(f"Erreur lors de l'arrêt du conteneur: {result.stderr}")
                return False
            
            logger.info(f"Conteneur arrêté avec succès: {self.container_name}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt du conteneur: {e}")
            return False
    
    def get_logs(self, lines=100):
        """Récupère les logs du conteneur."""
        try:
            result = subprocess.run(
                ['docker-compose', 'logs', '--tail', str(lines), 'web'],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return [f"Erreur lors de la récupération des logs: {result.stderr}"]
            
            return result.stdout.split('\n')
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des logs: {e}")
            return [f"Erreur: {str(e)}"]
    
    def get_status(self):
        """Récupère le statut du conteneur."""
        try:
            result = subprocess.run(
                ['docker-compose', 'ps', '--format', 'json'],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {"status": "error", "message": result.stderr}
            
            import json
            containers = json.loads(result.stdout) if result.stdout.strip() else []
            
            if not containers:
                return {"status": "stopped", "message": "Conteneur non démarré"}
            
            web_container = next((c for c in containers if 'web' in c.get('Service', '')), None)
            
            if web_container:
                state = web_container.get('State', 'unknown')
                return {
                    "status": "running" if state == "running" else state,
                    "container": web_container
                }
            
            return {"status": "unknown", "message": "Conteneur introuvable"}
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut: {e}")
            return {"status": "error", "message": str(e)}
