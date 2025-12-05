# 📚 NoCode Backend - Vue d'ensemble de l'API

## 🎯 Introduction

Le NoCode Backend est une **plateforme entreprise complète** pour créer, déployer et gérer des applications web sans code. L'API est organisée en 5 modules principaux avec **80+ endpoints** couvrant tout le cycle de vie des applications.

---

## 🏗️ **Architecture des Modules**

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   FOUNDATION    │  │     STUDIO      │  │     RUNTIME     │
│                 │  │                 │  │                 │
│ • Authentification│ │ • Projets       │  │ • Applications │
│ • Utilisateurs   │ │ • Schémas       │  │ • Déploiement  │
│ • Organisations  │ │ • Pages         │  │ • CRUD dynamique│
│ • Abonnements    │ │ • Composants    │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
          │                     │                     │
          └─────────────────────┼─────────────────────┘
                                │
┌─────────────────┐  ┌─────────────────┐
│   AUTOMATION    │  │     INSIGHTS    │
│                 │  │                 │
│ • Workflows     │  │ • Analytics     │
│ • Intégrations  │  │ • Tracking      │
│ • Exécutions    │  │ • Métriques     │
│ • Graphes       │  │ • Rapports      │
└─────────────────┘  └─────────────────┘
```

---

## 📋 **Modules et Leurs Responsabilités**

### 🔐 **FOUNDATION** - Gestion des identités et organisations
**Base URL :** `/api/v1/foundation/`

**Fonctionnalités principales :**
- **Authentification JWT** avec refresh tokens
- **Gestion des utilisateurs** (CRUD, profil, recherche)
- **Organisations multi-tenant** (membres, rôles, permissions)
- **Abonnements et facturation** (plans, paiements)
- **Sécurité** (reset mot de passe, vérification email)

**Endpoints clés :**
- `POST /auth/login/` - Connexion JWT
- `POST /auth/register/client/` - Inscription client
- `GET /users/profile/` - Profil utilisateur
- `GET/POST /organizations/` - Gestion organisations
- `GET /subscriptions/` - Abonnements

**Documentation détaillée :** [FOUNDATION_API.md](FOUNDATION_API.md)

---

### 🎨 **STUDIO** - Création et conception des applications
**Base URL :** `/api/v1/studio/`

**Fonctionnalités principales :**
- **Projets NoCode** (création, gestion, publication)
- **Schémas de données** (tables, champs, validation)
- **Pages visuelles** (routing, configuration)
- **Composants UI** (drag & drop, configuration)
- **Éditeur visuel** (state management)

**Endpoints clés :**
- `GET/POST /projects/` - CRUD projets
- `GET/POST /schemas/` - CRUD schémas de données
- `GET/POST /pages/` - CRUD pages
- `GET/POST /components/` - CRUD composants
- `POST /projects/{id}/publish/` - Publier projet

**Documentation détaillée :** [STUDIO_API.md](STUDIO_API.md)

---

### ⚡ **RUNTIME** - Exécution et déploiement des applications
**Base URL :** `/api/v1/runtime/`

**Fonctionnalités principales :**
- **Applications générées** (build, déploiement, statut)
- **CRUD dynamique** sur tables utilisateur
- **Gestion des déploiements** (logs, retry, rollback)
- **Métadonnées frontend** (schémas, validation)
- **Multi-environnement** (dev, staging, prod)

**Endpoints clés :**
- `GET/POST /apps/` - CRUD applications
- `POST /apps/{id}/deploy/` - Déployer application
- `GET /projects/{id}/tables/{table}/` - CRUD dynamique
- `GET /projects/{id}/schema/` - Schéma projet
- `GET /deployment-logs/` - Logs déploiement

**Documentation détaillée :** [RUNTIME_API.md](RUNTIME_API.md)

---

### 🤖 **AUTOMATION** - Workflows et intégrations
**Base URL :** `/api/v1/automation/`

**Fonctionnalités principales :**
- **Workflows visuels** (création, édition, exécution)
- **Nœuds et arêtes** (logique de workflow)
- **Intégrations externes** (API, webhooks)
- **Exécutions planifiées** (CRON, déclencheurs)
- **Graphes orientés** (visualisation, debugging)

**Endpoints clés :**
- `GET/POST /workflows/` - CRUD workflows
- `GET/POST /workflows/{id}/nodes/` - Nœuds workflow
- `GET/POST /workflows/{id}/edges/` - Connexions workflow
- `GET /workflows/{id}/graph/` - Graphe complet
- `GET/POST /integrations/` - Intégrations

**Documentation détaillée :** [AUTOMATION_API.md](AUTOMATION_API.md)

---

### 📊 **INSIGHTS** - Analytics et monitoring
**Base URL :** `/api/v1/insights/`

**Fonctionnalités principales :**
- **Tracking d'événements** (user actions, system events)
- **Métriques applicatives** (performance, usage)
- **Analytics avancés** (rapports, dashboards)
- **Monitoring système** (ressources, santé)
- **Export de données** (CSV, PDF, JSON)

**Endpoints clés :**
- `POST /track/` - Tracking événement
- `GET/POST /activities/` - Activités utilisateur
- `GET /analytics/` - Rapports analytics
- `GET /performance/` - Métriques performance
- `GET /system-metrics/` - Métriques système

**Documentation détaillée :** [INSIGHTS_API.md](INSIGHTS_API.md)

---

## 🔄 **Flux Utilisateur Typique**

### 1. **Initialisation**
```
1. POST /foundation/auth/register/client/     → Inscription
2. POST /foundation/auth/login/                → Connexion JWT
3. GET  /foundation/users/profile/             → Profil utilisateur
```

### 2. **Création Projet**
```
1. POST /studio/projects/                      → Créer projet
2. POST /studio/schemas/                       → Définir schéma de données
3. POST /studio/pages/                         → Créer pages
4. POST /studio/components/                    → Ajouter composants
```

### 3. **Déploiement**
```
1. POST /studio/projects/{id}/publish/         → Publier projet
2. POST /runtime/apps/                         → Générer application
3. POST /runtime/apps/{id}/deploy/             → Déployer
4. GET  /runtime/apps/{id}/status/             → Vérifier statut
```

### 4. **Utilisation**
```
1. GET  /runtime/projects/{id}/schema/         → Schéma frontend
2. GET  /runtime/projects/{id}/tables/{table}/ → CRUD dynamique
3. POST /insights/track/                       → Tracking usage
```

### 5. **Automatisation**
```
1. POST /automation/workflows/                  → Créer workflow
2. POST /automation/workflows/{id}/nodes/      → Ajouter nœuds
3. POST /automation/workflows/{id}/edges/      → Connecter nœuds
4. POST /automation/workflows/{id}/execute/    → Exécuter
```

---

## 🔐 **Système de Permissions**

### Rôles Utilisateurs
- **CLIENT** : Utilisateur externe, accès limité
- **MEMBER** : Membre organisation, droits personnalisés
- **ADMIN** : Admin organisation, gestion complète
- **OWNER** : Propriétaire, tous les droits

### Permissions par Module
| Module | CLIENT | MEMBER | ADMIN | OWNER |
|--------|--------|--------|-------|-------|
| **Foundation** | Profil, login | Profil + org | Tout | Tout |
| **Studio** | Lecture seule | CRUD projets | CRUD + membres | Tout |
| **Runtime** | Données publiques | CRUD données | CRUD + déploiement | Tout |
| **Automation** | Aucun | Workflows basiques | Workflows avancés | Tout |
| **Insights** | Usage perso | Analytics org | Analytics complètes | Tout |

---

## 📡 **Formats Standards**

### En-têtes HTTP
```http
Authorization: Bearer <access_token>
Content-Type: application/json
Accept: application/json
```

### Réponses Standard
```json
// Succès (200/201)
{
  "id": "uuid",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  // ... données spécifiques
}

// Erreur (400/401/403/404/500)
{
  "error": "Message d'erreur",
  "details": {
    "field": "Erreur spécifique au champ"
  },
  "code": "ERROR_CODE"
}
```

### Pagination
```json
{
  "count": 150,
  "next": "http://api.example.com/endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## 🚀 **Quick Start**

### 1. Installation Docker
```bash
git clone <repository>
cd NoCode_Backend
docker-compose -f docker-compose.dev.yml up --build -d
```

### 2. Création Superutilisateur
```bash
docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

### 3. Test API
```bash
# Login
curl -X POST http://localhost:8000/api/v1/foundation/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}'

# Créer projet
curl -X POST http://localhost:8000/api/v1/studio/projects/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Mon Projet"}'
```

### 4. Documentation Interactive
- **Swagger UI** : http://localhost:8000/api/docs/
- **ReDoc** : http://localhost:8000/api/redoc/
- **OpenAPI Schema** : http://localhost:8000/api/schema/

---

## 📈 **Statistiques de la Plateforme**

### Capacités
- **Projets** : Illimités (par organisation)
- **Tables par projet** : 100 maximum
- **Champs par table** : 50 maximum  
- **Enregistrements** : Illimités (performance dépendante)
- **Workflows** : 50 par projet
- **Utilisateurs par org** : 1000 maximum

### Performance
- **Requêtes/second** : ~500 (3 workers)
- **Concurrent users** : 1000+
- **Database connections** : 20 pooling
- **Cache hit ratio** : 95%+
- **API response time** : <200ms (95th percentile)

---

## 🛠️ **Outils et SDK**

### Python Client
```python
from nocode_client import NoCodeClient

client = NoCodeClient('https://api.nocode-platform.com')
client.login('user@company.com', 'password')

# Créer projet
project = client.create_project({
    'name': 'Mon Application',
    'organization_id': 'org-uuid'
})

# CRUD dynamique
data = client.get_table_data(project.id, 'products')
product = client.create_record(project.id, 'products', {
    'name': 'iPhone 15',
    'price': 1199.99
})
```

### JavaScript Client
```javascript
import { NoCodeAPI } from '@ncode/js-client';

const api = new NoCodeAPI('https://api.nocode-platform.com');
await api.login('user@company.com', 'password');

const project = await api.projects.create({name: 'Mon App'});
const products = await api.runtime.listData(project.id, 'products');
```

---

## 📞 **Support et Aide**

### Documentation
- **Guides détaillés** : Voir fichiers module spécifiques
- **Référence API** : [Swagger UI](http://localhost:8000/api/docs/)
- **Déploiement** : [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)
- **Architecture** : [DOCKER_SERVICES.md](DOCKER_SERVICES.md)

### Communauté
- **Issues** : GitHub Repository
- **Discussions** : Discord/Slack
- **Documentation** : Wiki GitHub

### Support Entreprise
- **Email** : support@nocode-platform.com
- **SLA** : 99.9% uptime garanti
- **Support 24/7** : Plans Enterprise

---

*Vue d'ensemble de l'API NoCode Backend - Version 1.0*
