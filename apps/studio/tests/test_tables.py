"""
Tests pour les tables (DataSchema) Studio
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.foundation.models import User, Organization
from apps.studio.models import Project, Table


@pytest.mark.django_db
class TestTableCRUD:
    """Tests CRUD des tables"""
    
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
                {'name': 'email', 'type': 'email', 'required': True}
            ]
        )
        
    def test_create_table_success(self):
        """Test création de table avec succès"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('studio:table-list', kwargs={'project_id': self.project.id})
        data = {
            'table_name': 'products',
            'display_name': 'Products',
            'fields_config': [
                {'name': 'name', 'type': 'string', 'required': True},
                {'name': 'price', 'type': 'decimal', 'required': True}
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['table_name'] == 'products'
        assert Table.objects.filter(table_name='products').exists()
        
    def test_create_table_without_fields(self):
        """Test création de table sans champs"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('studio:table-list', kwargs={'project_id': self.project.id})
        data = {
            'table_name': 'empty_table',
            'display_name': 'Empty Table',
            'fields_config': []
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST
        ]
        
    def test_get_table_detail(self):
        """Test récupération détails table"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('studio:table-detail', kwargs={
            'project_id': self.project.id,
            'pk': self.table.id
        })
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['table_name'] == 'clients'
        
    def test_update_table_fields(self):
        """Test modification des champs de la table"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('studio:table-detail', kwargs={
            'project_id': self.project.id,
            'pk': self.table.id
        })
        data = {
            'fields_config': [
                {'name': 'nom', 'type': 'string', 'required': True},
                {'name': 'email', 'type': 'email', 'required': True},
                {'name': 'telephone', 'type': 'string', 'required': False}
            ]
        }
        
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['fields_config']) == 3
        
    def test_delete_table(self):
        """Test suppression table"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('studio:table-detail', kwargs={
            'project_id': self.project.id,
            'pk': self.table.id
        })
        response = self.client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Table.objects.filter(id=self.table.id).exists()


@pytest.mark.django_db
class TestTableFieldTypes:
    """Tests types de champs des tables"""
    
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
        
    def test_create_table_with_various_field_types(self):
        """Test création avec différents types de champs"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('studio:table-list', kwargs={'project_id': self.project.id})
        data = {
            'table_name': 'complete_table',
            'display_name': 'Complete Table',
            'fields_config': [
                {'name': 'text_field', 'type': 'string'},
                {'name': 'number_field', 'type': 'integer'},
                {'name': 'decimal_field', 'type': 'decimal'},
                {'name': 'boolean_field', 'type': 'boolean'},
                {'name': 'date_field', 'type': 'date'},
                {'name': 'datetime_field', 'type': 'datetime'},
                {'name': 'email_field', 'type': 'email'},
                {'name': 'url_field', 'type': 'url'},
                {'name': 'json_field', 'type': 'json'},
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data['fields_config']) == 9
        
    def test_create_table_with_foreign_key(self):
        """Test création avec clé étrangère"""
        self.client.force_authenticate(user=self.owner)
        
        related_table = Table.objects.create(
            project=self.project,
            table_name='categories',
            display_name='Categories',
            fields_config=[{'name': 'name', 'type': 'string'}]
        )
        
        url = reverse('studio:table-list', kwargs={'project_id': self.project.id})
        data = {
            'table_name': 'products',
            'display_name': 'Products',
            'fields_config': [
                {'name': 'name', 'type': 'string'},
                {
                    'name': 'category',
                    'type': 'foreign_key',
                    'related_table': 'categories'
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestTableValidation:
    """Tests validation des tables"""
    
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
        
    def test_create_table_with_duplicate_name(self):
        """Test création avec nom déjà existant"""
        Table.objects.create(
            project=self.project,
            table_name='clients',
            display_name='Clients',
            fields_config=[{'name': 'name', 'type': 'string'}]
        )
        
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('studio:table-list', kwargs={'project_id': self.project.id})
        data = {
            'table_name': 'clients',
            'display_name': 'Clients Duplicate',
            'fields_config': [{'name': 'name', 'type': 'string'}]
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_create_table_with_invalid_field_type(self):
        """Test création avec type de champ invalide"""
        self.client.force_authenticate(user=self.owner)
        
        url = reverse('studio:table-list', kwargs={'project_id': self.project.id})
        data = {
            'table_name': 'invalid_table',
            'display_name': 'Invalid Table',
            'fields_config': [
                {'name': 'field', 'type': 'invalid_type'}
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
