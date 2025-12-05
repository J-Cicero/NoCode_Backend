# 📚 NoCode Backend - Documentation API Complète

## 🎯 Vue d'ensemble

L'API NoCode Backend est organisée en 5 modules principaux :
- **Foundation** : Authentification et gestion des organisations
- **Studio** : Création et gestion des schémas de données
- **Runtime** : CRUD dynamique sur les tables créées
- **Automation** : Gestion des tâches planifiées
- **Insights** : Analytics et métriques d'utilisation

---

## 🔐 **FOUNDATION - Authentification & Organisation**

### POST `/api/v1/foundation/auth/login/`
**Authentification JWT**

**Requête :**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Réponse (200) :**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "organizations": [
    {
      "id": "uuid",
      "name": "My Company",
      "role": "owner"
    }
  ],
  "permissions": ["read", "write", "admin"]
}
```

**Erreurs :**
- `400` : Champs manquants ou invalides
- `401` : Identifiants incorrects
- `403` : Compte désactivé

---

### POST `/api/v1/foundation/auth/refresh/`
**Rafraîchissement du token JWT**

**Requête :**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Réponse (200) :**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

### GET `/api/v1/foundation/organizations/`
**Lister les organisations de l'utilisateur**

**Headers :**
```
Authorization: Bearer <access_token>
```

**Réponse (200) :**
```json
{
  "count": 1,
  "results": [
    {
      "id": "uuid",
      "name": "My Company",
      "description": "Description de l'organisation",
      "created_at": "2024-01-01T00:00:00Z",
      "role": "owner",
      "member_count": 5
    }
  ]
}
```

---

## 🎨 **STUDIO - Gestion des Schémas**

### GET `/api/v1/studio/projects/{id}/schemas/`
**Lister les schémas d'un projet**

**Réponse (200) :**
```json
{
  "project": {
    "id": "uuid",
    "name": "My Project",
    "schema_name": "my_project"
  },
  "schemas": [
    {
      "id": "uuid",
      "table_name": "products",
      "display_name": "Produits",
      "icon": "🛒",
      "description": "Catalogue des produits",
      "field_count": 8,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

### POST `/api/v1/studio/projects/{id}/schemas/`
**Créer un nouveau schéma de table**

**Requête :**
```json
{
  "table_name": "customers",
  "display_name": "Clients",
  "icon": "👥",
  "description": "Base de données clients",
  "fields": [
    {
      "name": "first_name",
      "display_name": "Prénom",
      "field_type": "TEXT_SHORT",
      "is_required": true,
      "validation": {
        "min_length": 2,
        "max_length": 50
      }
    },
    {
      "name": "email",
      "display_name": "Email",
      "field_type": "EMAIL",
      "is_required": true,
      "is_unique": true,
      "validation": {}
    },
    {
      "name": "birth_date",
      "display_name": "Date de naissance",
      "field_type": "DATE",
      "is_required": false,
      "validation": {}
    }
  ]
}
```

**Réponse (201) :**
```json
{
  "id": "uuid",
  "table_name": "customers",
  "display_name": "Clients",
  "icon": "👥",
  "description": "Base de données clients",
  "field_count": 3,
  "created_at": "2024-01-01T00:00:00Z",
  "fields": [
    {
      "name": "first_name",
      "display_name": "Prénom",
      "field_type": "TEXT_SHORT",
      "is_required": true,
      "validation": {"min_length": 2, "max_length": 50}
    },
    {
      "name": "email",
      "display_name": "Email",
      "field_type": "EMAIL",
      "is_required": true,
      "is_unique": true,
      "validation": {}
    },
    {
      "name": "birth_date",
      "display_name": "Date de naissance",
      "field_type": "DATE",
      "is_required": false,
      "validation": {}
    }
  ]
}
```

---

## ⚡ **RUNTIME - CRUD Dynamique**

### GET `/api/v1/runtime/projects/{id}/tables/{table}/`
**Lister les enregistrements d'une table**

**Paramètres :**
- `page` (optional) : Numéro de page (défaut: 1)
- `page_size` (optional) : Taille de page (défaut: 20)
- `search` (optional) : Recherche textuelle
- `ordering` (optional) : Champ de tri (ex: `-created_at`)

**Réponse (200) :**
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/v1/runtime/projects/uuid/tables/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "iPhone 15 Pro",
      "price": "1199.99",
      "description": "Dernier modèle iPhone",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

### POST `/api/v1/runtime/projects/{id}/tables/{table}/`
**Créer un nouvel enregistrement**

**Requête (exemple pour table "products") :**
```json
{
  "name": "MacBook Pro M3",
  "price": "2499.99",
  "description": "Ordinateur portable puissant",
  "category": "electronics",
  "in_stock": true,
  "quantity": 25
}
```

**Réponse (201) :**
```json
{
  "id": 2,
  "name": "MacBook Pro M3",
  "price": "2499.99",
  "description": "Ordinateur portable puissant",
  "category": "electronics",
  "in_stock": true,
  "quantity": 25,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

---

### GET `/api/v1/runtime/projects/{id}/tables/{table}/{pk}/`
**Détails d'un enregistrement**

**Réponse (200) :**
```json
{
  "id": 1,
  "name": "iPhone 15 Pro",
  "price": "1199.99",
  "description": "Dernier modèle iPhone",
  "category": "electronics",
  "in_stock": true,
  "quantity": 50,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

---

### PUT `/api/v1/runtime/projects/{id}/tables/{table}/{pk}/`
**Mettre à jour un enregistrement**

**Requête :**
```json
{
  "name": "iPhone 15 Pro Max",
  "price": "1299.99",
  "description": "Version mise à jour",
  "quantity": 45
}
```

**Réponse (200) :**
```json
{
  "id": 1,
  "name": "iPhone 15 Pro Max",
  "price": "1299.99",
  "description": "Version mise à jour",
  "category": "electronics",
  "in_stock": true,
  "quantity": 45,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-02T00:00:00Z"
}
```

---

### DELETE `/api/v1/runtime/projects/{id}/tables/{table}/{pk}/`
**Supprimer un enregistrement**

**Réponse (204) :** Aucun contenu

---

## 🤖 **AUTOMATION - Tâches Planifiées**

### GET `/api/v1/automation/projects/{id}/tasks/`
**Lister les tâches automatisées**

**Réponse (200) :**
```json
{
  "count": 2,
  "results": [
    {
      "id": "uuid",
      "name": "Backup quotidien",
      "task_type": "backup",
      "schedule": "0 2 * * *",
      "is_active": true,
      "last_run": "2024-01-01T02:00:00Z",
      "next_run": "2024-01-02T02:00:00Z"
    }
  ]
}
```

---

### POST `/api/v1/automation/projects/{id}/tasks/`
**Créer une tâche automatisée**

**Requête :**
```json
{
  "name": "Rapport hebdomadaire",
  "task_type": "report",
  "schedule": "0 9 * * 1",
  "config": {
    "recipients": ["admin@example.com"],
    "format": "pdf"
  },
  "is_active": true
}
```

---

## 📊 **INSIGHTS - Analytics**

### GET `/api/v1/insights/projects/{id}/metrics/`
**Métriques du projet**

**Réponse (200) :**
```json
{
  "project_id": "uuid",
  "period": "30d",
  "metrics": {
    "total_records": 1250,
    "total_tables": 8,
    "api_calls": 15420,
    "active_users": 25,
    "storage_used": "125.5 MB"
  },
  "tables_breakdown": [
    {
      "table_name": "products",
      "record_count": 450,
      "last_activity": "2024-01-01T15:30:00Z"
    }
  ]
}
```

---

## 🔧 **Types de Champs Disponibles**

| Type | Description | Validation |
|------|-------------|------------|
| `TEXT_SHORT` | Texte court (max 255 chars) | min_length, max_length |
| `TEXT_LONG` | Texte long | min_length, max_length |
| `EMAIL` | Email | format email |
| `NUMBER` | Nombre entier | min_value, max_value |
| `DECIMAL` | Nombre décimal | min_value, max_value |
| `DATE` | Date | format date |
| `DATETIME` | Date + heure | format datetime |
| `BOOLEAN` | Vrai/Faux | - |
| `CHOICE` | Choix unique | choices |
| `MULTIPLE_CHOICE` | Choix multiples | choices |
| `FILE` | Fichier upload | file_types, max_size |
| `IMAGE` | Image upload | file_types, max_size |

---

## 🚨 **Codes d'Erreur Standards**

| Code | Signification | Description |
|------|---------------|-------------|
| `200` | OK | Requête réussie |
| `201` | Created | Ressource créée |
| `204` | No Content | Ressource supprimée |
| `400` | Bad Request | Requête invalide |
| `401` | Unauthorized | Non authentifié |
| `403` | Forbidden | Permissions insuffisantes |
| `404` | Not Found | Ressource introuvable |
| `409` | Conflict | Conflit de données |
| `422` | Unprocessable Entity | Validation échouée |
| `500` | Internal Error | Erreur serveur |

---

## 📝 **Exemples cURL**

### Authentification
```bash
curl -X POST http://localhost:8000/api/v1/foundation/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```

### Créer une table
```bash
curl -X POST http://localhost:8000/api/v1/studio/projects/uuid/schemas/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"table_name":"tasks","display_name":"Tâches","icon":"📋","fields":[...]}'
```

### CRUD sur enregistrements
```bash
# Lister
curl -X GET "http://localhost:8000/api/v1/runtime/projects/uuid/tables/tasks/" \
  -H "Authorization: Bearer <access_token>"

# Créer
curl -X POST http://localhost:8000/api/v1/runtime/projects/uuid/tables/tasks/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Nouvelle tâche","description":"Description","priority":"high"}'

# Mettre à jour
curl -X PUT http://localhost:8000/api/v1/runtime/projects/uuid/tables/tasks/1/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Tâche mise à jour","status":"completed"}'

# Supprimer
curl -X DELETE http://localhost:8000/api/v1/runtime/projects/uuid/tables/tasks/1/ \
  -H "Authorization: Bearer <access_token>"
```

---

## 🌐 **Documentation Interactive**

- **Swagger UI** : http://localhost:8000/api/docs/
- **ReDoc** : http://localhost:8000/api/redoc/
- **OpenAPI Schema** : http://localhost:8000/api/schema/

---

*Documentation générée automatiquement - Version 1.0*
