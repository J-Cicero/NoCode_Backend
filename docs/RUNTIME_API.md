# ⚡ Runtime API - Exécution et Déploiement d'Applications

## 📋 Vue d'ensemble

Le module Runtime est le **moteur d'exécution** qui transforme les projets NoCode en applications web fonctionnelles. Il gère la génération d'applications, leur déploiement, et fournit le **CRUD dynamique** sur les tables utilisateur.

**Base URL :** `/api/v1/runtime/`

---

## 🚀 **Applications Générées**

### GET `/apps/`
**Lister les applications générées de l'utilisateur**

**Headers :**
```http
Authorization: Bearer <access_token>
```

**Réponse (200) :**
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "tracking_id": "app-uuid-here",
      "project": {
        "tracking_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Gestion Client",
        "organization_name": "Tech Company"
      },
      "name": "Gestion Client App",
      "status": "deployed",
      "version": "1.2.0",
      "api_base_url": "https://api.nocode-platform.com/runtime/projects/550e8400-e29b-41d4-a716-446655440000/",
      "admin_url": "https://admin.nocode-platform.com/app-uuid-here/",
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-05T15:30:00Z",
      "deployment_info": {
        "environment": "production",
        "deployed_at": "2024-01-05T15:30:00Z",
        "health_status": "healthy",
        "uptime_percentage": 99.9
      }
    }
  ]
}
```

**Statuts possibles :**
- `draft` : En cours de création
- `generated` : Code généré, prêt déploiement
- `deployment_pending` : Déploiement en cours
- `deployed` : Déployé avec succès
- `deployment_failed` : Échec déploiement
- `error` : Erreur génération

---

### POST `/apps/`
**Créer une nouvelle application générée**

**Requête :**
```json
{
  "project": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Mon Application CRM",
  "environment": "production"
}
```

**Réponse (201) :**
```json
{
  "id": 4,
  "tracking_id": "app-uuid-new",
  "project": {
    "tracking_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Gestion Client"
  },
  "name": "Mon Application CRM",
  "status": "draft",
  "version": "1.0.0",
  "environment": "production",
  "created_at": "2024-01-20T10:00:00Z",
  "generation_task_id": "task-uuid-here",
  "estimated_generation_time": "2-3 minutes"
}
```

**Processus de génération :**
1. Validation du projet source
2. Génération des modèles Django
3. Création des serializers dynamiques
4. Génération des endpoints REST
5. Configuration des permissions
6. Création des tables SQL
7. Déploiement de l'application

---

### GET `/apps/{app_id}/`
**Détails d'une application spécifique**

**Réponse (200) :**
```json
{
  "id": 1,
  "tracking_id": "app-uuid-here",
  "project": {
    "tracking_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Gestion Client",
    "schema_name": "project_1"
  },
  "name": "Gestion Client App",
  "status": "deployed",
  "version": "1.2.0",
  "environment": "production",
  "api_base_url": "https://api.nocode-platform.com/runtime/projects/550e8400-e29b-41d4-a716-446655440000/",
  "admin_url": "https://admin.nocode-platform.com/app-uuid-here/",
  "public_url": "https://app.nocode-platform.com/project_1/",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-05T15:30:00Z",
  "configuration": {
    "database": {
      "type": "postgresql",
      "host": "db.production.nocode-platform.com",
      "name": "project_1_db"
    },
    "cache": {
      "type": "redis",
      "ttl": 3600
    },
    "security": {
      "jwt_required": true,
      "rate_limiting": {
        "requests_per_minute": 1000
      }
    }
  },
  "statistics": {
    "total_requests": 15420,
    "requests_today": 450,
    "active_users": 25,
    "data_records": 1250,
    "storage_used_mb": 45.2
  }
}
```

---

### PUT `/apps/{app_id}/`
**Mettre à jour une application**

**Requête :**
```json
{
  "name": "Gestion Client v2",
  "environment": "staging"
}
```

**Réponse (200) :**
```json
{
  "id": 1,
  "name": "Gestion Client v2",
  "environment": "staging",
  "updated_at": "2024-01-20T11:00:00Z",
  "regeneration_required": true
}
```

---

### DELETE `/apps/{app_id}/`
**Supprimer une application**

**Réponse (204) :** Aucun contenu

**Attention :** Supprime également toutes les données et l'application déployée.

---

### POST `/apps/{app_id}/deploy/`
**Déployer une application sur l'environnement cible**

**Requête :**
```json
{
  "environment": "production",
  "force_redeploy": false,
  "migration_required": true
}
```

**Réponse (202) :**
```json
{
  "status": "déploiement démarré",
  "deployment_id": "deploy-uuid-here",
  "app_id": 1,
  "app_status": "deployment_pending",
  "environment": "production",
  "estimated_time": "5-10 minutes",
  "deployment_steps": [
    "Validation de la configuration",
    "Migration de la base de données",
    "Déploiement du code",
    "Configuration des routes",
    "Tests de santé",
    "Mise en ligne"
  ]
}
```

**Processus de déploiement :**
1. Validation de la configuration
2. Backup des données existantes
3. Migration de la base de données
4. Déploiement du code applicatif
5. Configuration des routes et endpoints
6. Tests de santé et validation
7. Mise en ligne et monitoring

---

### GET `/apps/{app_id}/status/`
**Statut de déploiement et santé d'une application**

**Réponse (200) :**
```json
{
  "app_id": "app-uuid-here",
  "name": "Gestion Client App",
  "status": "deployed",
  "deployment_status": {
    "status": "success",
    "version": "1.2.0",
    "deployed_at": "2024-01-05T15:30:00Z",
    "deployment_duration": "7m 23s",
    "environment": "production"
  },
  "health_status": {
    "overall": "healthy",
    "database": "connected",
    "cache": "operational",
    "api": "responding",
    "last_check": "2024-01-20T12:00:00Z"
  },
  "performance": {
    "response_time_ms": 120,
    "uptime_percentage": 99.9,
    "error_rate": 0.1,
    "concurrent_users": 25
  },
  "last_deployed": "2024-01-05T15:30:00Z",
  "last_deployment_status": "success",
  "api_url": "https://api.nocode-platform.com/runtime/projects/550e8400-e29b-41d4-a716-446655440000/",
  "admin_url": "https://admin.nocode-platform.com/app-uuid-here/",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-05T15:30:00Z"
}
```

---

### GET `/apps/{app_id}/logs/`
**Journaux de déploiement et d'exécution**

**Réponse (200) :**
```json
{
  "app_id": "app-uuid-here",
  "app_name": "Gestion Client App",
  "total_logs": 15,
  "logs": [
    {
      "id": 15,
      "status": "success",
      "environment": "production",
      "version": "1.2.0",
      "created_at": "2024-01-05T15:30:00Z",
      "completed_at": "2024-01-05T15:37:23Z",
      "duration": "7m 23s",
      "performed_by": {
        "id": 1,
        "email": "admin@company.com"
      },
      "steps": [
        {
          "name": "Database Migration",
          "status": "success",
          "duration": "2m 15s"
        },
        {
          "name": "Code Deployment",
          "status": "success", 
          "duration": "3m 45s"
        },
        {
          "name": "Health Checks",
          "status": "success",
          "duration": "1m 23s"
        }
      ],
      "error_message": null
    },
    {
      "id": 14,
      "status": "failed",
      "environment": "staging",
      "version": "1.1.9",
      "created_at": "2024-01-05T14:00:00Z",
      "completed_at": "2024-01-05T14:02:30Z",
      "duration": "2m 30s",
      "error_message": "Database migration failed: Column 'email' already exists"
    }
  ]
}
```

---

## 📊 **CRUD Dynamique sur Tables**

### GET `/projects/{project_id}/schema/`
**Schéma complet du projet (métadonnées de toutes les tables)**

**Réponse (200) :**
```json
{
  "project": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Gestion Client",
    "schema_name": "project_1",
    "status": "published"
  },
  "tables": {
    "clients": {
      "table_name": "clients",
      "display_name": "Clients",
      "icon": "👥",
      "description": "Gestion des clients",
      "api_endpoint": "/projects/550e8400-e29b-41d4-a716-446655440000/tables/clients/",
      "records_count": 150,
      "created_at": "2024-01-01T10:30:00Z",
      "fields": [
        {
          "name": "id",
          "display_name": "ID",
          "field_type": "INTEGER",
          "is_primary_key": true,
          "is_required": false,
          "is_readonly": true,
          "validation": {}
        },
        {
          "name": "nom",
          "display_name": "Nom",
          "field_type": "TEXT_SHORT",
          "is_required": true,
          "is_unique": false,
          "validation": {
            "min_length": 2,
            "max_length": 100
          }
        },
        {
          "name": "email",
          "display_name": "Email",
          "field_type": "EMAIL",
          "is_required": true,
          "is_unique": true,
          "validation": {
            "format": "email"
          }
        },
        {
          "name": "telephone",
          "display_name": "Téléphone",
          "field_type": "PHONE",
          "is_required": false,
          "validation": {
            "pattern": "^\\+?[0-9]{10,15}$"
          }
        },
        {
          "name": "adresse",
          "display_name": "Adresse",
          "field_type": "TEXT_LONG",
          "is_required": false,
          "validation": {}
        }
      ]
    },
    "produits": {
      "table_name": "produits",
      "display_name": "Produits",
      "icon": "📦",
      "description": "Catalogue des produits",
      "api_endpoint": "/projects/550e8400-e29b-41d4-a716-446655440000/tables/produits/",
      "records_count": 85,
      "created_at": "2024-01-01T11:00:00Z",
      "fields": [
        {
          "name": "id",
          "display_name": "ID",
          "field_type": "INTEGER",
          "is_primary_key": true,
          "is_readonly": true
        },
        {
          "name": "reference",
          "display_name": "Référence",
          "field_type": "TEXT_SHORT",
          "is_required": true,
          "is_unique": true,
          "validation": {
            "max_length": 50
          }
        },
        {
          "name": "nom",
          "display_name": "Nom",
          "field_type": "TEXT_SHORT",
          "is_required": true,
          "validation": {
            "max_length": 200
          }
        },
        {
          "name": "description",
          "display_name": "Description",
          "field_type": "TEXT_LONG",
          "is_required": false
        },
        {
          "name": "prix",
          "display_name": "Prix",
          "field_type": "DECIMAL",
          "is_required": true,
          "validation": {
            "min_value": 0,
            "max_digits": 10,
            "decimal_places": 2
          }
        },
        {
          "name": "stock",
          "display_name": "Stock",
          "field_type": "INTEGER",
          "is_required": true,
          "validation": {
            "min_value": 0
          }
        },
        {
          "name": "actif",
          "display_name": "Actif",
          "field_type": "BOOLEAN",
          "is_required": true,
          "default_value": true
        }
      ]
    }
  },
  "statistics": {
    "total_tables": 5,
    "total_records": 1250,
    "storage_used_mb": 45.2,
    "last_updated": "2024-01-20T12:00:00Z"
  }
}
```

---

### GET `/projects/{project_id}/schema/{table_name}/`
**Schéma détaillé d'une table spécifique**

**Réponse (200) :**
```json
{
  "table_name": "clients",
  "display_name": "Clients",
  "icon": "👥",
  "description": "Gestion des clients de l'entreprise",
  "api_endpoint": "/projects/550e8400-e29b-41d4-a716-446655440000/tables/clients/",
  "database_table": "project_1_clients",
  "records_count": 150,
  "created_at": "2024-01-01T10:30:00Z",
  "updated_at": "2024-01-15T14:20:00Z",
  "permissions": {
    "can_create": true,
    "can_read": true,
    "can_update": true,
    "can_delete": false
  },
  "fields": [
    {
      "name": "id",
      "display_name": "ID",
      "field_type": "INTEGER",
      "is_primary_key": true,
      "is_required": false,
      "is_readonly": true,
      "is_visible_in_list": false,
      "is_visible_in_form": false,
      "validation": {},
      "default_value": null
    },
    {
      "name": "nom",
      "display_name": "Nom complet",
      "field_type": "TEXT_SHORT",
      "is_required": true,
      "is_unique": false,
      "is_readonly": false,
      "is_visible_in_list": true,
      "is_visible_in_form": true,
      "validation": {
        "min_length": 2,
        "max_length": 100,
        "pattern": "^[a-zA-Z\\s\\-']+$"
      },
      "default_value": null,
      "form_config": {
        "placeholder": "Entrez le nom complet",
        "help_text": "Nom et prénom du client"
      }
    },
    {
      "name": "email",
      "display_name": "Email professionnel",
      "field_type": "EMAIL",
      "is_required": true,
      "is_unique": true,
      "is_readonly": false,
      "is_visible_in_list": true,
      "is_visible_in_form": true,
      "validation": {
        "format": "email"
      },
      "default_value": null,
      "form_config": {
        "placeholder": "client@entreprise.com",
        "help_text": "Adresse email professionnelle"
      }
    },
    {
      "name": "telephone",
      "display_name": "Téléphone",
      "field_type": "PHONE",
      "is_required": false,
      "is_unique": false,
      "is_readonly": false,
      "is_visible_in_list": true,
      "is_visible_in_form": true,
      "validation": {
        "pattern": "^\\+?[0-9]{10,15}$"
      },
      "default_value": null,
      "form_config": {
        "placeholder": "+33612345678",
        "help_text": "Numéro de téléphone avec indicatif pays"
      }
    }
  ],
  "indexes": [
    {
      "name": "idx_clients_email",
      "fields": ["email"],
      "type": "unique"
    },
    {
      "name": "idx_clients_nom",
      "fields": ["nom"],
      "type": "normal"
    }
  ],
  "relationships": [
    {
      "type": "has_many",
      "target_table": "commandes",
      "foreign_key": "client_id",
      "target_display_name": "Commandes"
    }
  ]
}
```

---

### GET `/projects/{project_id}/tables/{table_name}/`
**Lister les enregistrements d'une table**

**Paramètres de requête :**
- `page` (optional) : Numéro de page (défaut: 1)
- `page_size` (optional) : Taille de page (défaut: 20, max: 100)
- `search` (optional) : Recherche textuelle
- `sort_by` (optional) : Champ de tri
- `sort_order` (optional) : Ordre de tri (asc/desc)
- `filters` (optional) : Filtres JSON

**Réponse (200) :**
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/v1/runtime/projects/550e8400-e29b-41d4-a716-446655440000/tables/clients/?page=2&page_size=20",
  "previous": null,
  "results": [
    {
      "id": 1,
      "nom": "Jean Dupont",
      "email": "jean.dupont@entreprise.com",
      "telephone": "+33612345678",
      "adresse": "123 Rue de la Paix, 75001 Paris",
      "created_at": "2024-01-01T10:30:00Z",
      "updated_at": "2024-01-15T14:20:00Z"
    },
    {
      "id": 2,
      "nom": "Marie Martin",
      "email": "marie.martin@company.fr",
      "telephone": "+33698765432",
      "adresse": "456 Avenue des Champs-Élysées, 75008 Paris",
      "created_at": "2024-01-02T09:15:00Z",
      "updated_at": "2024-01-10T11:30:00Z"
    }
  ],
  "filters_applied": {
    "search": null,
    "sort_by": "created_at",
    "sort_order": "desc"
  },
  "table_info": {
    "table_name": "clients",
    "display_name": "Clients",
    "total_fields": 5,
    "permissions": {
      "can_create": true,
      "can_read": true,
      "can_update": true,
      "can_delete": false
    }
  }
}
```

**Exemples de filtres :**
```
# Recherche textuelle
GET /projects/{id}/tables/clients/?search=jean

# Tri par nom
GET /projects/{id}/tables/clients/?sort_by=nom&sort_order=asc

# Filtres avancés
GET /projects/{id}/tables/clients/?filters={"actif": true, "created_at__gte": "2024-01-01"}

# Pagination
GET /projects/{id}/tables/clients/?page=2&page_size=50
```

---

### POST `/projects/{project_id}/tables/{table_name}/`
**Créer un nouvel enregistrement**

**Requête :**
```json
{
  "nom": "Sophie Bernard",
  "email": "sophie.bernard@techcorp.io",
  "telephone": "+33655558888",
  "adresse": "789 Boulevard Haussmann, 75009 Paris"
}
```

**Réponse (201) :**
```json
{
  "id": 151,
  "nom": "Sophie Bernard",
  "email": "sophie.bernard@techcorp.io",
  "telephone": "+33655558888",
  "adresse": "789 Boulevard Haussmann, 75009 Paris",
  "created_at": "2024-01-20T13:00:00Z",
  "updated_at": "2024-01-20T13:00:00Z"
}
```

**Validation automatique :**
- Champs requis vérifiés
- Formats validés (email, téléphone, etc.)
- Contraintes d'unicité respectées
- Valeurs par défaut appliquées

---

### GET `/projects/{project_id}/tables/{table_name}/{record_id}/`
**Récupérer un enregistrement spécifique**

**Réponse (200) :**
```json
{
  "id": 1,
  "nom": "Jean Dupont",
  "email": "jean.dupont@entreprise.com",
  "telephone": "+33612345678",
  "adresse": "123 Rue de la Paix, 75001 Paris",
  "created_at": "2024-01-01T10:30:00Z",
  "updated_at": "2024-01-15T14:20:00Z",
  "metadata": {
    "created_by": "admin@company.com",
    "updated_by": "jean.dupont@entreprise.com",
    "version": 3
  }
}
```

**Erreurs :**
- `404` : Enregistrement non trouvé
- `403` : Accès non autorisé à cette table

---

### PUT `/projects/{project_id}/tables/{table_name}/{record_id}/`
**Mettre à jour un enregistrement**

**Requête :**
```json
{
  "nom": "Jean Dupont-Updated",
  "telephone": "+33612345679",
  "adresse": "123 Rue de la Paix, 75001 Paris, France"
}
```

**Réponse (200) :**
```json
{
  "id": 1,
  "nom": "Jean Dupont-Updated",
  "email": "jean.dupont@entreprise.com",
  "telephone": "+33612345679",
  "adresse": "123 Rue de la Paix, 75001 Paris, France",
  "created_at": "2024-01-01T10:30:00Z",
  "updated_at": "2024-01-20T14:00:00Z",
  "updated_by": "admin@company.com"
}
```

---

### PATCH `/projects/{project_id}/tables/{table_name}/{record_id}/`
**Mise à jour partielle d'un enregistrement**

**Requête :**
```json
{
  "telephone": "+33612345679"
}
```

**Réponse (200) :**
```json
{
  "id": 1,
  "telephone": "+33612345679",
  "updated_at": "2024-01-20T14:15:00Z"
}
```

---

### DELETE `/projects/{project_id}/tables/{table_name}/{record_id}/`
**Supprimer un enregistrement**

**Réponse (204) :** Aucun contenu

**Note :** La suppression est définitive sauf si des soft deletes sont configurés.

---

## 🏗️ **Métadonnées Frontend**

### GET `/projects/{project_id}/tables/{table_name}/schema/`
**Configuration de formulaire pour une table**

**Réponse (200) :**
```json
{
  "table_name": "clients",
  "display_name": "Clients",
  "total_fields": 5,
  "form_config": {
    "layout": "vertical",
    "columns": 1,
    "submit_button": {
      "label": "Enregistrer",
      "style": "primary"
    },
    "cancel_button": {
      "label": "Annuler",
      "action": "navigate",
      "target": "/clients"
    }
  },
  "validation_rules": {
    "nom": {
      "required": true,
      "min_length": 2,
      "max_length": 100,
      "pattern": "^[a-zA-Z\\s\\-']+$"
    },
    "email": {
      "required": true,
      "format": "email",
      "unique": true
    },
    "telephone": {
      "required": false,
      "pattern": "^\\+?[0-9]{10,15}$"
    }
  },
  "fields": [
    {
      "name": "nom",
      "display_name": "Nom complet",
      "field_type": "TEXT_SHORT",
      "form_field": {
        "type": "text",
        "placeholder": "Entrez le nom complet",
        "help_text": "Nom et prénom du client",
        "autocomplete": "name"
      },
      "is_required": true,
      "validation": {
        "min_length": 2,
        "max_length": 100
      }
    },
    {
      "name": "email",
      "display_name": "Email professionnel",
      "field_type": "EMAIL",
      "form_field": {
        "type": "email",
        "placeholder": "client@entreprise.com",
        "help_text": "Adresse email professionnelle",
        "autocomplete": "email"
      },
      "is_required": true,
      "validation": {
        "format": "email"
      }
    },
    {
      "name": "telephone",
      "display_name": "Téléphone",
      "field_type": "PHONE",
      "form_field": {
        "type": "tel",
        "placeholder": "+33612345678",
        "help_text": "Numéro avec indicatif pays",
        "autocomplete": "tel"
      },
      "is_required": false,
      "validation": {
        "pattern": "^\\+?[0-9]{10,15}$"
      }
    },
    {
      "name": "adresse",
      "display_name": "Adresse",
      "field_type": "TEXT_LONG",
      "form_field": {
        "type": "textarea",
        "placeholder": "123 Rue de la Paix, 75001 Paris",
        "help_text": "Adresse postale complète",
        "rows": 3
      },
      "is_required": false
    }
  ]
}
```

---

### GET `/projects/{project_id}/tables/{table_name}/fields/`
**Liste des champs avec métadonnées**

**Réponse (200) :**
```json
{
  "table_name": "clients",
  "fields": [
    {
      "name": "id",
      "display_name": "ID",
      "field_type": "INTEGER",
      "is_primary_key": true,
      "is_readonly": true,
      "is_visible_in_list": false,
      "is_visible_in_form": false,
      "list_config": {
        "width": 80,
        "sortable": false
      }
    },
    {
      "name": "nom",
      "display_name": "Nom",
      "field_type": "TEXT_SHORT",
      "is_primary_key": false,
      "is_readonly": false,
      "is_visible_in_list": true,
      "is_visible_in_form": true,
      "list_config": {
        "width": 200,
        "sortable": true,
        "filterable": true
      },
      "form_field": {
        "type": "text",
        "placeholder": "Nom du client"
      }
    },
    {
      "name": "email",
      "display_name": "Email",
      "field_type": "EMAIL",
      "is_primary_key": false,
      "is_readonly": false,
      "is_visible_in_list": true,
      "is_visible_in_form": true,
      "list_config": {
        "width": 250,
        "sortable": true,
        "filterable": true
      },
      "form_field": {
        "type": "email",
        "placeholder": "email@exemple.com"
      }
    }
  ]
}
```

---

## 📋 **Logs de Déploiement**

### GET `/deployment-logs/`
**Lister les journaux de déploiement**

**Paramètres de requête :**
- `app_id` (optional) : Filtrer par application
- `status` (optional) : Filtrer par statut (success/failed/pending)
- `environment` (optional) : Filtrer par environnement

**Réponse (200) :**
```json
{
  "count": 25,
  "results": [
    {
      "id": 25,
      "app": {
        "id": 1,
        "tracking_id": "app-uuid-here",
        "name": "Gestion Client App"
      },
      "status": "success",
      "environment": "production",
      "version": "1.2.0",
      "created_at": "2024-01-05T15:30:00Z",
      "completed_at": "2024-01-05T15:37:23Z",
      "duration": "7m 23s",
      "performed_by": {
        "id": 1,
        "email": "admin@company.com",
        "full_name": "Admin User"
      },
      "deployment_details": {
        "database_migrations": 3,
        "files_deployed": 145,
        "tests_run": 25,
        "tests_passed": 25
      }
    }
  ]
}
```

---

### GET `/deployment-logs/{log_id}/`
**Détails d'un journal de déploiement**

**Réponse (200) :**
```json
{
  "id": 25,
  "app": {
    "id": 1,
    "tracking_id": "app-uuid-here",
    "name": "Gestion Client App"
  },
  "status": "success",
  "environment": "production",
  "version": "1.2.0",
  "created_at": "2024-01-05T15:30:00Z",
  "completed_at": "2024-01-05T15:37:23Z",
  "duration": "7m 23s",
  "performed_by": {
    "id": 1,
    "email": "admin@company.com"
  },
  "steps": [
    {
      "step": "Validation",
      "status": "success",
      "started_at": "2024-01-05T15:30:00Z",
      "completed_at": "2024-01-05T15:30:45Z",
      "duration": "45s",
      "details": "Configuration validée"
    },
    {
      "step": "Database Migration",
      "status": "success",
      "started_at": "2024-01-05T15:30:45Z",
      "completed_at": "2024-01-05T15:33:00Z",
      "duration": "2m 15s",
      "details": "3 migrations appliquées"
    },
    {
      "step": "Code Deployment",
      "status": "success",
      "started_at": "2024-01-05T15:33:00Z",
      "completed_at": "2024-01-05T15:36:45Z",
      "duration": "3m 45s",
      "details": "145 fichiers déployés"
    },
    {
      "step": "Health Checks",
      "status": "success",
      "started_at": "2024-01-05T15:36:45Z",
      "completed_at": "2024-01-05T15:37:23Z",
      "duration": "38s",
      "details": "Tous les tests passés"
    }
  ],
  "error_message": null,
  "rollback_available": false
}
```

---

### POST `/deployment-logs/{log_id}/retry/`
**Relancer un déploiement échoué**

**Réponse (202) :**
```json
{
  "status": "redémarrage du déploiement",
  "original_deployment_id": 24,
  "new_deployment": {
    "id": 26,
    "tracking_id": "deploy-uuid-new",
    "status": "pending",
    "created_at": "2024-01-20T15:00:00Z"
  },
  "estimated_time": "5-10 minutes"
}
```

---

## 🚨 **Gestion des Erreurs**

### Types d'Erreurs CRUD
| Code | Message | Contexte |
|------|---------|----------|
| `RUNTIME_001` | "Table non trouvée" | Endpoint table invalide |
| `RUNTIME_002` | "Champ requis manquant" | Validation formulaire |
| `RUNTIME_003` | "Format de donnée invalide" | Type mismatch |
| `RUNTIME_004` | "Contrainte d'unicité violée" | Duplicate entry |
| `RUNTIME_005` | "Permission refusée" | Accès table non autorisé |

### Erreurs de Déploiement
| Code | Message | Cause |
|------|---------|-------|
| `DEPLOY_001` | "Application non déployable" | Statut invalide |
| `DEPLOY_002` | "Migration de base de données échouée" | Erreur SQL |
| `DEPLOY_003` | "Configuration invalide" | Paramètres incorrects |
| `DEPLOY_004` | "Ressources insuffisantes" | Memory/CPU limit |

---

## 🔄 **Exemples d'Intégration**

### JavaScript Client pour CRUD
```javascript
class RuntimeAPI {
    constructor(baseURL, token) {
        this.baseURL = baseURL;
        this.token = token;
    }

    async getProjectSchema(projectId) {
        const response = await fetch(
            `${this.baseURL}/api/v1/runtime/projects/${projectId}/schema/`,
            {
                headers: { 'Authorization': `Bearer ${this.token}` }
            }
        );
        return response.json();
    }

    async listRecords(projectId, tableName, options = {}) {
        const params = new URLSearchParams(options);
        const response = await fetch(
            `${this.baseURL}/api/v1/runtime/projects/${projectId}/tables/${tableName}/?${params}`,
            {
                headers: { 'Authorization': `Bearer ${this.token}` }
            }
        );
        return response.json();
    }

    async createRecord(projectId, tableName, data) {
        const response = await fetch(
            `${this.baseURL}/api/v1/runtime/projects/${projectId}/tables/${tableName}/`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            }
        );
        return response.json();
    }

    async updateRecord(projectId, tableName, recordId, data) {
        const response = await fetch(
            `${this.baseURL}/api/v1/runtime/projects/${projectId}/tables/${tableName}/${recordId}/`,
            {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            }
        );
        return response.json();
    }

    async deleteRecord(projectId, tableName, recordId) {
        const response = await fetch(
            `${this.baseURL}/api/v1/runtime/projects/${projectId}/tables/${tableName}/${recordId}/`,
            {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${this.token}` }
            }
        );
        return response.status === 204;
    }
}

// Utilisation
const runtime = new RuntimeAPI('https://api.nocode-platform.com', token);

// Charger le schéma
const schema = await runtime.getProjectSchema('project-uuid');

// Lister les clients
const clients = await runtime.listRecords('project-uuid', 'clients', {
    page: 1,
    page_size: 20,
    search: 'jean'
});

// Créer un client
const newClient = await runtime.createRecord('project-uuid', 'clients', {
    nom: 'Nouveau Client',
    email: 'client@example.com',
    telephone: '+33612345678'
});
```

### React Hook pour Table Dynamique
```jsx
import { useState, useEffect } from 'react';

function useDynamicTable(projectId, tableName, options = {}) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [pagination, setPagination] = useState({
        page: 1,
        pageSize: 20,
        count: 0
    });

    const loadData = async (newOptions = {}) => {
        try {
            setLoading(true);
            const params = { ...options, ...newOptions };
            const response = await fetch(
                `/api/v1/runtime/projects/${projectId}/tables/${tableName}/?${new URLSearchParams(params)}`,
                {
                    headers: { 'Authorization': `Bearer ${token}` }
                }
            );
            const result = await response.json();
            
            setData(result.results);
            setPagination({
                page: parseInt(params.page) || 1,
                pageSize: parseInt(params.page_size) || 20,
                count: result.count
            });
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const createRecord = async (recordData) => {
        const response = await fetch(
            `/api/v1/runtime/projects/${projectId}/tables/${tableName}/`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(recordData)
            }
        );
        
        if (response.ok) {
            await loadData(); // Recharger les données
            return response.json();
        }
        throw new Error('Creation failed');
    };

    const updateRecord = async (recordId, recordData) => {
        const response = await fetch(
            `/api/v1/runtime/projects/${projectId}/tables/${tableName}/${recordId}/`,
            {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(recordData)
            }
        );
        
        if (response.ok) {
            await loadData();
            return response.json();
        }
        throw new Error('Update failed');
    };

    const deleteRecord = async (recordId) => {
        const response = await fetch(
            `/api/v1/runtime/projects/${projectId}/tables/${tableName}/${recordId}/`,
            {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            }
        );
        
        if (response.ok) {
            await loadData();
            return true;
        }
        throw new Error('Delete failed');
    };

    useEffect(() => {
        loadData();
    }, [projectId, tableName]);

    return {
        data,
        loading,
        error,
        pagination,
        loadData,
        createRecord,
        updateRecord,
        deleteRecord
    };
}

// Composant React
function DynamicTable({ projectId, tableName }) {
    const {
        data,
        loading,
        error,
        pagination,
        loadData,
        createRecord,
        updateRecord,
        deleteRecord
    } = useDynamicTable(projectId, tableName);

    if (loading) return <div>Chargement...</div>;
    if (error) return <div>Erreur: {error}</div>;

    return (
        <div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Nom</th>
                        <th>Email</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {data.map(record => (
                        <tr key={record.id}>
                            <td>{record.id}</td>
                            <td>{record.nom}</td>
                            <td>{record.email}</td>
                            <td>
                                <button onClick={() => updateRecord(record.id, { nom: record.nom + ' (modifié)' })}>
                                    Modifier
                                </button>
                                <button onClick={() => deleteRecord(record.id)}>
                                    Supprimer
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
            
            <div>
                Page {pagination.page} de {Math.ceil(pagination.count / pagination.pageSize)}
                <button onClick={() => loadData({ page: pagination.page - 1 })} disabled={pagination.page === 1}>
                    Précédent
                </button>
                <button onClick={() => loadData({ page: pagination.page + 1 })} disabled={!data.length}>
                    Suivant
                </button>
            </div>
        </div>
    );
}
```

---

## 📊 **Monitoring et Performance**

### Métriques en Temps Réel
```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "metrics": {
    "api_requests": {
      "total_today": 15420,
      "requests_per_minute": 85,
      "average_response_time_ms": 120,
      "error_rate": 0.2
    },
    "database": {
      "connections_active": 15,
      "query_time_avg_ms": 25,
      "slow_queries_count": 3
    },
    "cache": {
      "hit_rate": 0.85,
      "memory_usage_mb": 256,
      "evictions_per_minute": 2
    },
    "storage": {
      "total_records": 1250,
      "storage_used_mb": 45.2,
      "growth_rate_mb_per_day": 1.2
    }
  },
  "health_checks": {
    "database": "healthy",
    "cache": "healthy",
    "api": "healthy",
    "background_tasks": "healthy"
  }
}
```

---

## 🧪 **Tests et Validation**

### Tests CRUD Complets
```bash
# Test de création
curl -X POST http://localhost:8000/api/v1/runtime/projects/PROJECT_UUID/tables/clients/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"nom":"Test Client","email":"test@example.com"}'

# Test de lecture
curl -X GET http://localhost:8000/api/v1/runtime/projects/PROJECT_UUID/tables/clients/ \
  -H "Authorization: Bearer TOKEN"

# Test de mise à jour
curl -X PUT http://localhost:8000/api/v1/runtime/projects/PROJECT_UUID/tables/clients/1/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"nom":"Updated Client"}'

# Test de suppression
curl -X DELETE http://localhost:8000/api/v1/runtime/projects/PROJECT_UUID/tables/clients/1/ \
  -H "Authorization: Bearer TOKEN"

# Test schéma
curl -X GET http://localhost:8000/api/v1/runtime/projects/PROJECT_UUID/schema/ \
  -H "Authorization: Bearer TOKEN"
```

---

*Documentation Runtime API - Version 1.0*
