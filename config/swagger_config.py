"""
Configuration centralisée pour Swagger/OpenAPI
Améliore automatiquement la documentation sans modifier les vues
"""

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema_view, extend_schema
from drf_spectacular.extensions import OpenApiViewExtension


# Configuration globale Swagger
SWAGGER_SETTINGS = {
    'TITLE': 'NoCode Backend Platform API',
    'DESCRIPTION': """
# 🚀 NoCode Backend Platform - API Documentation

Bienvenue dans la documentation complète de la plateforme NoCode Backend !

## 📖 Vue d'ensemble

Cette plateforme permet de **créer des applications web sans code** en combinant :
- **Studio** : Éditeur visuel pour créer des projets, tables, pages et composants
- **Automation** : Workflows automatisés avec éditeur Node/Edge
- **Runtime** : Génération et déploiement automatique d'applications Django
- **Foundation** : Authentification, organisations, utilisateurs, facturation

## 🔐 Authentification

### Comment s'authentifier ?

Toutes les requêtes (sauf login/register) nécessitent un **JWT Token** :

```javascript
// 1. Se connecter
const response = await fetch('/api/v1/auth/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        email: 'user@example.com',
        password: 'password123'
    })
});

const data = await response.json();
const accessToken = data.tokens.access;

// 2. Utiliser le token dans les requêtes
fetch('/api/v1/projects/', {
    headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
    }
});
```

### Renouvellement du token

Les access tokens expirent après 15 minutes. Utilisez le refresh token :

```javascript
const refreshResponse = await fetch('/api/v1/auth/token/refresh/', {
    method: 'POST',
    body: JSON.stringify({ refresh: refreshToken })
});

const newAccessToken = refreshResponse.data.access;
```

## 🎯 Workflow complet

### 1. Créer un projet NoCode

```javascript
const project = await fetch('/api/v1/studio/projects/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        name: 'Mon Application CRM',
        description: 'Gestion de la relation client'
    })
}).then(r => r.json());
```

### 2. Créer des tables (modèles de données)

```javascript
const table = await fetch(`/api/v1/studio/projects/${project.id}/schemas/`, {
    method: 'POST',
    body: JSON.stringify({
        table_name: 'clients',
        display_name: 'Clients',
        fields_config: [
            { name: 'nom', type: 'string', required: true },
            { name: 'email', type: 'email', required: true, unique: true },
            { name: 'telephone', type: 'string' }
        ]
    })
}).then(r => r.json());
```

### 3. Créer des pages (interface)

```javascript
const page = await fetch(`/api/v1/studio/projects/${project.id}/pages/`, {
    method: 'POST',
    body: JSON.stringify({
        name: 'Liste Clients',
        route: '/clients'
    })
}).then(r => r.json());
```

### 4. Créer un workflow d'automatisation

```javascript
// Créer le workflow
const workflow = await fetch('/api/v1/automation/workflows/', {
    method: 'POST',
    body: JSON.stringify({
        name: 'Notification nouveau client',
        project_id: project.id
    })
}).then(r => r.json());

// Ajouter un trigger
const trigger = await fetch(`/api/v1/automation/workflows/${workflow.id}/nodes/`, {
    method: 'POST',
    body: JSON.stringify({
        node_type: 'trigger',
        label: 'Nouveau client créé',
        position_x: 100,
        position_y: 100,
        config: { event_type: 'client.created' }
    })
}).then(r => r.json());

// Ajouter une action email
const emailAction = await fetch(`/api/v1/automation/workflows/${workflow.id}/nodes/`, {
    method: 'POST',
    body: JSON.stringify({
        node_type: 'email',
        label: 'Envoyer email bienvenue',
        position_x: 300,
        position_y: 100,
        config: {
            to: '{{client.email}}',
            subject: 'Bienvenue',
            template: 'welcome'
        }
    })
}).then(r => r.json());

// Connecter les nodes
await fetch(`/api/v1/automation/workflows/${workflow.id}/edges/`, {
    method: 'POST',
    body: JSON.stringify({
        source_node_id: trigger.id,
        target_node_id: emailAction.id
    })
});

// Activer le workflow
await fetch(`/api/v1/automation/workflows/${workflow.id}/activate/`, {
    method: 'POST'
});
```

### 5. Générer et déployer l'application

```javascript
// Créer l'application générée
const app = await fetch('/api/v1/runtime/apps/', {
    method: 'POST',
    body: JSON.stringify({
        project_id: project.id,
        name: 'CRM App',
        deployment_target: 'docker'
    })
}).then(r => r.json());

// Déployer dans Docker
const deployment = await fetch(`/api/v1/runtime/apps/${app.id}/deploy/`, {
    method: 'POST'
}).then(r => r.json());

console.log('Application déployée :', deployment.urls.api);
// http://localhost:8456/api/v1/
```

## 📊 Codes de statut HTTP

- **200 OK** : Requête réussie
- **201 Created** : Ressource créée
- **204 No Content** : Suppression réussie
- **400 Bad Request** : Données invalides
- **401 Unauthorized** : Token manquant ou expiré
- **403 Forbidden** : Permissions insuffisantes
- **404 Not Found** : Ressource introuvable
- **500 Internal Server Error** : Erreur serveur

## 🔍 Filtres et Pagination

La plupart des endpoints de listing supportent :

```javascript
// Pagination
GET /api/v1/projects/?page=2&page_size=20

// Recherche
GET /api/v1/projects/?search=CRM

// Filtres
GET /api/v1/projects/?status=active&created_by=user_id

// Tri
GET /api/v1/projects/?ordering=-created_at
```

## 💡 Bonnes pratiques

### Gestion des erreurs

```javascript
const handleRequest = async (url, options) => {
    try {
        const response = await fetch(url, options);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || error.message);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Erreur API:', error);
        throw error;
    }
};
```

### Refresh automatique du token

```javascript
// Intercepteur fetch
const originalFetch = window.fetch;
window.fetch = async (...args) => {
    let response = await originalFetch(...args);
    
    if (response.status === 401) {
        // Token expiré, renouveler
        const refreshToken = localStorage.getItem('refresh_token');
        const refreshResponse = await originalFetch('/api/v1/auth/token/refresh/', {
            method: 'POST',
            body: JSON.stringify({ refresh: refreshToken })
        });
        
        const { access } = await refreshResponse.json();
        localStorage.setItem('access_token', access);
        
        // Rejouer la requête originale
        const [url, options] = args;
        options.headers['Authorization'] = `Bearer ${access}`;
        response = await originalFetch(url, options);
    }
    
    return response;
};
```

## 📚 Modules disponibles

### 🔐 Foundation
- Authentification (login, register, tokens)
- Gestion des organisations
- Gestion des utilisateurs
- Facturation et abonnements

### 📁 Studio
- Projets NoCode
- Tables (DataSchema)
- Pages et composants
- Éditeur drag & drop

### ⚡ Automation
- Workflows visuels
- Nodes et Edges (système de graphe)
- Intégrations externes
- Historique des exécutions

### 🚀 Runtime
- Génération automatique d'applications
- Déploiement Docker
- Gestion des conteneurs
- Logs et monitoring

### 📊 Insights
- Analytics et métriques
- Activités utilisateurs
- Performances
- Rapports

## 🆘 Support

Pour toute question :
- 📧 Email: support@nocode-platform.com
- 📖 Documentation complète: /docs/
- 🐛 Bugs: GitHub Issues
- 💬 Chat: Discord/Slack

## 🔄 Versioning

API Version: **v1**

L'API utilise le versioning dans l'URL : `/api/v1/`

Les changements majeurs seront versionnés : `/api/v2/`, etc.
    """,
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'TAGS': [
        {'name': '🔐 Authentification', 'description': 'Connexion, inscription, gestion des tokens JWT'},
        {'name': '🏢 Organisations', 'description': 'Gestion multi-tenant des organisations'},
        {'name': '👥 Utilisateurs', 'description': 'Profils et gestion des utilisateurs'},
        {'name': '💳 Abonnements', 'description': 'Plans, facturation et paiements Stripe'},
        {'name': '📁 Studio - Projets', 'description': 'Création et gestion de projets NoCode'},
        {'name': '📊 Studio - Tables', 'description': 'Définition des modèles de données'},
        {'name': '🎨 Studio - Pages', 'description': 'Interfaces utilisateur drag & drop'},
        {'name': '🧩 Studio - Composants', 'description': 'Bibliothèque de composants visuels'},
        {'name': '⚡ Automation - Workflows', 'description': 'Workflows d\'automatisation'},
        {'name': '🔵 Automation - Nodes', 'description': 'Nœuds du graphe de workflow'},
        {'name': '🔗 Automation - Edges', 'description': 'Connexions entre nodes'},
        {'name': '🔌 Automation - Intégrations', 'description': 'Services externes (SendGrid, Stripe, etc.)'},
        {'name': '📊 Automation - Exécutions', 'description': 'Historique et logs des exécutions'},
        {'name': '🚀 Runtime - Applications', 'description': 'Applications générées et déployées'},
        {'name': '📊 Insights - Analytics', 'description': 'Métriques et statistiques'},
    ],
    'CONTACT': {
        'name': 'NoCode Platform Support',
        'email': 'support@nocode-platform.com',
        'url': 'https://nocode-platform.com/support'
    },
    'LICENSE': {
        'name': 'Proprietary',
        'url': 'https://nocode-platform.com/license'
    },
    'EXTERNAL_DOCS': {
        'description': 'Documentation complète',
        'url': 'https://docs.nocode-platform.com'
    },
    'SERVERS': [
        {
            'url': 'http://localhost:8000',
            'description': 'Serveur de développement'
        },
        {
            'url': 'https://staging-api.nocode-platform.com',
            'description': 'Environnement de staging'
        },
        {
            'url': 'https://api.nocode-platform.com',
            'description': 'Production'
        }
    ],
    'SECURITY': [
        {
            'BearerAuth': []
        }
    ],
    'COMPONENT_SPLIT_REQUEST': True,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'filter': True,
        'tryItOutEnabled': True,
        'syntaxHighlight.theme': 'monokai',
    },
}


def get_schema_description(view_name):
    """
    Retourne automatiquement la description d'une vue
    basée sur son nom.
    """
    descriptions = {
        # Foundation - Auth
        'RegisterOwnerView': AUTH_REGISTER_OWNER,
        'RegisterClientView': AUTH_REGISTER_CLIENT,
        'LoginView': AUTH_LOGIN,
        'LogoutView': AUTH_LOGOUT,
        'PasswordChangeView': AUTH_PASSWORD_CHANGE,
        'PasswordResetRequestView': AUTH_PASSWORD_RESET_REQUEST,
        'PasswordResetConfirmView': AUTH_PASSWORD_RESET_CONFIRM,
        'EmailVerificationView': AUTH_EMAIL_VERIFICATION,
        
        # Foundation - Organizations
        'OrganizationListCreateView': ORG_LIST_CREATE,
        
        # Studio
        'ProjectViewSet': PROJECT_LIST_CREATE,
        'DataSchemaViewSet': DATASCHEMA_LIST_CREATE,
        'PageViewSet': PAGE_LIST_CREATE,
        'ComponentViewSet': COMPONENT_LIST,
        
        # Automation
        'WorkflowViewSet': WORKFLOW_LIST_CREATE,
        'NodeViewSet': NODE_LIST_CREATE,
        'EdgeViewSet': EDGE_LIST_CREATE,
        'IntegrationViewSet': INTEGRATION_LIST_CREATE,
        'WorkflowExecutionViewSet': EXECUTION_LIST,
        
        # Runtime
        'GeneratedAppViewSet': GENERATED_APP_LIST_CREATE,
    }
    
    return descriptions.get(view_name, {})


# Import des descriptions depuis les modules
try:
    from apps.foundation.schema_descriptions import *
    from apps.studio.schema_descriptions import *
    from apps.automation.schema_descriptions import *
    from apps.runtime.schema_descriptions import *
except ImportError:
    pass
