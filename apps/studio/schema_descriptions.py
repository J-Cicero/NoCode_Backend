"""
Descriptions détaillées pour la documentation Swagger/OpenAPI
Module: Studio (Projets, Tables, Pages, Composants)
"""

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes


# ============================================================================
# 📁 PROJETS - Descriptions
# ============================================================================

PROJECT_LIST_CREATE = {
    "summary": "📁 Liste et création de projets NoCode",
    "description": """
    **Gère les projets NoCode de votre organisation.**
    
    ## 📋 GET - Lister les projets
    
    ### Retourne :
    - Tous les projets de votre organisation
    - Projets partagés avec vous
    - Informations complètes (tables, pages, workflows)
    
    ### Filtres disponibles :
    - `?status=active` : Projets actifs uniquement
    - `?status=archived` : Projets archivés
    - `?search=nom` : Recherche par nom
    - `?created_by=user_id` : Projets créés par un utilisateur
    
    ## ➕ POST - Créer un projet
    
    ### C'est quoi un projet ?
    Un projet NoCode contient :
    - **Tables** : Schémas de données (modèles)
    - **Pages** : Interfaces utilisateur (drag & drop)
    - **Workflows** : Automatisations (Node/Edge)
    - **App générée** : Application Django complète
    
    ### Données requises :
    - **name** : Nom du projet
    - **description** : Description (optionnel)
    
    ### Ce qui est créé automatiquement :
    - ✅ Schéma PostgreSQL dédié
    - ✅ Dossier de travail
    - ✅ Configuration par défaut
    - ✅ Tracking ID unique
    
    ## 💡 Exemple frontend :
    ```javascript
    // Créer un nouveau projet
    const project = await fetch('/api/v1/studio/projects/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: 'Gestion Clients',
            description: 'Application de gestion de la relation client'
        })
    }).then(r => r.json());
    
    console.log(project.id);  // UUID du projet
    console.log(project.tracking_id);  // Pour analytics
    ```
    
    ## 🔑 Permissions :
    - **OWNER/ADMIN** : Peut créer des projets
    - **CLIENT** : Lecture seule (sauf si collaborateur)
    """,
    "tags": ["📁 Studio - Projets"],
    "examples": [
        OpenApiExample(
            name="Création projet CRM",
            value={
                "name": "CRM Entreprise",
                "description": "Gestion complète des clients et opportunités"
            },
            request_only=True
        )
    ]
}

PROJECT_DETAIL = {
    "summary": "📁 Détails d'un projet",
    "description": """
    **Récupère, modifie ou supprime un projet spécifique.**
    
    ## 📖 GET - Voir le projet
    
    ### Retourne :
    - Informations du projet
    - Liste des tables (DataSchema)
    - Liste des pages
    - Statistiques
    - Membres ayant accès
    
    ## ✏️ PUT/PATCH - Modifier le projet
    
    ### Vous pouvez modifier :
    - Nom du projet
    - Description
    - Statut (active, archived)
    - Configuration (settings JSON)
    
    ## 🗑️ DELETE - Supprimer le projet
    
    ### ⚠️ Attention :
    - Suppression définitive
    - Supprime aussi : tables, pages, workflows, app générée
    - Nécessite confirmation (ajouter `?confirm=true`)
    
    ## 💡 Exemple frontend :
    ```javascript
    // Récupérer un projet
    const project = await fetch(`/api/v1/studio/projects/${projectId}/`, {
        headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json());
    
    // Modifier le projet
    await fetch(`/api/v1/studio/projects/${projectId}/`, {
        method: 'PATCH',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: 'Nouveau nom',
            status: 'archived'
        })
    });
    
    // Supprimer le projet
    await fetch(`/api/v1/studio/projects/${projectId}/?confirm=true`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
    });
    ```
    """,
    "tags": ["📁 Studio - Projets"]
}

PROJECT_GENERATE = {
    "summary": "⚡ Générer l'application",
    "description": """
    **Génère automatiquement le code Django de votre application.**
    
    ## 🎯 Que fait cette action ?
    
    ### Génération automatique de :
    1. **models.py** : Modèles Django depuis vos tables
    2. **serializers.py** : Serializers DRF automatiques
    3. **views.py** : ViewSets avec CRUD complet
    4. **urls.py** : Routes API REST
    5. **admin.py** : Interface Django Admin
    6. **migrations/** : Migrations de base de données
    
    ## 📦 Structure générée :
    ```
    generated_apps/
    └── app_{project_id}/
        ├── models.py
        ├── serializers.py
        ├── views.py
        ├── urls.py
        ├── admin.py
        ├── apps.py
        └── migrations/
    ```
    
    ## 🔄 Processus :
    1. Analyse de vos tables (DataSchema)
    2. Génération du code Python
    3. Écriture des fichiers
    4. Création de l'app Django
    5. Prêt pour déploiement
    
    ## 💡 Exemple frontend :
    ```javascript
    // Générer l'application
    const result = await fetch(`/api/v1/studio/projects/${projectId}/generate/`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json());
    
    if (result.success) {
        console.log('Code généré avec succès');
        console.log('Fichiers:', result.files);
    }
    ```
    
    ## ⚠️ Notes :
    - Nécessite au moins 1 table définie
    - Écrase les fichiers existants
    - Ne modifie pas le code personnalisé (safe)
    """,
    "tags": ["📁 Studio - Projets"]
}


# ============================================================================
# 📊 TABLES (DataSchema) - Descriptions
# ============================================================================

DATASCHEMA_LIST_CREATE = {
    "summary": "📊 Gérer les tables de données",
    "description": """
    **Les tables sont les modèles de données de votre application.**
    
    ## 🎯 C'est quoi une Table ?
    
    Une table définit :
    - **Nom** : Nom de la table (ex: clients, produits)
    - **Champs** : Liste des colonnes avec leur type
    - **Relations** : Liens vers d'autres tables
    - **Validations** : Règles de validation
    
    ## 📋 GET - Lister les tables
    
    ### Retourne :
    - Toutes les tables du projet
    - Configuration des champs (fields_config)
    - Statistiques (nombre d'enregistrements)
    
    ## ➕ POST - Créer une table
    
    ### Données requises :
    - **table_name** : Nom technique (snake_case)
    - **display_name** : Nom affiché
    - **fields_config** : Configuration des champs (JSON)
    
    ### Format fields_config :
    ```json
    [
        {
            "name": "nom",
            "type": "string",
            "required": true,
            "max_length": 100
        },
        {
            "name": "email",
            "type": "email",
            "required": true,
            "unique": true
        },
        {
            "name": "age",
            "type": "integer",
            "min_value": 0,
            "max_value": 150
        },
        {
            "name": "date_inscription",
            "type": "datetime",
            "auto_now_add": true
        }
    ]
    ```
    
    ### Types de champs supportés :
    - **string** : Texte court
    - **text** : Texte long
    - **integer** : Nombre entier
    - **decimal** : Nombre décimal
    - **boolean** : Vrai/Faux
    - **date** : Date
    - **datetime** : Date + Heure
    - **email** : Email (avec validation)
    - **url** : URL (avec validation)
    - **json** : Données JSON
    - **file** : Fichier uploadé
    - **image** : Image
    - **foreign_key** : Relation vers autre table
    - **many_to_many** : Relation multiple
    
    ## 💡 Exemple frontend :
    ```javascript
    // Créer une table Clients
    const table = await fetch(`/api/v1/studio/projects/${projectId}/schemas/`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            table_name: 'clients',
            display_name: 'Clients',
            description: 'Table des clients de l\'entreprise',
            fields_config: [
                { name: 'nom', type: 'string', required: true },
                { name: 'email', type: 'email', required: true, unique: true },
                { name: 'telephone', type: 'string' },
                { name: 'date_creation', type: 'datetime', auto_now_add: true }
            ]
        })
    }).then(r => r.json());
    ```
    
    ## 🔄 Génération automatique :
    Cette table devient un modèle Django :
    ```python
    class Client(BaseModel):
        nom = models.CharField(max_length=100)
        email = models.EmailField(unique=True)
        telephone = models.CharField(max_length=20, blank=True)
        date_creation = models.DateTimeField(auto_now_add=True)
    ```
    """,
    "tags": ["📊 Studio - Tables"]
}


# ============================================================================
# 🎨 PAGES - Descriptions
# ============================================================================

PAGE_LIST_CREATE = {
    "summary": "🎨 Gérer les pages de l'interface",
    "description": """
    **Les pages définissent l'interface utilisateur de votre application.**
    
    ## 🎯 C'est quoi une Page ?
    
    Une page contient :
    - **Nom et route** : URL de la page (ex: /clients, /dashboard)
    - **Composants** : Éléments visuels (tableaux, formulaires, graphiques)
    - **Layout** : Disposition des composants
    - **Configuration** : Styles, permissions, etc.
    
    ## 📋 GET - Lister les pages
    
    ### Retourne :
    - Toutes les pages du projet
    - Configuration complète
    - Composants inclus
    
    ## ➕ POST - Créer une page
    
    ### Données requises :
    - **name** : Nom de la page
    - **route** : Chemin URL (ex: /clients, /dashboard)
    - **config** : Configuration JSON (optionnel)
    
    ### Exemple config :
    ```json
    {
        "layout": "grid",
        "columns": 12,
        "theme": "light",
        "permissions": ["authenticated"],
        "meta": {
            "title": "Liste des Clients",
            "description": "Gérer tous vos clients"
        }
    }
    ```
    
    ## 💡 Exemple frontend :
    ```javascript
    // Créer une page
    const page = await fetch(`/api/v1/studio/projects/${projectId}/pages/`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: 'Liste Clients',
            route: '/clients',
            config: {
                layout: 'grid',
                theme: 'light'
            }
        })
    }).then(r => r.json());
    
    console.log(page.id);  // UUID de la page
    ```
    """,
    "tags": ["🎨 Studio - Pages"]
}


# ============================================================================
# 🧩 COMPOSANTS - Descriptions
# ============================================================================

COMPONENT_LIST = {
    "summary": "🧩 Liste des composants disponibles",
    "description": """
    **Les composants sont les briques visuelles de votre application.**
    
    ## 🎯 Types de composants :
    
    ### 📊 Affichage de données
    - **DataTable** : Tableau avec tri, filtre, pagination
    - **Card** : Carte d'information
    - **List** : Liste d'éléments
    - **DetailView** : Vue détaillée d'un élément
    
    ### 📝 Formulaires
    - **Form** : Formulaire complet
    - **Input** : Champ de saisie
    - **Select** : Liste déroulante
    - **Checkbox** : Case à cocher
    - **DatePicker** : Sélecteur de date
    - **FileUpload** : Upload de fichiers
    
    ### 📈 Graphiques
    - **LineChart** : Graphique en ligne
    - **BarChart** : Graphique en barres
    - **PieChart** : Graphique circulaire
    - **AreaChart** : Graphique en aires
    
    ### 🎛️ Navigation
    - **Menu** : Menu de navigation
    - **Breadcrumb** : Fil d'Ariane
    - **Tabs** : Onglets
    - **Sidebar** : Barre latérale
    
    ### 🎨 Layout
    - **Container** : Conteneur flexible
    - **Grid** : Grille responsive
    - **Row/Column** : Lignes et colonnes
    - **Divider** : Séparateur
    
    ## 📋 GET - Lister les composants
    
    ### Retourne :
    - Tous les composants disponibles
    - Configuration par défaut
    - Props acceptées
    - Exemples d'utilisation
    
    ## 💡 Exemple frontend :
    ```javascript
    // Récupérer tous les composants
    const components = await fetch('/api/v1/studio/components/', {
        headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json());
    
    // Filtrer les composants de type "form"
    const formComponents = components.filter(c => c.category === 'form');
    ```
    """,
    "tags": ["🧩 Studio - Composants"]
}

COMPONENT_INSTANCE_CREATE = {
    "summary": "➕ Ajouter un composant à une page",
    "description": """
    **Place un composant sur une page avec drag & drop.**
    
    ## 🎯 C'est quoi une Instance ?
    
    Une instance = Un composant placé sur une page avec :
    - **Position** : Coordonnées X/Y ou slot
    - **Configuration** : Props spécifiques
    - **Données** : Liaison aux tables
    - **Events** : Actions (click, submit, etc.)
    
    ## ➕ POST - Ajouter un composant
    
    ### Données requises :
    - **page_id** : ID de la page cible
    - **component_id** : ID du composant à utiliser
    - **position** : Positionnement (JSON)
    - **config** : Configuration spécifique (JSON)
    
    ### Format position :
    ```json
    {
        "x": 100,
        "y": 200,
        "width": 400,
        "height": 300,
        "slot": "content"
    }
    ```
    
    ### Format config (exemple DataTable) :
    ```json
    {
        "dataSource": "clients",
        "columns": [
            { "field": "nom", "header": "Nom", "sortable": true },
            { "field": "email", "header": "Email" },
            { "field": "telephone", "header": "Téléphone" }
        ],
        "pagination": true,
        "pageSize": 10,
        "actions": ["view", "edit", "delete"]
    }
    ```
    
    ## 💡 Exemple frontend (Drag & Drop) :
    ```javascript
    // Lors du drop d'un composant
    const onDrop = async (componentId, position) => {
        const instance = await fetch(`/api/v1/studio/pages/${pageId}/instances/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                component_id: componentId,
                position: {
                    x: position.x,
                    y: position.y,
                    width: 400,
                    height: 300
                },
                config: {
                    // Configuration par défaut du composant
                }
            })
        }).then(r => r.json());
        
        // Ajouter l'instance au canvas
        addToCanvas(instance);
    };
    ```
    
    ## 🔄 Mise à jour de position :
    ```javascript
    // Lors du déplacement
    await fetch(`/api/v1/studio/component-instances/${instanceId}/`, {
        method: 'PATCH',
        body: JSON.stringify({
            position: { x: newX, y: newY }
        })
    });
    ```
    """,
    "tags": ["🧩 Studio - Composants"]
}
