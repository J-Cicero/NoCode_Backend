# Mapping RBAC - Rôles et Permissions

## Vue d'ensemble

Ce document décrit le système RBAC (Role-Based Access Control) de la plateforme NoCode. Les rôles métier remplacent les dépendances à `is_staff` et `is_superuser` dans les endpoints métier.

## Rôles Métier

### 1. USER_SIMPLE

**Description:** Utilisateur de base, peut consulter ses propres données uniquement.

**Caractéristiques:**
- Ne peut pas créer d'organisation
- Ne peut pas gérer d'autres utilisateurs
- Accès limité à ses propres ressources

**Actions autorisées:**
- ✅ Consulter ses propres données (profil, projets personnels)
- ✅ Modifier son propre profil
- ✅ Créer des projets personnels (sans organisation)
- ❌ Créer une organisation
- ❌ Gérer d'autres utilisateurs
- ❌ Accéder aux ressources d'autres utilisateurs

**Permissions DRF:**
```python
from apps.foundation.permissions.rbac import IsUserSimple

class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsUserSimple]
```

---

### 2. ORGANIZATION_CREATOR

**Description:** Utilisateur qui a créé au moins une organisation. Devient automatiquement OWNER de son organisation.

**Caractéristiques:**
- Peut créer des organisations
- Devient automatiquement OWNER de son organisation
- Peut inviter / supprimer des membres dans ses organisations
- Peut gérer toutes les ressources de ses organisations

**Actions autorisées:**
- ✅ Créer une organisation
- ✅ Gérer ses propres organisations (modifier, supprimer)
- ✅ Inviter des membres dans ses organisations
- ✅ Supprimer des membres de ses organisations
- ✅ Gérer tous les projets de ses organisations
- ✅ Accéder à toutes les ressources de ses organisations
- ✅ Consulter ses propres données personnelles

**Permissions DRF:**
```python
from apps.foundation.permissions.rbac import IsOrganizationCreator, CanInviteMembers

class OrganizationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOrganizationCreator]
    
    @action(detail=True, methods=['post'], permission_classes=[CanInviteMembers])
    def invite_member(self, request, pk=None):
        # Inviter un membre
        pass
```

---

### 3. ORGANIZATION_MEMBER

**Description:** Membre d'une organisation (rôle MEMBER ou OWNER).

**Caractéristiques:**
- Appartient à une organisation
- Accès limité aux ressources de l'organisation
- Ne peut ni inviter ni supprimer d'autres membres (seul OWNER peut le faire)

**Sous-rôles dans l'organisation:**
- **MEMBER:** Accès en lecture/écriture aux ressources
- **OWNER:** Contrôle total sur l'organisation (celui qui crée l'organisation devient OWNER)

**Actions autorisées selon sous-rôle:**

#### MEMBER
- ✅ Consulter les ressources de l'organisation
- ✅ Créer des projets dans l'organisation
- ✅ Modifier ses propres ressources
- ❌ Inviter des membres
- ❌ Supprimer des membres
- ❌ Modifier les paramètres de l'organisation
- ❌ Supprimer l'organisation

#### OWNER (ORGANIZATION_CREATOR)
- ✅ Toutes les actions de MEMBER
- ✅ Inviter des membres
- ✅ Supprimer des membres
- ✅ Modifier les projets de l'organisation
- ✅ Gérer les ressources de l'organisation
- ✅ Supprimer l'organisation
- ✅ Transférer la propriété
- ✅ Modifier tous les paramètres de l'organisation

**Permissions DRF:**
```python
from apps.foundation.permissions.rbac import (
    IsOrganizationMember,
    IsOrganizationOwner,
    CanInviteMembers,
    CanRemoveMembers
)

# Pour les membres
class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

# Pour les owners (créateurs d'organisation)
class MemberManagementViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOrganizationOwner, CanInviteMembers]

# Pour les settings d'organisation
class OrganizationSettingsViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOrganizationOwner]
```

---

## Mapping RÔLE → ACTIONS AUTORISÉES

### Endpoints Foundation

| Endpoint | USER_SIMPLE | ORGANIZATION_CREATOR | ORGANIZATION_MEMBER |
|----------|-------------|---------------------|---------------------|
| `GET /api/v1/foundation/auth/me/` | ✅ | ✅ | ✅ |
| `POST /api/v1/foundation/organizations/` | ❌ | ✅ | ❌ |
| `GET /api/v1/foundation/organizations/` | ✅ (ses orgs) | ✅ (ses orgs) | ✅ (ses orgs) |
| `PUT /api/v1/foundation/organizations/{id}/` | ❌ | ✅ (si owner) | ❌ |
| `DELETE /api/v1/foundation/organizations/{id}/` | ❌ | ✅ (si owner) | ❌ |
| `POST /api/v1/foundation/organizations/{id}/invite/` | ❌ | ✅ (si admin/owner) | ❌ |
| `POST /api/v1/foundation/organizations/{id}/members/{id}/remove/` | ❌ | ✅ (si owner) | ❌ |

### Endpoints Studio

| Endpoint | USER_SIMPLE | ORGANIZATION_CREATOR | ORGANIZATION_MEMBER |
|----------|-------------|---------------------|---------------------|
| `POST /api/v1/studio/projects/` | ✅ (perso) | ✅ | ✅ |
| `GET /api/v1/studio/projects/` | ✅ (ses projets) | ✅ (ses projets) | ✅ (projets org) |
| `PUT /api/v1/studio/projects/{id}/` | ✅ (si owner) | ✅ (si owner ou org admin) | ✅ (si owner ou org admin) |
| `DELETE /api/v1/studio/projects/{id}/` | ✅ (si owner) | ✅ (si owner ou org admin) | ❌ (sauf si owner) |
| `POST /api/v1/studio/projects/{id}/tables/` | ✅ (si owner) | ✅ (si owner ou org admin) | ✅ (si org member) |

### Endpoints Runtime

| Endpoint | USER_SIMPLE | ORGANIZATION_CREATOR | ORGANIZATION_MEMBER |
|----------|-------------|---------------------|---------------------|
| `POST /api/v1/runtime/apps/` | ✅ (si project owner) | ✅ | ✅ (si org member) |
| `GET /api/v1/runtime/apps/` | ✅ (ses apps) | ✅ (ses apps) | ✅ (apps org) |
| `POST /api/v1/runtime/apps/{id}/deploy/` | ✅ (si owner) | ✅ (si owner ou org admin) | ❌ (sauf si owner) |

---

## Exemples d'implémentation

### Exemple 1: ViewSet avec permission simple

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.foundation.permissions.rbac import IsUserSimple

class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """Profil utilisateur - accessible uniquement par l'utilisateur lui-même."""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsUserSimple]
    
    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)
```

### Exemple 2: ViewSet avec permission composée

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.foundation.permissions.rbac import IsOwnerOrOrgMember

class ProjectViewSet(viewsets.ModelViewSet):
    """Projets - accessible par le propriétaire ou les membres de l'organisation."""
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrOrgMember]
    
    def get_queryset(self):
        user = self.request.user
        # Logique de filtrage selon le rôle
        return Project.objects.filter(
            Q(created_by=user) | 
            Q(organization__members__user=user, organization__members__status='ACTIVE')
        )
```

### Exemple 3: Action personnalisée avec permission spécifique

```python
from rest_framework.decorators import action
from apps.foundation.permissions.rbac import CanInviteMembers

class OrganizationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOrganizationCreator]
    
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated, CanInviteMembers]
    )
    def invite_member(self, request, pk=None):
        """Inviter un membre - uniquement pour OWNER."""
        organization = self.get_object()
        # Logique d'invitation
        pass
```

---

## Comparaison avec Spring Boot / Spring Security

### Spring Boot équivalent

```java
// Rôle USER_SIMPLE
@PreAuthorize("hasRole('USER_SIMPLE')")
public class UserProfileController {
    // ...
}

// Rôle ORGANIZATION_CREATOR
@PreAuthorize("hasRole('ORGANIZATION_CREATOR')")
public class OrganizationController {
    // ...
}

// Permission composée
@PreAuthorize("hasRole('ORGANIZATION_MEMBER') or @organizationService.isOwner(#orgId, authentication.name)")
public ResponseEntity<?> manageProject(@PathVariable Long orgId) {
    // ...
}
```

### Django REST Framework équivalent

```python
# Rôle USER_SIMPLE
class UserProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsUserSimple]

# Rôle ORGANIZATION_CREATOR
class OrganizationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOrganizationCreator]

# Permission composée
class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrOrgMember]
```

---

## Migration depuis is_staff/is_superuser

### Avant (avec is_staff)

```python
class MyViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return MyModel.objects.all()
        return MyModel.objects.filter(created_by=user)
```

### Après (avec RBAC)

```python
from apps.foundation.permissions.rbac import IsOwnerOrOrgMember

class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrOrgMember]
    
    def get_queryset(self):
        user = self.request.user
        # Le filtrage est géré par la permission
        return MyModel.objects.filter(
            Q(created_by=user) | 
            Q(organization__members__user=user, organization__members__status='ACTIVE')
        )
```

---

## Tests sans superuser

Tous les tests doivent fonctionner sans créer de superuser. Exemple:

```python
from django.test import TestCase
from rest_framework.test import APIClient
from apps.foundation.models import User, Organization

class MyAPITest(TestCase):
    def setUp(self):
        # Créer un utilisateur normal (pas superuser)
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nom='Test',
            prenom='User'
        )
        
        # Créer une organisation pour devenir ORGANIZATION_CREATOR
        self.org = Organization.objects.create(
            name='Test Org',
            owner=self.user
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_user_can_access_own_resources(self):
        # Test que l'utilisateur peut accéder à ses ressources
        response = self.client.get('/api/v1/foundation/auth/me/')
        self.assertEqual(response.status_code, 200)
```

---

## Notes importantes

1. **Django Admin reste disponible** mais uniquement pour l'administration interne (is_staff/is_superuser)
2. **Aucun endpoint métier ne dépend de is_staff/is_superuser**
3. **Swagger est utilisable** par un utilisateur normal authentifié via JWT
4. **Le système est prêt pour la montée en charge** avec multi-organisations

