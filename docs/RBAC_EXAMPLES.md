# Exemples d'implémentation RBAC

Ce document fournit des exemples concrets d'utilisation du système RBAC dans les ViewSets.

## Exemple 1: ViewSet pour utilisateur simple

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.foundation.permissions.rbac import IsUserSimple
from apps.foundation.models import User
from apps.foundation.serializers import UserProfileSerializer

class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Profil utilisateur - accessible uniquement par l'utilisateur lui-même.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsUserSimple]
    
    def get_queryset(self):
        """Retourne uniquement le profil de l'utilisateur connecté."""
        return User.objects.filter(id=self.request.user.id)
    
    def get_object(self):
        """Retourne toujours le profil de l'utilisateur connecté."""
        return self.request.user
```

## Exemple 2: ViewSet pour organisations avec RBAC

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.foundation.permissions.rbac import (
    IsOrganizationCreator,
    CanCreateOrganization,
    CanInviteMembers,
    CanRemoveMembers,
    IsOrganizationOwner,
)
from apps.foundation.models import Organization, OrganizationMember
from apps.foundation.serializers import OrganizationSerializer

class OrganizationViewSet(viewsets.ModelViewSet):
    """
    Gestion des organisations avec RBAC.
    """
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """
        Permissions dynamiques selon l'action.
        """
        if self.action == 'create':
            permission_classes = [IsAuthenticated, CanCreateOrganization]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsOrganizationOwner]
        else:
            permission_classes = [IsAuthenticated, IsOrganizationCreator]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Retourne les organisations de l'utilisateur."""
        user = self.request.user
        
        # Organisations dont l'utilisateur est propriétaire
        owned_orgs = Organization.objects.filter(owner=user)
        
        # Organisations dont l'utilisateur est membre
        member_orgs = Organization.objects.filter(
            members__user=user,
            members__status='ACTIVE'
        )
        
        return (owned_orgs | member_orgs).distinct()
    
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated, CanInviteMembers]
    )
    def invite_member(self, request, pk=None):
        """
        Inviter un membre dans l'organisation.
        Seuls les OWNER peuvent inviter.
        """
        organization = self.get_object()
        email = request.data.get('email')
        role = request.data.get('role', 'MEMBER')
        
        # Logique d'invitation
        # ...
        
        return Response({'message': 'Invitation envoyée'}, status=status.HTTP_201_CREATED)
    
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated, CanRemoveMembers]
    )
    def remove_member(self, request, pk=None):
        """
        Supprimer un membre de l'organisation.
        Seuls les OWNER peuvent supprimer des membres.
        """
        organization = self.get_object()
        member_id = request.data.get('member_id')
        
        # Logique de suppression
        # ...
        
        return Response({'message': 'Membre supprimé'}, status=status.HTTP_200_OK)
```

## Exemple 3: ViewSet avec permission composée

```python
from rest_framework import viewsets
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from apps.foundation.permissions.rbac import IsOwnerOrOrgMember
from apps.studio.models import Project
from apps.studio.serializers import ProjectSerializer

class ProjectViewSet(viewsets.ModelViewSet):
    """
    Projets - accessible par le propriétaire ou les membres de l'organisation.
    """
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrOrgMember]
    
    def get_queryset(self):
        """Retourne les projets accessibles à l'utilisateur."""
        user = self.request.user
        
        # Projets personnels (sans organisation)
        personal_projects = Project.objects.filter(
            created_by=user,
            organization__isnull=True
        )
        
        # Projets des organisations dont l'utilisateur est membre
        org_projects = Project.objects.filter(
            organization__members__user=user,
            organization__members__status='ACTIVE'
        )
        
        return (personal_projects | org_projects).distinct()
    
    def perform_create(self, serializer):
        """Crée un projet avec le créateur automatiquement assigné."""
        serializer.save(created_by=self.request.user)
```

## Exemple 4: Action conditionnelle selon le rôle

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.foundation.permissions.rbac import (
    IsOrganizationMember,
    IsOrganizationOwner,
    get_user_role_in_organization,
    UserRole,
)
from apps.runtime.models import GeneratedApp
from apps.runtime.serializers import GeneratedAppSerializer

class GeneratedAppViewSet(viewsets.ModelViewSet):
    """
    Applications générées avec permissions selon le rôle dans l'organisation.
    """
    serializer_class = GeneratedAppSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]
    
    def get_queryset(self):
        """Retourne les apps accessibles selon le rôle."""
        user = self.request.user
        
        # Apps personnelles
        personal_apps = GeneratedApp.objects.filter(
            project__created_by=user,
            project__organization__isnull=True
        )
        
        # Apps des organisations
        org_apps = GeneratedApp.objects.filter(
            project__organization__members__user=user,
            project__organization__members__status='ACTIVE'
        )
        
        return (personal_apps | org_apps).distinct()
    
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated, IsOrganizationOwner]
    )
    def deploy(self, request, pk=None):
        """
        Déployer une application.
        Seuls les OWNER peuvent déployer.
        """
        app = self.get_object()
        
        # Vérifier le rôle dans l'organisation
        if app.project.organization:
            role = get_user_role_in_organization(
                request.user,
                app.project.organization
            )
            
            if role != UserRole.ORGANIZATION_OWNER:
                return Response(
                    {'error': 'Seuls les propriétaires peuvent déployer'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Logique de déploiement
        # ...
        
        return Response({'message': 'Déploiement lancé'}, status=status.HTTP_202_ACCEPTED)
```

## Exemple 5: Test sans superuser

```python
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.foundation.models import User, Organization, OrganizationMember
from apps.studio.models import Project

class ProjectAPITest(TestCase):
    """Tests de l'API projets sans superuser."""
    
    def setUp(self):
        # Créer un utilisateur normal (pas superuser)
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass123',
            nom='User',
            prenom='Test'
        )
        
        # Créer une organisation pour devenir ORGANIZATION_CREATOR
        self.org = Organization.objects.create(
            name='Test Organization',
            owner=self.user
        )
        
        # Créer un membre dans l'organisation
        self.member = User.objects.create_user(
            email='member@example.com',
            password='testpass123',
            nom='Member',
            prenom='Test'
        )
        OrganizationMember.objects.create(
            organization=self.org,
            user=self.member,
            role='MEMBER',
            status='ACTIVE'
        )
        
        self.client = APIClient()
    
    def test_user_can_create_project(self):
        """Test qu'un ORGANIZATION_CREATOR peut créer un projet."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/v1/studio/projects/', {
            'name': 'Test Project',
            'organization': self.org.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_member_can_view_org_projects(self):
        """Test qu'un ORGANIZATION_MEMBER peut voir les projets de l'org."""
        # Créer un projet dans l'organisation
        project = Project.objects.create(
            name='Org Project',
            created_by=self.user,
            organization=self.org
        )
        
        self.client.force_authenticate(user=self.member)
        
        response = self.client.get('/api/v1/studio/projects/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(project.id, [p['id'] for p in response.data['results']])
    
    def test_member_cannot_delete_project(self):
        """Test qu'un MEMBER ne peut pas supprimer un projet."""
        project = Project.objects.create(
            name='Org Project',
            created_by=self.user,
            organization=self.org
        )
        
        self.client.force_authenticate(user=self.member)
        
        response = self.client.delete(f'/api/v1/studio/projects/{project.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
```

## Exemple 6: Utilisation dans les serializers

```python
from rest_framework import serializers
from apps.foundation.permissions.rbac import get_user_role, UserRole

class ProjectSerializer(serializers.ModelSerializer):
    """Serializer avec logique conditionnelle selon le rôle."""
    
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = ['id', 'name', 'can_edit', 'can_delete']
    
    def get_can_edit(self, obj):
        """Détermine si l'utilisateur peut éditer."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        # Propriétaire peut toujours éditer
        if obj.created_by == request.user:
            return True
        
        # OWNER peut éditer les projets de l'organisation
        if obj.organization:
            from apps.foundation.permissions.rbac import get_user_role_in_organization
            role = get_user_role_in_organization(request.user, obj.organization)
            return role == UserRole.ORGANIZATION_OWNER
        
        return False
    
    def get_can_delete(self, obj):
        """Détermine si l'utilisateur peut supprimer."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        # Seul le propriétaire ou OWNER peut supprimer
        if obj.created_by == request.user:
            return True
        
        if obj.organization:
            from apps.foundation.permissions.rbac import get_user_role_in_organization
            role = get_user_role_in_organization(request.user, obj.organization)
            return role == UserRole.ORGANIZATION_OWNER
        
        return False
```

## Notes importantes

1. **Toujours utiliser les permissions RBAC** au lieu de `is_staff`/`is_superuser` dans les endpoints métier
2. **Django Admin reste disponible** mais uniquement pour l'administration interne
3. **Tous les tests doivent fonctionner** sans créer de superuser
4. **Swagger est utilisable** par un utilisateur normal authentifié via JWT

