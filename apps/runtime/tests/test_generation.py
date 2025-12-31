"""
Tests pour la génération de code
"""

import pytest
import os
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.foundation.models import User, Organization
from apps.studio.models import Project, Table
from apps.runtime.models import GeneratedApp
from apps.runtime.services.code_generator import AppGenerator


@pytest.mark.django_db
class TestCodeGeneration:
    """Tests génération de code Django"""
    
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
        
        self.table = Table.objects.create(
            project=self.project,
            table_name='clients',
            display_name='Clients',
            fields_config=[
                {'name': 'nom', 'type': 'string', 'required': True},
                {'name': 'email', 'type': 'email', 'required': True},
                {'name': 'age', 'type': 'integer', 'required': False}
            ]
        )
        
    def test_create_generated_app(self):
        """Test création d'une application générée"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('runtime:generated-app-list')
        data = {
            'project_id': self.project.id,
            'name': 'Test App',
            'deployment_target': 'local'
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Test App'
        assert GeneratedApp.objects.filter(name='Test App').exists()
        
    def test_generate_models_code(self):
        """Test génération du code des modèles"""
        generator = AppGenerator(self.project)
        models_code = generator.generate_models()
        
        assert models_code is not None
        assert 'class Client' in models_code or 'clients' in models_code.lower()
        assert 'nom' in models_code
        assert 'email' in models_code
        assert 'age' in models_code
        
    def test_generate_serializers_code(self):
        """Test génération du code des serializers"""
        generator = AppGenerator(self.project)
        serializers_code = generator.generate_serializers()
        
        assert serializers_code is not None
        assert 'Serializer' in serializers_code
        assert 'ModelSerializer' in serializers_code or 'serializers' in serializers_code
        
    def test_generate_views_code(self):
        """Test génération du code des vues"""
        generator = AppGenerator(self.project)
        views_code = generator.generate_views()
        
        assert views_code is not None
        assert 'ViewSet' in views_code or 'APIView' in views_code
        
    def test_generate_urls_code(self):
        """Test génération du code des URLs"""
        generator = AppGenerator(self.project)
        urls_code = generator.generate_urls()
        
        assert urls_code is not None
        assert 'urlpatterns' in urls_code
        assert 'path' in urls_code or 'url' in urls_code
        
    def test_generate_admin_code(self):
        """Test génération du code admin"""
        generator = AppGenerator(self.project)
        admin_code = generator.generate_admin()
        
        assert admin_code is not None
        assert 'admin' in admin_code.lower()
        assert 'register' in admin_code.lower() or 'ModelAdmin' in admin_code


@pytest.mark.django_db
class TestGeneratedAppFiles:
    """Tests création des fichiers générés"""
    
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
            table_name='products',
            display_name='Products',
            fields_config=[
                {'name': 'name', 'type': 'string', 'required': True},
                {'name': 'price', 'type': 'decimal', 'required': True}
            ]
        )
        
        self.app = GeneratedApp.objects.create(
            project=self.project,
            name='Test App',
            deployment_target='local'
        )
        
    def test_generate_code_creates_files(self):
        """Test que la génération crée bien les fichiers"""
        self.app.generate_code()
        
        app_dir = os.path.join('generated_apps', f'app_{self.project.id}')
        
        assert os.path.exists(os.path.join(app_dir, 'models.py'))
        assert os.path.exists(os.path.join(app_dir, 'serializers.py'))
        assert os.path.exists(os.path.join(app_dir, 'views.py'))
        assert os.path.exists(os.path.join(app_dir, 'urls.py'))
        assert os.path.exists(os.path.join(app_dir, 'admin.py'))
        
    def test_regenerate_code_overwrites_files(self):
        """Test que régénérer écrase les fichiers"""
        self.app.generate_code()
        
        first_generation_time = self.app.generated_at
        
        self.app.generate_code()
        
        self.app.refresh_from_db()
        assert self.app.generated_at > first_generation_time


@pytest.mark.django_db
class TestGenerationWithMultipleTables:
    """Tests génération avec plusieurs tables"""
    
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
            table_name='categories',
            display_name='Categories',
            fields_config=[
                {'name': 'name', 'type': 'string', 'required': True}
            ]
        )
        
        Table.objects.create(
            project=self.project,
            table_name='products',
            display_name='Products',
            fields_config=[
                {'name': 'name', 'type': 'string', 'required': True},
                {'name': 'price', 'type': 'decimal', 'required': True},
                {'name': 'category', 'type': 'foreign_key', 'related_table': 'categories'}
            ]
        )
        
    def test_generate_code_with_relations(self):
        """Test génération avec relations entre tables"""
        generator = AppGenerator(self.project)
        models_code = generator.generate_models()
        
        assert 'Category' in models_code or 'categories' in models_code.lower()
        assert 'Product' in models_code or 'products' in models_code.lower()
        assert 'ForeignKey' in models_code or 'foreign' in models_code.lower()


@pytest.mark.django_db
class TestGenerationErrors:
    """Tests gestion des erreurs de génération"""
    
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
        
    def test_generate_without_tables(self):
        """Test génération sans tables (projet vide)"""
        project = Project.objects.create(
            name='Empty Project',
            organization=self.org,
            created_by=self.owner
        )
        
        generator = AppGenerator(project)
        models_code = generator.generate_models()
        
        assert models_code is not None
        assert 'BaseModel' in models_code or 'models' in models_code
        
    def test_generate_with_invalid_field_type(self):
        """Test génération avec type de champ invalide"""
        project = Project.objects.create(
            name='Test Project',
            organization=self.org,
            created_by=self.owner
        )
        
        Table.objects.create(
            project=project,
            table_name='invalid_table',
            display_name='Invalid Table',
            fields_config=[
                {'name': 'field', 'type': 'invalid_type'}
            ]
        )
        
        generator = AppGenerator(project)
        
        try:
            models_code = generator.generate_models()
            assert models_code is not None
        except Exception as e:
            assert 'invalid' in str(e).lower() or 'type' in str(e).lower()
