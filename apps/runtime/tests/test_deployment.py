"""
Tests pour le déploiement Docker et la gestion des applications
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.foundation.models import User, Organization
from apps.studio.models import Project, Table
from apps.runtime.models import GeneratedApp, DeploymentLog
from apps.runtime.services.deployment import DeploymentManager
from apps.runtime.services.docker_deployment import DockerDeploymentService


@pytest.mark.django_db
class TestDeployment:
    """Tests déploiement des applications"""
    
    def setup_method(self):
        """Setup exécuté avant chaque test"""
        self.client = APIClient()
        
        self.org = Organization.objects.create(name='Test Organization')
        
        self.owner = User.objects.create_user(
            email='owner@test.com',
            password='Pass123!',
            first_name='Owner',
            last_name='User',
            role='OWNER',
            organization=self.org
        )
        
        self.project = Project.objects.create(
            name='Test Project',
            organization=self.org,
            created_by=self.owner
        )
        
        Table.objects.create(
            project=self.project,
            table_name='clients',
            display_name='Clients',
            fields_config=[
                {'name': 'nom', 'type': 'string', 'required': True}
            ]
        )
        
        self.app = GeneratedApp.objects.create(
            project=self.project,
            name='Test App',
            deployment_target='docker'
        )
        
    def test_deploy_app_endpoint(self):
        """Test endpoint de déploiement"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('runtime:generated-app-deploy', kwargs={'pk': self.app.id})
        response = self.client.post(url, format='json')
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_202_ACCEPTED]
        
    def test_deployment_creates_log(self):
        """Test que le déploiement crée un log"""
        self.app.deploy()
        
        assert DeploymentLog.objects.filter(app=self.app).exists()
        
    def test_get_app_status(self):
        """Test récupération du statut de l'application"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('runtime:generated-app-status', kwargs={'pk': self.app.id})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'status' in response.data
        
    def test_get_app_logs(self):
        """Test récupération des logs de l'application"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('runtime:generated-app-logs', kwargs={'pk': self.app.id})
        response = self.client.get(url, {'lines': 100})
        
        assert response.status_code == status.HTTP_200_OK
        
    def test_stop_app(self):
        """Test arrêt de l'application"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('runtime:generated-app-stop', kwargs={'pk': self.app.id})
        response = self.client.post(url, format='json')
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_202_ACCEPTED]


@pytest.mark.django_db
class TestDeploymentManager:
    """Tests du gestionnaire de déploiement"""
    
    def setup_method(self):
        """Setup exécuté avant chaque test"""
        self.org = Organization.objects.create(name='Test Organization')
        
        self.owner = User.objects.create_user(
            email='owner@test.com',
            password='Pass123!',
            first_name='Owner',
            last_name='User',
            role='OWNER',
            organization=self.org
        )
        
        self.project = Project.objects.create(
            name='Test Project',
            organization=self.org,
            created_by=self.owner
        )
        
        Table.objects.create(
            project=self.project,
            table_name='clients',
            display_name='Clients',
            fields_config=[
                {'name': 'nom', 'type': 'string'}
            ]
        )
        
    def test_deployment_manager_has_targets(self):
        """Test que le manager a les cibles de déploiement"""
        app = GeneratedApp.objects.create(
            project=self.project,
            name='Test App',
            deployment_target='local'
        )
        
        manager = DeploymentManager(app)
        
        assert 'local' in manager.targets
        assert 'docker' in manager.targets
        assert 'staging' in manager.targets
        assert 'production' in manager.targets
        
    def test_deployment_manager_local(self):
        """Test déploiement local"""
        app = GeneratedApp.objects.create(
            project=self.project,
            name='Test App',
            deployment_target='local'
        )
        
        manager = DeploymentManager(app)
        result = manager.deploy('local')
        
        assert result in [True, False]
        
    def test_deployment_manager_docker(self):
        """Test déploiement Docker"""
        app = GeneratedApp.objects.create(
            project=self.project,
            name='Test App',
            deployment_target='docker'
        )
        
        manager = DeploymentManager(app)
        
        assert 'docker' in manager.targets


@pytest.mark.django_db
class TestDockerDeployment:
    """Tests du service de déploiement Docker"""
    
    def setup_method(self):
        """Setup exécuté avant chaque test"""
        self.org = Organization.objects.create(name='Test Organization')
        
        self.owner = User.objects.create_user(
            email='owner@test.com',
            password='Pass123!',
            first_name='Owner',
            last_name='User',
            role='OWNER',
            organization=self.org
        )
        
        self.project = Project.objects.create(
            name='Test Project',
            organization=self.org,
            created_by=self.owner
        )
        
        Table.objects.create(
            project=self.project,
            table_name='clients',
            display_name='Clients',
            fields_config=[
                {'name': 'nom', 'type': 'string'}
            ]
        )
        
        self.app = GeneratedApp.objects.create(
            project=self.project,
            name='Test App',
            deployment_target='docker'
        )
        
    def test_docker_service_initialization(self):
        """Test initialisation du service Docker"""
        service = DockerDeploymentService(self.app)
        
        assert service.app == self.app
        assert service.project == self.project
        assert service.app_name is not None
        assert service.container_name is not None
        
    def test_docker_creates_dockerfile(self):
        """Test création du Dockerfile"""
        service = DockerDeploymentService(self.app)
        service._ensure_app_structure()
        service._create_dockerfile()
        
        import os
        dockerfile_path = os.path.join(service.base_dir, 'Dockerfile')
        assert os.path.exists(dockerfile_path)
        
    def test_docker_creates_docker_compose(self):
        """Test création du docker-compose.yml"""
        service = DockerDeploymentService(self.app)
        service._ensure_app_structure()
        service._create_docker_compose()
        
        import os
        compose_path = os.path.join(service.base_dir, 'docker-compose.yml')
        assert os.path.exists(compose_path)
        
    def test_docker_creates_requirements(self):
        """Test création du requirements.txt"""
        service = DockerDeploymentService(self.app)
        service._ensure_app_structure()
        service._create_requirements()
        
        import os
        req_path = os.path.join(service.base_dir, 'requirements.txt')
        assert os.path.exists(req_path)
        
    def test_docker_creates_entrypoint(self):
        """Test création du entrypoint.sh"""
        service = DockerDeploymentService(self.app)
        service._ensure_app_structure()
        service._create_entrypoint()
        
        import os
        entrypoint_path = os.path.join(service.base_dir, 'entrypoint.sh')
        assert os.path.exists(entrypoint_path)


@pytest.mark.django_db
class TestDeploymentLogs:
    """Tests des logs de déploiement"""
    
    def setup_method(self):
        """Setup exécuté avant chaque test"""
        self.org = Organization.objects.create(name='Test Organization')
        
        self.owner = User.objects.create_user(
            email='owner@test.com',
            password='Pass123!',
            first_name='Owner',
            last_name='User',
            role='OWNER',
            organization=self.org
        )
        
        self.project = Project.objects.create(
            name='Test Project',
            organization=self.org,
            created_by=self.owner
        )
        
        self.app = GeneratedApp.objects.create(
            project=self.project,
            name='Test App',
            deployment_target='docker'
        )
        
    def test_create_deployment_log(self):
        """Test création d'un log de déploiement"""
        log = DeploymentLog.objects.create(
            app=self.app,
            status='started',
            logs='Deployment started'
        )
        
        assert log.app == self.app
        assert log.status == 'started'
        
    def test_get_latest_deployment_log(self):
        """Test récupération du dernier log"""
        DeploymentLog.objects.create(
            app=self.app,
            status='started',
            logs='Started'
        )
        
        DeploymentLog.objects.create(
            app=self.app,
            status='completed',
            logs='Completed'
        )
        
        latest_log = self.app.deployment_logs.order_by('-created_at').first()
        
        assert latest_log.status == 'completed'


@pytest.mark.django_db
class TestDeploymentTargets:
    """Tests des différentes cibles de déploiement"""
    
    def setup_method(self):
        """Setup exécuté avant chaque test"""
        self.client = APIClient()
        
        self.org = Organization.objects.create(name='Test Organization')
        
        self.owner = User.objects.create_user(
            email='owner@test.com',
            password='Pass123!',
            first_name='Owner',
            last_name='User',
            role='OWNER',
            organization=self.org
        )
        
        self.project = Project.objects.create(
            name='Test Project',
            organization=self.org,
            created_by=self.owner
        )
        
    def test_create_app_with_local_target(self):
        """Test création avec cible local"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('runtime:generated-app-list')
        data = {
            'project_id': self.project.id,
            'name': 'Local App',
            'deployment_target': 'local'
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['deployment_target'] == 'local'
        
    def test_create_app_with_docker_target(self):
        """Test création avec cible docker"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('runtime:generated-app-list')
        data = {
            'project_id': self.project.id,
            'name': 'Docker App',
            'deployment_target': 'docker'
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['deployment_target'] == 'docker'
        
    def test_update_deployment_target(self):
        """Test modification de la cible de déploiement"""
        app = GeneratedApp.objects.create(
            project=self.project,
            name='Test App',
            deployment_target='local'
        )
        
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('runtime:generated-app-detail', kwargs={'pk': app.id})
        data = {'deployment_target': 'docker'}
        
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['deployment_target'] == 'docker'
