# 🔐 Authentication & Roles - NoCode Backend

## 🎯 Vue d'ensemble

Le système d'authentification NoCode Backend utilise **JWT (JSON Web Tokens)** avec SIMPLE_JWT configuré. Le système supporte l'authentification individuelle et organisationnelle avec des permissions granulaires par projet.

**Dernière mise à jour :** 20 janvier 2024

---

## 🚀 Flow d'Authentification JWT

### 1. Login - Obtention des Tokens

**Endpoint :** `POST /api/v1/foundation/auth/login/`

**Requête :**
```json
{
  "email": "user@company.com",
  "password": "UserPassword123!"
}
```

**Réponse (200) :**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyX3V1aWQiLCJpYXQiOjE2MDk0NTkyMDAsImV4cCI6MTYwOTQ2MjgwMCwianRpIjoiand0X3V1aWQiLCJ1c2VyX2lkIjoxLCJlbWFpbCI6InVzZXJAY29tcGFueS5jb20iLCJvcmdhbml6YXRpb25faWQiOm51bGx9.signature",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyX3V1aWQiLCJpYXQiOjE2MDk0NTkyMDAsImV4cCI6MTYxMjA1MTIwMH0.signature",
  "user": {
    "id": 1,
    "email": "user@company.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "last_login": "2024-01-20T12:00:00Z",
    "created_at": "2024-01-01T10:00:00Z"
  },
  "organizations": [
    {
      "id": "org-uuid-here",
      "name": "Tech Company",
      "role": "MEMBER",
      "permissions": ["read", "write"]
    }
  ],
  "permissions": {
    "can_create_projects": true,
    "can_create_organizations": true,
    "can_manage_users": false
  }
}
```

### 2. Utilisation du Access Token

**Headers pour toutes les requêtes API :**
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json
```

**Durée de vie des tokens :**
- **Access Token** : 5 minutes (configurable via `ACCESS_TOKEN_LIFETIME`)
- **Refresh Token** : 30 jours (configurable via `REFRESH_TOKEN_LIFETIME`)

### 3. Refresh du Token

**Endpoint :** `POST /api/v1/foundation/auth/refresh/`

**Requête :**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Réponse (200) :**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 4. Logout

**Endpoint :** `POST /api/v1/foundation/auth/logout/`

**Requête :**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Réponse (200) :**
```json
{
  "message": "Déconnexion réussie",
  "blacklisted": true
}
```

---

## 👥 Rôles et Permissions

### Rôles Utilisateur

| Rôle | Description | Permissions par défaut |
|------|-------------|------------------------|
| **OWNER** | Propriétaire du compte | `read`, `write`, `delete`, `admin` |
| **ADMIN** | Administrateur organisation | `read`, `write`, `delete` |
| **MEMBER** | Membre standard | `read`, `write` |
| **VIEWER** | Lecteur uniquement | `read` |

### Permissions par Module

#### Foundation Module
```json
{
  "can_login": true,
  "can_register": true,
  "can_manage_profile": true,
  "can_create_organizations": true,
  "can_manage_organizations": ["admin", "owner"],
  "can_manage_subscriptions": ["admin", "owner"]
}
```

#### Studio Module
```json
{
  "can_create_projects": true,
  "can_edit_projects": ["owner", "admin", "member"],
  "can_delete_projects": ["owner", "admin"],
  "can_publish_projects": ["owner", "admin", "member"],
  "can_manage_schemas": ["owner", "admin", "member"]
}
```

#### Runtime Module
```json
{
  "can_access_runtime_data": true,
  "can_perform_crud": ["owner", "admin", "member"],
  "can_deploy_applications": ["owner", "admin"],
  "can_view_analytics": ["owner", "admin", "member", "viewer"]
}
```

#### Automation Module
```json
{
  "can_create_workflows": ["owner", "admin", "member"],
  "can_execute_workflows": ["owner", "admin", "member"],
  "can_manage_integrations": ["owner", "admin"]
}
```

#### Insights Module
```json
{
  "can_view_analytics": true,
  "can_export_data": ["owner", "admin", "member"],
  "can_manage_tracking": ["owner", "admin"]
}
```

---

## 🏗️ Architecture Multi-tenant

### Isolation par Organisation

Chaque organisation fonctionne dans un espace isolé :

```python
# Isolation des données
class Organization(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

class Project(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    # Les projets sont automatiquement isolés par organisation
```

### Permissions par Projet

Les utilisateurs peuvent avoir des rôles différents par projet :

```json
{
  "user_id": 1,
  "project_permissions": {
    "project-uuid-1": {
      "role": "owner",
      "permissions": ["read", "write", "delete", "admin"]
    },
    "project-uuid-2": {
      "role": "member", 
      "permissions": ["read", "write"]
    },
    "project-uuid-3": {
      "role": "viewer",
      "permissions": ["read"]
    }
  }
}
```

---

## 🔒 Configuration JWT

### Settings SIMPLE_JWT

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}
```

### Claims Personnalisés

Les tokens JWT contiennent des claims personnalisés :

```python
# Dans le token access
{
  "user_id": 1,
  "email": "user@company.com",
  "organization_id": "org-uuid-here",
  "is_staff": false,
  "is_superuser": false,
  "permissions": ["read", "write"],
  "jti": "jwt-uuid-here",
  "exp": 1642694400,
  "iat": 1642691100
}
```

---

## 🛡️ Middleware de Sécurité

### Permission Classes

```python
# Permissions par défaut
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}
```

### Permissions Spécifiques

```python
# Permissions par module
class IsProjectMemberOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        return (
            user.is_superuser or
            obj.organization.members.filter(user=user).exists() or
            obj.created_by == user
        )

class CanAccessProjectData(BasePermission):
    def has_permission(self, request, view):
        project_id = view.kwargs.get('project_id')
        if not project_id:
            return False
        
        # Vérifier si l'utilisateur a accès au projet
        return Project.objects.filter(
            id=project_id,
            organization__members__user=request.user
        ).exists()
```

---

## 📊 Endpoints d'Authentification

### Authentification Utilisateur

| Endpoint | Méthode | Description | Auth requise |
|----------|---------|-------------|--------------|
| `/auth/login/` | POST | Connexion utilisateur | ❌ |
| `/auth/register/` | POST | Inscription utilisateur | ❌ |
| `/auth/logout/` | POST | Déconnexion | ✅ |
| `/auth/refresh/` | POST | Rafraîchir token | ❌ |
| `/auth/verify/` | POST | Vérifier token | ❌ |

### Gestion du Profil

| Endpoint | Méthode | Description | Auth requise |
|----------|---------|-------------|--------------|
| `/profile/` | GET | Obtenir profil utilisateur | ✅ |
| `/profile/` | PUT | Mettre à jour profil | ✅ |
| `/profile/password/` | POST | Changer mot de passe | ✅ |

### Organisation

| Endpoint | Méthode | Description | Auth requise | Permissions |
|----------|---------|-------------|--------------|-------------|
| `/organizations/` | GET | Lister organisations | ✅ | read |
| `/organizations/` | POST | Créer organisation | ✅ | admin |
| `/organizations/{id}/` | PUT | Modifier organisation | ✅ | admin |
| `/organizations/{id}/members/` | GET | Lister membres | ✅ | admin |
| `/organizations/{id}/transfer/` | POST | Transférer propriété | ✅ | owner |

---

## 🧪 Exemples d'Utilisation

### JavaScript Client

```javascript
class AuthAPI {
    constructor(baseURL) {
        this.baseURL = baseURL;
        this.accessToken = null;
        this.refreshToken = null;
    }

    async login(email, password) {
        const response = await fetch(`${this.baseURL}/api/v1/foundation/auth/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        this.accessToken = data.access;
        this.refreshToken = data.refresh;
        
        // Stocker dans localStorage
        localStorage.setItem('accessToken', this.accessToken);
        localStorage.setItem('refreshToken', this.refreshToken);
        
        return data;
    }

    async refreshAccessToken() {
        const response = await fetch(`${this.baseURL}/api/v1/foundation/auth/refresh/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh: this.refreshToken })
        });
        
        const data = await response.json();
        this.accessToken = data.access;
        localStorage.setItem('accessToken', this.accessToken);
        
        return data;
    }

    async makeAuthenticatedRequest(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Authorization': `Bearer ${this.accessToken}`,
                'Content-Type': 'application/json'
            }
        };

        let response = await fetch(url, { ...defaultOptions, ...options });

        // Si token expiré, essayer de rafraîchir
        if (response.status === 401) {
            await this.refreshAccessToken();
            defaultOptions.headers['Authorization'] = `Bearer ${this.accessToken}`;
            response = await fetch(url, { ...defaultOptions, ...options });
        }

        return response;
    }
}

// Utilisation
const auth = new AuthAPI('https://api.nocode-platform.com');

// Connexion
await auth.login('user@company.com', 'password123');

// Requête authentifiée
const projects = await auth.makeAuthenticatedRequest('/api/v1/studio/projects/');
```

---

## 🚨 Gestion des Erreurs

### Codes d'Erreur Auth

| Code | Message | Cause |
|------|---------|-------|
| `AUTH_001` | "Identifiants invalides" | Email/mot de passe incorrect |
| `AUTH_002` | "Token expiré" | Access token périmé |
| `AUTH_003` | "Token invalide" | Token malformé ou blacklisté |
| `AUTH_004` | "Permission refusée" | Droits insuffisants |
| `AUTH_005` | "Compte désactivé" | Utilisateur inactif |
| `AUTH_006` | "Email déjà utilisé" | Doublon lors inscription |

---

## 🔗 Ressources Additionnelles

- **Documentation API** : `/docs/FOUNDATION_API.md`
- **Configuration JWT** : Django settings SIMPLE_JWT
- **Guide de déploiement** : `/docs/DOCKER_DEPLOYMENT.md`
- **Support** : Créer une issue sur GitHub

---

**🔐 Le système d'authentification NoCode Backend est conçu pour être sécurisé, scalable et facile à intégrer dans des applications frontend modernes.**
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyX3V1aWQiLCJpYXQiOjE2MDk0NTkyMDAsImV4cCI6MTYwOTQ2MjgwMH0.signature
Content-Type: application/json
```

**Durée de vie :**
- **Access Token** : 15 minutes
- **Refresh Token** : 7 jours

### 3. Refresh - Renouvellement du Access Token

**Endpoint :** `POST /api/v1/foundation/auth/refresh/`

**Requête :**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyX3V1aWQiLCJpYXQiOjE2MDk0NTkyMDAsImV4cCI6MTYxMjA1MTIwMH0.signature"
}
```

**Réponse (200) :**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyX3V1aWQiLCJpYXQiOjE2MDk0NjAwMDAsImV4cCI6MTYwOTQ2MzYwMH0.signature"
}
```

### 4. Logout - Révocation du Refresh Token

**Endpoint :** `POST /api/v1/foundation/auth/logout/`

**Requête :**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyX3V1aWQiLCJpYXQiOjE2MDk0NTkyMDAsImV4cCI6MTYxMjA1MTIwMH0.signature"
}
```

**Réponse (200) :**
```json
{
  "message": "Successfully logged out"
}
```

---

## 👥 Rôles et Permissions

### Types de Rôles

#### 1. **Client** (Utilisateur externe)
- **Description** : Utilisateur n'appartenant à aucune organisation
- **Cas d'usage** : Client final, API public, consultation seule
- **Permissions par défaut** : Lecture limitée

#### 2. **Owner** (Propriétaire)
- **Description** : Propriétaire de l'organisation
- **Cas d'usage** : Administrateur système, gestion complète
- **Permissions par défaut** : Tous les droits

#### 3. **Member** (Membre)
- **Description** : Employé ou collaborateur dans une organisation
- **Cas d'usage** : Développeur, analyste, utilisateur avancé
- **Permissions par défaut** : Droits personnalisés

### Matrix de Permissions

| Action | Client | Member | Owner |
|--------|--------|--------|-------|
| **Voir les projets** | ✅ (publics) | ✅ (org) | ✅ (tous) |
| **Créer un projet** | ❌ | ✅ (si autorisé) | ✅ |
| **Modifier un projet** | ❌ | ✅ (si autorisé) | ✅ |
| **Supprimer un projet** | ❌ | ❌ | ✅ |
| **Créer des tables** | ❌ | ✅ (si autorisé) | ✅ |
| **Modifier les schémas** | ❌ | ✅ (si autorisé) | ✅ |
| **CRUD sur données** | ✅ (public) | ✅ (org) | ✅ (tous) |
| **Gérer les membres** | ❌ | ❌ | ✅ |
| **Voir les analytics** | ❌ | ✅ (si autorisé) | ✅ |
| **Exporter les données** | ❌ | ✅ (si autorisé) | ✅ |
| **Gérer les tâches** | ❌ | ✅ (si autorisé) | ✅ |

---

## 🏗️ Architecture Multi-Tenant

### Isolation des Données

Chaque projet dispose de tables préfixées :
```sql
-- Projet A (uuid: 123e4567-e89b-12d3-a456-426614174000)
project_123e4567_products
project_123e4567_customers
project_123e4567_orders

-- Projet B (uuid: 987e6543-e21b-45d6-b789-123456789abc)  
project_987e6543_products
project_987e6543_clients
project_987e6543_invoices
```

### Validation des Permissions

**Middleware de permission :**
```python
class ProjectPermissionMiddleware:
    def process_request(self, request):
        # Extraire le token JWT
        token = self.extract_token(request)
        
        # Valider le token et obtenir l'utilisateur
        user = self.validate_token(token)
        
        # Vérifier les permissions sur le projet
        project_id = request.get('project_id')
        if not self.has_project_access(user, project_id):
            raise PermissionDenied("Access denied to this project")
```

**Exemples de validation :**

#### Accès aux données d'un projet
```python
# GET /api/v1/runtime/projects/{project_id}/tables/{table}/
# Vérifie que l'utilisateur a accès à ce projet spécifique

# POST /api/v1/runtime/projects/{project_id}/tables/{table}/
# Vérifie que l'utilisateur a les droits d'écriture

# PUT /api/v1/runtime/projects/{project_id}/tables/{table}/{id}/
# Vérifie que l'utilisateur a les droits de modification
```

#### Gestion des schémas
```python
# POST /api/v1/studio/projects/{project_id}/schemas/
# Uniquement Owner ou Member avec permissions 'admin'

# DELETE /api/v1/studio/projects/{project_id}/schemas/{schema_id}/
# Uniquement Owner
```

---

## 📋 Scénarios d'Utilisation

### Scénario 1 : Client consulte un catalogue public

**Flow :**
```
1. Client accède à /api/v1/runtime/projects/{public_project_id}/tables/products/
2. Middleware vérifie que le projet est public
3. Retourne les données produits (lecture seule)
```

**Permissions requises :** Aucune (projet public)

**Endpoints accessibles :**
- `GET /api/v1/runtime/projects/{id}/tables/{table}/`
- `GET /api/v1/runtime/projects/{id}/tables/{table}/{pk}/`

---

### Scénario 2 : Member gère les données de son organisation

**Flow :**
```
1. Member se connecte avec email/password
2. Reçoit token JWT avec rôle 'member' et permissions ['read', 'write']
3. Accède aux projets de son organisation
4. Peut CRUD sur les données (pas sur les schémas)
```

**Permissions requises :** `read`, `write`

**Endpoints accessibles :**
- `GET /api/v1/runtime/projects/{id}/tables/{table}/`
- `POST /api/v1/runtime/projects/{id}/tables/{table}/`
- `PUT /api/v1/runtime/projects/{id}/tables/{table}/{pk}/`
- `DELETE /api/v1/runtime/projects/{id}/tables/{table}/{pk}/`

**Endpoints refusés :**
- `POST /api/v1/studio/projects/{id}/schemas/`
- `PUT /api/v1/studio/projects/{id}/schemas/{schema_id}/`
- `DELETE /api/v1/studio/projects/{id}/schemas/{schema_id}/`

---

### Scénario 3 : Owner gère complètement son organisation

**Flow :**
```
1. Owner se connecte
2. Reçoit token JWT avec rôle 'owner' et permissions ['read', 'write', 'admin', 'delete']
3. Accès complet à tous les endpoints
4. Peut gérer les membres, schémas, et données
```

**Permissions requises :** `read`, `write`, `admin`, `delete`

**Tous les endpoints accessibles :**
- Foundation : Auth, organisations, membres
- Studio : Création/modification/suppression schémas
- Runtime : CRUD complet sur toutes les données
- Automation : Gestion des tâches
- Insights : Analytics et rapports

---

### Scénario 4 : Super Admin (multi-organisations)

**Flow :**
```
1. Super Admin se connecte
2. Peut basculer entre organisations
3. Droits d'administration sur toutes les organisations
4. Accès aux analytics globaux
```

**Permissions spéciales :**
- `super_admin` : Accès à toutes les organisations
- `system_monitoring` : Accès aux métriques système
- `user_management` : Gestion de tous les utilisateurs

---

## 🔒 Sécurité et Bonnes Pratiques

### Validation des Tokens

**Structure du JWT Payload :**
```json
{
  "sub": "user-uuid",
  "iat": 1609459200,
  "exp": 1609462800,
  "organization": "org-uuid",
  "role": "owner",
  "permissions": ["read", "write", "admin", "delete"],
  "jti": "token-uuid"
}
```

**Vérifications effectuées :**
1. **Signature** : Validité de la clé secrète
2. **Expiration** : Token non expiré
3. **Utilisateur** : Utilisateur actif et non banni
4. **Organisation** : Organisation valide et active
5. **Permissions** : Permissions à jour pour le rôle

### Rate Limiting

**Limites par utilisateur :**
- **Login** : 5 tentatives / 15 minutes
- **API** : 1000 requêtes / heure / utilisateur
- **Refresh** : 10 rafraîchissements / heure

**Limites par IP :**
- **Login** : 20 tentatives / heure
- **API** : 5000 requêtes / heure

### Gestion des Sessions

**Blacklist des tokens :**
```python
# Logout ajoute le refresh token à la blacklist
BLACKLISTED_REFRESH_TOKENS.add(refresh_token_jti)

# Vérification blacklist à chaque refresh
if refresh_token_jti in BLACKLISTED_REFRESH_TOKENS:
    raise InvalidToken("Token has been revoked")
```

**Rotation des tokens :**
```python
# Nouveau refresh token à chaque utilisation
def refresh_token(old_refresh_token):
    blacklist_token(old_refresh_token)
    return generate_new_refresh_token(user)
```

---

## 🛡️ Protection des Endpoints

### Configuration des Permissions

**Dans `views.py` :**
```python
from rest_framework.permissions import IsAuthenticated
from .permissions import IsProjectOwner, IsProjectMember

class ProjectDataViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsProjectMember]
    
    def get_queryset(self):
        # Filtrer automatiquement par projet utilisateur
        project_id = self.kwargs['project_id']
        return self.get_project_data(project_id)

class ProjectSchemaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsProjectOwner]
    
    def destroy(self, request, *args, **kwargs):
        # Suppression uniquement par Owner
        return super().destroy(request, *args, **kwargs)
```

### Permissions personnalisées

**`permissions.py` :**
```python
class IsProjectOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.organization.owner == request.user

class IsProjectMember(BasePermission):
    def has_permission(self, request, view):
        project_id = view.kwargs.get('project_id')
        return request.user.has_project_access(project_id)
```

---

## 📊 Exemples d'Intégration

### Frontend React

**Contexte d'authentification :**
```jsx
// AuthContext.js
const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);

  const login = async (email, password) => {
    const response = await fetch('/api/v1/foundation/auth/login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    const data = await response.json();
    setToken(data.access);
    setUser(data.user);
    localStorage.setItem('refreshToken', data.refresh);
  };

  const logout = async () => {
    const refreshToken = localStorage.getItem('refreshToken');
    await fetch('/api/v1/foundation/auth/logout/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refreshToken })
    });
    
    setToken(null);
    setUser(null);
    localStorage.removeItem('refreshToken');
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
```

**Hook d'API :**
```jsx
// useApi.js
const useApi = () => {
  const { token } = useContext(AuthContext);

  const apiCall = async (url, options = {}) => {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers
      }
    });

    if (response.status === 401) {
      // Token expiré, tentative de refresh
      await refreshToken();
      // Réessayer avec nouveau token
      return apiCall(url, options);
    }

    return response.json();
  };

  return { apiCall };
};
```

### Python Client

**Classe d'authentification :**
```python
# nocode_client.py
import requests
import jwt
from datetime import datetime

class NoCodeClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
    
    def login(self, email, password):
        response = requests.post(f"{self.base_url}/api/v1/foundation/auth/login/", 
                               json={"email": email, "password": password})
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access']
            self.refresh_token = data['refresh']
            return data
        else:
            raise Exception("Login failed")
    
    def _refresh_token(self):
        response = requests.post(f"{self.base_url}/api/v1/foundation/auth/refresh/",
                               json={"refresh": self.refresh_token})
        
        if response.status_code == 200:
            self.access_token = response.json()['access']
        else:
            raise Exception("Token refresh failed")
    
    def _make_request(self, method, endpoint, **kwargs):
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {self.access_token}'
        kwargs['headers'] = headers
        
        response = requests.request(method, f"{self.base_url}{endpoint}", **kwargs)
        
        if response.status_code == 401:
            self._refresh_token()
            headers['Authorization'] = f'Bearer {self.access_token}'
            response = requests.request(method, f"{self.base_url}{endpoint}", **kwargs)
        
        return response
    
    def get_project_data(self, project_id, table_name):
        return self._make_request('GET', 
                                f'/api/v1/runtime/projects/{project_id}/tables/{table_name}/')
    
    def create_record(self, project_id, table_name, data):
        return self._make_request('POST',
                                f'/api/v1/runtime/projects/{project_id}/tables/{table_name}/',
                                json=data)

# Utilisation
client = NoCodeClient('https://api.nocode-platform.com')
client.login('user@company.com', 'password')
data = client.get_project_data('project-uuid', 'products')
```

---

## 🚨 Gestion des Erreurs

### Codes d'Erreur Authentification

| Code | Message | Cause | Solution |
|------|---------|-------|----------|
| `401` | "Authentication credentials were not provided" | Token manquant | Ajouter header Authorization |
| `401` | "Token is invalid or expired" | Token invalide/expiré | Rafraîchir le token |
| `401` | "Token has been revoked" | Token blacklisté | Se reconnecter |
| `403` | "You do not have permission to perform this action" | Permissions insuffisantes | Vérifier rôle utilisateur |
| `403` | "Access denied to this project" | Pas accès au projet | Demander accès à l'owner |
| `429` | "Rate limit exceeded" | Trop de requêtes | Attendre et réessayer |

### Flow de Gestion d'Erreur

**Frontend :**
```jsx
const apiCall = async () => {
  try {
    const response = await fetch(url, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.status === 401) {
      // Tentative de refresh
      const newToken = await refreshToken();
      // Réessayer avec nouveau token
      return fetch(url, { headers: { 'Authorization': `Bearer ${newToken}` }});
    }
    
    if (response.status === 403) {
      // Rediriger vers page d'erreur permissions
      window.location.href = '/unauthorized';
    }
    
    return response.json();
  } catch (error) {
    console.error('API Error:', error);
    // Afficher message d'erreur utilisateur
  }
};
```

---

## 📈 Monitoring et Audit

### Logs d'Authentification

**Événements tracés :**
```python
# Login réussi
logger.info(f"User login successful", extra={
    'user_id': user.id,
    'email': user.email,
    'ip_address': request.META.get('REMOTE_ADDR'),
    'user_agent': request.META.get('HTTP_USER_AGENT'),
    'timestamp': timezone.now()
});

# Échec login
logger.warning(f"User login failed", extra={
    'email': email,
    'ip_address': request.META.get('REMOTE_ADDR'),
    'reason': 'invalid_password',
    'timestamp': timezone.now()
});

# Permission refusée
logger.warning(f"Access denied", extra={
    'user_id': request.user.id,
    'resource': request.path,
    'action': 'delete',
    'project_id': project_id,
    'timestamp': timezone.now()
});
```

### Métriques de Sécurité

**Indicateurs monitorés :**
- **Tentatives de login par IP** : Détection d'attaques
- **Tokens refresh anormaux** : Utilisation suspecte
- **Accès refusés par projet** : Tentatives d'intrusion
- **Connexions simultanées** : Compte partagé suspect
- **Géolocalisation anormale** : Connexion depuis pays inhabituel

---

## 🔮 Évolutions Futures

### Features en développement

1. **SSO Integration** : SAML, OAuth2, LDAP
2. **2FA** : Authentification à deux facteurs
3. **RBAC Avancé** : Permissions granulaires par ressource
4. **Audit Trail** : Historique complet des actions
5. **Session Management** : Gestion des sessions actives

### Extensions de sécurité

1. **IP Whitelisting** : Restriction d'accès par IP
2. **Device Fingerprinting** : Reconnaissance des appareils
3. **Behavioral Analysis** : Détection d'anomalies
4. **Zero Trust Architecture** : Validation systématique

---

*Documentation Authentication & Rôles - Version 1.0*
