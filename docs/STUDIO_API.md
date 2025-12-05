# 🎨 Studio API - Création et Conception d'Applications

## 📋 Vue d'ensemble

Le module Studio est l'**atelier de création NoCode** où les utilisateurs conçoivent leurs applications. Il gère les projets, les schémas de données, les pages visuelles et les composants UI avec un système de drag & drop.

**Base URL :** `/api/v1/studio/`

---

## 🏗️ **Projets NoCode**

### GET `/projects/`
**Lister les projets de l'utilisateur**

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
      "tracking_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Gestion Client",
      "organization_id": null,
      "organization_name": null,
      "schema_name": "project_1",
      "created_by_username": "john_doe",
      "status": "published",
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-05T15:30:00Z"
    },
    {
      "tracking_id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "E-commerce Boutique",
      "organization_id": "org-uuid-here",
      "organization_name": "Tech Company",
      "schema_name": "project_2",
      "created_by_username": "john_doe",
      "status": "draft",
      "created_at": "2024-01-10T09:00:00Z",
      "updated_at": "2024-01-12T14:20:00Z"
    }
  ]
}
```

**Paramètres de requête :**
- `organization_id` (optional) : Filtrer par organisation
- `status` (optional) : Filtrer par statut (draft/published/archived)
- `page` (optional) : Numéro de page (défaut: 1)
- `page_size` (optional) : Taille de page (défaut: 20)

---

### POST `/projects/`
**Créer un nouveau projet**

**Requête :**
```json
{
  "name": "Mon Application NoCode",
  "organization_id": "org-uuid-here"
}
```

**Réponse (201) :**
```json
{
  "tracking_id": "770e8400-e29b-41d4-a716-446655440002",
  "name": "Mon Application NoCode",
  "organization_id": "org-uuid-here",
  "organization_name": "Tech Company",
  "schema_name": "project_3",
  "created_by_username": "john_doe",
  "status": "draft",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

**Validation :**
- `name` : Minimum 2 caractères, unique par organisation
- `organization_id` : Doit appartenir à l'utilisateur

---

### GET `/projects/{project_id}/`
**Détails d'un projet spécifique**

**Réponse (200) :**
```json
{
  "tracking_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Gestion Client",
  "organization_id": null,
  "organization_name": null,
  "schema_name": "project_1",
  "created_by_username": "john_doe",
  "status": "published",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-05T15:30:00Z",
  "statistics": {
    "tables_count": 5,
    "pages_count": 8,
    "components_count": 24,
    "records_count": 1250
  }
}
```

---

### PUT `/projects/{project_id}/`
**Mettre à jour un projet**

**Requête :**
```json
{
  "name": "Gestion Client v2",
  "organization_id": "new-org-uuid"
}
```

**Réponse (200) :**
```json
{
  "tracking_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Gestion Client v2",
  "organization_id": "new-org-uuid",
  "organization_name": "New Company",
  "updated_at": "2024-01-20T11:00:00Z"
}
```

---

### DELETE `/projects/{project_id}/`
**Supprimer un projet**

**Réponse (204) :** Aucun contenu

**Note :** Supprime également toutes les tables, pages et composants associés.

---

### POST `/projects/{project_id}/publish/`
**Publier un projet (déclenche la génération Runtime)**

**Réponse (200) :**
```json
{
  "message": "Génération de l'application démarrée",
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "generation_task_id": "task-uuid-here",
  "estimated_time": "2-3 minutes",
  "status": "generating"
}
```

**Flow de publication :**
1. Validation du projet
2. Génération des modèles Django
3. Création des serializers dynamiques
4. Déploiement des endpoints Runtime
5. Mise à jour du statut

---

### POST `/projects/{project_id}/unpublish/`
**Dépublier un projet**

**Réponse (200) :**
```json
{
  "message": "Projet dépublié",
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "draft",
  "unpublished_at": "2024-01-20T12:00:00Z"
}
```

---

### GET `/projects/{project_id}/deployment_status/`
**Statut de déploiement du projet**

**Réponse (200) :**
```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "published",
  "name": "Gestion Client",
  "deployment": {
    "status": "deployed",
    "url": "https://app.nocode-platform.com/project_1/",
    "api_url": "https://api.nocode-platform.com/api/v1/runtime/projects/550e8400-e29b-41d4-a716-446655440000/",
    "deployed_at": "2024-01-05T15:30:00Z",
    "version": "1.2.0"
  },
  "generation": {
    "status": "completed",
    "tables_generated": 5,
    "endpoints_created": 25,
    "completed_at": "2024-01-05T15:25:00Z"
  }
}
```

---

### GET `/projects/{project_id}/schemas/`
**Lister les schémas de données du projet**

**Réponse (200) :**
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "table_name": "clients",
      "display_name": "Clients",
      "fields_count": 8,
      "records_count": 150,
      "created_at": "2024-01-01T10:30:00Z"
    },
    {
      "id": 2,
      "table_name": "produits",
      "display_name": "Produits",
      "fields_count": 12,
      "records_count": 85,
      "created_at": "2024-01-01T11:00:00Z"
    }
  ]
}
```

---

## 📊 **Schémas de Données**

### GET `/schemas/`
**Lister les schémas de données**

**Paramètres de requête :**
- `project` (optional) : Filtrer par projet UUID
- `table_name` (optional) : Filtrer par nom de table

**Réponse (200) :**
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "project": {
        "tracking_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Gestion Client"
      },
      "table_name": "clients",
      "display_name": "Clients",
      "fields_config": [
        {
          "name": "nom",
          "type": "string",
          "label": "Nom",
          "required": true,
          "max_length": 100
        },
        {
          "name": "email",
          "type": "string",
          "label": "Email",
          "required": true,
          "unique": true
        }
      ],
      "created_at": "2024-01-01T10:30:00Z",
      "updated_at": "2024-01-05T14:00:00Z"
    }
  ]
}
```

---

### POST `/schemas/`
**Créer un nouveau schéma de données**

**Requête :**
```json
{
  "project": "550e8400-e29b-41d4-a716-446655440000",
  "table_name": "commandes",
  "display_name": "Commandes",
  "fields_config": [
    {
      "name": "reference",
      "type": "string",
      "label": "Référence",
      "required": true,
      "unique": true,
      "default": "AUTO"
    },
    {
      "name": "client_id",
      "type": "integer",
      "label": "ID Client",
      "required": true
    },
    {
      "name": "montant_total",
      "type": "float",
      "label": "Montant Total",
      "required": true,
      "min_value": 0
    },
    {
      "name": "statut",
      "type": "string",
      "label": "Statut",
      "required": true,
      "default": "EN_ATTENTE"
    },
    {
      "name": "date_commande",
      "type": "datetime",
      "label": "Date Commande",
      "required": true,
      "default": "NOW"
    }
  ]
}
```

**Réponse (201) :**
```json
{
  "id": 11,
  "project": "550e8400-e29b-41d4-a716-446655440000",
  "table_name": "commandes",
  "display_name": "Commandes",
  "fields_config": [
    {
      "name": "reference",
      "type": "string",
      "label": "Référence",
      "required": true,
      "unique": true,
      "default": "AUTO"
    }
  ],
  "created_at": "2024-01-20T13:00:00Z",
  "updated_at": "2024-01-20T13:00:00Z",
  "sql_table_created": true,
  "table_name_full": "project_1_commandes"
}
```

**Types de champs disponibles :**
- `string` : Texte court (max 255 caractères)
- `text` : Texte long (illimité)
- `integer` : Nombre entier
- `float` : Nombre décimal
- `boolean` : Vrai/Faux
- `date` : Date (YYYY-MM-DD)
- `datetime` : Date + Heure
- `json` : Objet JSON complexe

**Options de validation :**
- `required` : Champ obligatoire
- `unique` : Valeur unique
- `default` : Valeur par défaut
- `max_length` : Longueur maximale (string)
- `min_value` / `max_value` : Valeurs min/max (integer/float)

---

### GET `/schemas/{schema_id}/`
**Détails d'un schéma**

**Réponse (200) :**
```json
{
  "id": 1,
  "project": {
    "tracking_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Gestion Client"
  },
  "table_name": "clients",
  "display_name": "Clients",
  "fields_config": [
    {
      "name": "id",
      "type": "integer",
      "label": "ID",
      "required": false,
      "auto_increment": true
    },
    {
      "name": "nom",
      "type": "string",
      "label": "Nom",
      "required": true,
      "max_length": 100
    }
  ],
  "sql_info": {
    "table_name": "project_1_clients",
    "columns_count": 8,
    "indexes": ["id", "email"],
    "constraints": ["unique_email"]
  },
  "statistics": {
    "records_count": 150,
    "last_record_at": "2024-01-20T12:30:00Z",
    "storage_size_kb": 45.2
  },
  "created_at": "2024-01-01T10:30:00Z",
  "updated_at": "2024-01-05T14:00:00Z"
}
```

---

### PUT `/schemas/{schema_id}/`
**Mettre à jour un schéma**

**Requête :**
```json
{
  "display_name": "Clients VIP",
  "fields_config": [
    {
      "name": "nom",
      "type": "string",
      "label": "Nom Complet",
      "required": true,
      "max_length": 150
    },
    {
      "name": "email",
      "type": "string",
      "label": "Email Professionnel",
      "required": true,
      "unique": true
    },
    {
      "name": "telephone",
      "type": "string",
      "label": "Téléphone",
      "required": false
    }
  ]
}
```

**Réponse (200) :**
```json
{
  "id": 1,
  "display_name": "Clients VIP",
  "fields_config": [...],
  "updated_at": "2024-01-20T14:00:00Z",
  "sql_migration_applied": true,
  "migration_id": "migration_001"
}
```

---

### DELETE `/schemas/{schema_id}/`
**Supprimer un schéma**

**Réponse (204) :** Aucun contenu

**Attention :** Supprime également la table SQL et toutes les données.

---

### GET `/schemas/{schema_id}/fields/`
**Lister les champs d'un schéma**

**Réponse (200) :**
```json
{
  "count": 8,
  "results": [
    {
      "id": 1,
      "schema": 1,
      "name": "nom",
      "display_name": "Nom",
      "field_type": "TEXT_SHORT",
      "is_required": true,
      "is_unique": false,
      "default_value": null,
      "validation_rules": {
        "max_length": 100
      },
      "created_at": "2024-01-01T10:30:00Z"
    },
    {
      "id": 2,
      "schema": 1,
      "name": "email",
      "display_name": "Email",
      "field_type": "EMAIL",
      "is_required": true,
      "is_unique": true,
      "default_value": null,
      "validation_rules": {
        "format": "email"
      },
      "created_at": "2024-01-01T10:30:00Z"
    }
  ]
}
```

---

## 📄 **Pages Visuelles**

### GET `/pages/`
**Lister les pages**

**Paramètres de requête :**
- `project` (optional) : Filtrer par projet UUID
- `is_home` (optional) : Filtrer pages d'accueil

**Réponse (200) :**
```json
{
  "count": 8,
  "results": [
    {
      "id": 1,
      "project": {
        "tracking_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Gestion Client"
      },
      "name": "Tableau de Bord",
      "route": "/dashboard",
      "is_home": true,
      "config": {
        "layout": "grid",
        "theme": "light"
      },
      "components_count": 5,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

---

### POST `/pages/`
**Créer une nouvelle page**

**Requête :**
```json
{
  "project": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Liste des Clients",
  "route": "/clients",
  "is_home": false,
  "config": {
    "layout": "table",
    "theme": "light",
    "pagination": {
      "enabled": true,
      "page_size": 20
    }
  }
}
```

**Réponse (201) :**
```json
{
  "id": 9,
  "project": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Liste des Clients",
  "route": "clients",
  "is_home": false,
  "config": {
    "layout": "table",
    "theme": "light",
    "pagination": {
      "enabled": true,
      "page_size": 20
    }
  },
  "created_at": "2024-01-20T15:00:00Z"
}
```

---

### GET `/pages/{page_id}/components/`
**Lister les composants d'une page**

**Réponse (200) :**
```json
{
  "count": 5,
  "results": [
    {
      "tracking_id": "comp-uuid-1",
      "component_type": "DataTable",
      "position": {
        "x": 10,
        "y": 10,
        "width": 800,
        "height": 400
      },
      "config": {
        "table_name": "clients",
        "columns": ["nom", "email", "telephone"],
        "sortable": true,
        "filterable": true
      },
      "created_at": "2024-01-01T12:30:00Z"
    },
    {
      "tracking_id": "comp-uuid-2",
      "component_type": "Button",
      "position": {
        "x": 10,
        "y": 420,
        "width": 120,
        "height": 40
      },
      "config": {
        "label": "Ajouter Client",
        "action": "navigate",
        "target": "/clients/new"
      },
      "created_at": "2024-01-01T12:35:00Z"
    }
  ]
}
```

---

## 🧩 **Composants UI**

### GET `/components/`
**Lister les composants**

**Paramètres de requête :**
- `page` (optional) : Filtrer par page ID
- `component_type` (optional) : Filtrer par type

**Réponse (200) :**
```json
{
  "count": 24,
  "results": [
    {
      "tracking_id": "comp-uuid-1",
      "page": {
        "id": 1,
        "name": "Tableau de Bord"
      },
      "component_type": "DataTable",
      "position": {
        "x": 10,
        "y": 10,
        "width": 800,
        "height": 400
      },
      "config": {
        "table_name": "clients",
        "columns": ["nom", "email", "telephone"],
        "sortable": true,
        "filterable": true,
        "actions": ["edit", "delete"]
      },
      "created_at": "2024-01-01T12:30:00Z",
      "updated_at": "2024-01-05T16:00:00Z"
    }
  ]
}
```

---

### POST `/components/`
**Créer un nouveau composant**

**Requête :**
```json
{
  "page": 1,
  "component_type": "Form",
  "position": {
    "x": 50,
    "y": 100,
    "width": 600,
    "height": 500
  },
  "config": {
    "form_title": "Nouveau Client",
    "table_name": "clients",
    "fields": [
      {
        "name": "nom",
        "label": "Nom",
        "type": "text",
        "required": true
      },
      {
        "name": "email",
        "label": "Email",
        "type": "email",
        "required": true
      },
      {
        "name": "telephone",
        "label": "Téléphone",
        "type": "tel",
        "required": false
      }
    ],
    "submit_button": {
      "label": "Enregistrer",
      "action": "create_record"
    }
  }
}
```

**Réponse (201) :**
```json
{
  "tracking_id": "comp-uuid-new",
  "page": 1,
  "component_type": "Form",
  "position": {
    "x": 50,
    "y": 100,
    "width": 600,
    "height": 500
  },
  "config": {
    "form_title": "Nouveau Client",
    "table_name": "clients",
    "fields": [...]
  },
  "created_at": "2024-01-20T16:00:00Z"
}
```

---

### PUT `/components/{component_id}/`
**Mettre à jour un composant**

**Requête :**
```json
{
  "position": {
    "x": 60,
    "y": 110,
    "width": 650,
    "height": 520
  },
  "config": {
    "form_title": "Formulaire Client",
    "submit_button": {
      "label": "Créer Client",
      "action": "create_record"
    }
  }
}
```

**Réponse (200) :**
```json
{
  "tracking_id": "comp-uuid-1",
  "updated_at": "2024-01-20T16:30:00Z"
}
```

---

### DELETE `/components/{component_id}/`
**Supprimer un composant**

**Réponse (204) :** Aucun contenu

---

## 🎛️ **Éditeur Visuel**

### POST `/editor/add_component/`
**Ajouter un composant via l'éditeur**

**Requête :**
```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "component_type": "Chart",
  "position": {
    "x": 100,
    "y": 200,
    "width": 400,
    "height": 300
  },
  "config": {
    "chart_type": "bar",
    "data_source": "clients",
    "x_axis": "created_at",
    "y_axis": "count",
    "title": "Évolution des Clients"
  }
}
```

**Réponse (200) :**
```json
{
  "component_id": "comp-uuid-new",
  "page_id": "page-uuid-home",
  "page_created": false,
  "message": "Composant ajouté avec succès"
}
```

---

### PUT `/editor/move_component/`
**Déplacer un composant**

**Requête :**
```json
{
  "component_id": "comp-uuid-1",
  "position": {
    "x": 150,
    "y": 250,
    "width": 450,
    "height": 350
  }
}
```

**Réponse (200) :**
```json
{
  "message": "Composant déplacé",
  "new_position": {
    "x": 150,
    "y": 250,
    "width": 450,
    "height": 350
  }
}
```

---

### DELETE `/editor/remove_component/`
**Supprimer un composant via l'éditeur**

**Requête :**
```json
{
  "component_id": "comp-uuid-1"
}
```

**Réponse (200) :**
```json
{
  "message": "Composant supprimé"
}
```

---

### GET `/editor/state/`
**État actuel de l'éditeur**

**Paramètres de requête :**
- `project_id` (required) : UUID du projet

**Réponse (200) :**
```json
{
  "project": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Gestion Client",
    "status": "published"
  },
  "pages": [
    {
      "id": "page-uuid-1",
      "name": "Tableau de Bord",
      "is_home": true,
      "components": [
        {
          "tracking_id": "comp-uuid-1",
          "component_type": "DataTable",
          "position": { "x": 10, "y": 10, "width": 800, "height": 400 },
          "config": {
            "table_name": "clients",
            "columns": ["nom", "email", "telephone"]
          }
        }
      ]
    }
  ],
  "statistics": {
    "total_pages": 3,
    "total_components": 12,
    "last_modified": "2024-01-20T16:30:00Z"
  }
}
```

---

## 🧩 **Types de Composants Disponibles**

### Composants de Données
- **DataTable** : Tableau de données avec pagination
- **Form** : Formulaire de saisie/modification
- **DetailView** : Vue détaillée d'un enregistrement
- **ListView** : Liste personnalisée
- **Chart** : Graphiques (bar, line, pie, etc.)

### Composants d'Interface
- **Button** : Bouton avec actions
- **Input** : Champ de saisie
- **Text** : Texte statique ou dynamique
- **Image** : Affichage d'images
- **Container** : Conteneur pour organiser

### Composants de Navigation
- **Menu** : Menu de navigation
- **Breadcrumb** : Fil d'Ariane
- **Tabs** : Onglets
- **Modal** : Fenêtre modale

### Composants Avancés
- **Kanban** : Tableau Kanban
- **Calendar** : Calendrier interactif
- **FileUpload** : Upload de fichiers
- **RichText** : Éditeur de texte riche

---

## 📊 **Configuration des Composants**

### DataTable
```json
{
  "component_type": "DataTable",
  "config": {
    "table_name": "clients",
    "columns": [
      {"name": "nom", "label": "Nom", "sortable": true},
      {"name": "email", "label": "Email", "sortable": true},
      {"name": "telephone", "label": "Téléphone", "sortable": false}
    ],
    "pagination": {
      "enabled": true,
      "page_size": 20
    },
    "filtering": {
      "enabled": true,
      "fields": ["nom", "email"]
    },
    "actions": ["view", "edit", "delete"],
    "selection": {
      "enabled": true,
      "multiple": true
    }
  }
}
```

### Form
```json
{
  "component_type": "Form",
  "config": {
    "form_title": "Nouveau Client",
    "table_name": "clients",
    "layout": "vertical",
    "fields": [
      {
        "name": "nom",
        "label": "Nom",
        "type": "text",
        "required": true,
        "placeholder": "Entrez le nom"
      },
      {
        "name": "email",
        "label": "Email",
        "type": "email",
        "required": true,
        "validation": {
          "format": "email"
        }
      }
    ],
    "submit_button": {
      "label": "Enregistrer",
      "style": "primary",
      "action": "create_record",
      "redirect_on_success": "/clients"
    },
    "cancel_button": {
      "label": "Annuler",
      "action": "navigate",
      "target": "/clients"
    }
  }
}
```

### Chart
```json
{
  "component_type": "Chart",
  "config": {
    "chart_type": "bar",
    "title": "Évolution des Clients",
    "data_source": {
      "table": "clients",
      "query": "SELECT DATE(created_at) as date, COUNT(*) as count FROM clients GROUP BY DATE(created_at)"
    },
    "x_axis": {
      "field": "date",
      "label": "Date",
      "type": "datetime"
    },
    "y_axis": {
      "field": "count",
      "label": "Nombre de Clients",
      "type": "integer"
    },
    "styling": {
      "colors": ["#3B82F6", "#10B981"],
      "grid": true,
      "legend": true
    }
  }
}
```

---

## 🔄 **Workflows de Création**

### Flow Complet de Création d'Application
```
1. POST /studio/projects/                    → Créer projet
2. POST /studio/schemas/                     → Définir tables
3. POST /studio/pages/                       → Créer pages
4. POST /studio/components/                  → Ajouter composants
5. POST /studio/projects/{id}/publish/       → Publier
6. POST /runtime/apps/                       → Générer application
7. POST /runtime/apps/{id}/deploy/           → Déployer
```

### Flow de Modification
```
1. GET /studio/editor/state/?project_id=X    → État actuel
2. PUT /studio/components/{id}/              → Modifier composant
3. PUT /studio/schemas/{id}/                 → Modifier schéma
4. POST /studio/projects/{id}/publish/       → Republier
5. POST /runtime/apps/{id}/deploy/           → Redéployer
```

---

## 🧪 **Tests et Exemples**

### Création Projet Complet
```bash
# 1. Créer le projet
curl -X POST http://localhost:8000/api/v1/studio/projects/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"CRM Client"}'

# 2. Créer schéma clients
curl -X POST http://localhost:8000/api/v1/studio/schemas/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project":"PROJECT_UUID",
    "table_name":"clients",
    "display_name":"Clients",
    "fields_config":[
      {"name":"nom","type":"string","label":"Nom","required":true},
      {"name":"email","type":"string","label":"Email","required":true,"unique":true}
    ]
  }'

# 3. Créer page
curl -X POST http://localhost:8000/api/v1/studio/pages/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project":"PROJECT_UUID",
    "name":"Liste Clients",
    "route":"/clients",
    "config":{"layout":"table"}
  }'

# 4. Ajouter composant tableau
curl -X POST http://localhost:8000/api/v1/studio/components/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "page":PAGE_ID,
    "component_type":"DataTable",
    "position":{"x":10,"y":10,"width":800,"height":400},
    "config":{"table_name":"clients"}
  }'

# 5. Publier
curl -X POST http://localhost:8000/api/v1/studio/projects/PROJECT_UUID/publish/ \
  -H "Authorization: Bearer TOKEN"
```

### Éditeur Interactif
```javascript
// JavaScript pour l'éditeur drag & drop
class StudioEditor {
    constructor(projectId) {
        this.projectId = projectId;
        this.canvas = document.getElementById('canvas');
        this.init();
    }

    async loadState() {
        const response = await fetch(`/api/v1/studio/editor/state/?project_id=${this.projectId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        this.state = await response.json();
        this.renderCanvas();
    }

    async addComponent(type, position) {
        const response = await fetch('/api/v1/studio/editor/add_component/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                project_id: this.projectId,
                component_type: type,
                position: position,
                config: this.getDefaultConfig(type)
            })
        });
        
        const result = await response.json();
        this.addComponentToCanvas(result.component_id, type, position);
    }

    async moveComponent(componentId, newPosition) {
        await fetch('/api/v1/studio/editor/move_component/', {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                component_id: componentId,
                position: newPosition
            })
        });
    }
}
```

---

## 📈 **Monitoring et Statistiques**

### Statistiques Projet
```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "statistics": {
    "tables_count": 5,
    "fields_count": 42,
    "pages_count": 8,
    "components_count": 24,
    "records_count": 1250,
    "last_modified": "2024-01-20T16:30:00Z",
    "storage_used_mb": 12.5,
    "api_calls_today": 450
  },
  "performance": {
    "load_time_ms": 120,
    "components_rendered": 24,
    "data_queries": 8,
    "cache_hit_rate": 0.85
  }
}
```

---

## 🚨 **Codes d'Erreur**

| Code | Message | Contexte |
|------|---------|----------|
| `STUDIO_001` | "Nom de projet requis" | Création projet |
| `STUDIO_002` | "Nom de projet déjà utilisé" | Doublon projet |
| `STUDIO_003` | "Nom de table invalide" | Validation schéma |
| `STUDIO_004` | "Type de champ non supporté" | Configuration champ |
| `STUDIO_005` | "Page d'accueil déjà existe" | Création page |
| `STUDIO_006` | "Composant non trouvé" | Modification composant |
| `STUDIO_007` | "Position invalide" | Déplacement composant |

---

*Documentation Studio API - Version 1.0*
