"""
Descriptions détaillées pour la documentation Swagger/OpenAPI
Module: Runtime (Génération et Déploiement d'applications)
"""

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes


# ============================================================================
# 🚀 APPLICATIONS GÉNÉRÉES - Descriptions
# ============================================================================

GENERATED_APP_LIST_CREATE = {
    "summary": "🚀 Gérer les applications générées",
    "description": """
    **Les applications générées sont des apps Django complètes créées automatiquement.**
    
    ## 🎯 C'est quoi une Application Générée ?
    
    À partir d'un projet Studio, le système génère :
    - **Code Django complet** : models.py, views.py, serializers.py, etc.
    - **API REST** : Endpoints CRUD automatiques
    - **Base de données** : PostgreSQL dédiée
    - **Conteneur Docker** : Application isolée
    - **Interface Admin** : Django Admin configuré
    
    ## 📋 GET - Lister les applications
    
    ### Retourne :
    - Toutes vos applications générées
    - Statut de déploiement
    - URLs d'accès
    - Statistiques
    
    ### Filtres :
    - `?project_id=xxx` : Apps d'un projet
    - `?deployment_target=docker` : Apps Docker
    - `?status=deployed` : Apps déployées
    
    ## ➕ POST - Générer une application
    
    ### Données requises :
    - **project_id** : ID du projet Studio
    - **name** : Nom de l'application
    - **deployment_target** : Cible de déploiement
    
    ### Choix deployment_target :
    - **local** : Fichiers uniquement (développement)
    - **docker** : Conteneur Docker (recommandé)
    - **staging** : Environnement de test (Docker)
    - **production** : Production (Kubernetes)
    
    ### Ce qui est généré automatiquement :
    
    #### 1. Structure Django :
    ```
    generated_apps/app_{project_id}/
    ├── models.py          # Modèles depuis tables Studio
    ├── serializers.py     # Serializers DRF automatiques
    ├── views.py           # ViewSets CRUD complets
    ├── urls.py            # Routes API
    ├── admin.py           # Interface admin Django
    ├── apps.py            # Configuration app
    ├── __init__.py
    └── migrations/        # Migrations DB
    ```
    
    #### 2. Déploiement Docker (si docker) :
    ```
    ├── Dockerfile         # Image Docker personnalisée
    ├── docker-compose.yml # Orchestration (web + db)
    ├── entrypoint.sh      # Script de démarrage
    ├── requirements.txt   # Dépendances Python
    ├── static/            # Fichiers statiques
    ├── media/             # Fichiers uploadés
    └── logs/              # Logs applicatifs
    ```
    
    ## 💡 Exemple frontend :
    ```javascript
    // Générer une application
    const app = await fetch('/api/v1/runtime/apps/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            project_id: projectId,
            name: 'Mon Application CRM',
            deployment_target: 'docker'
        })
    }).then(r => r.json());
    
    console.log('Application créée:', app.id);
    console.log('Statut:', app.status);
    ```
    
    ## 📤 Réponse :
    ```json
    {
        "id": "app_123xyz",
        "name": "Mon Application CRM",
        "project": {...},
        "status": "generated",
        "deployment_target": "docker",
        "created_at": "2025-12-31T10:00:00Z"
    }
    ```
    """,
    "tags": ["🚀 Runtime - Applications"]
}

GENERATED_APP_DETAIL = {
    "summary": "📱 Détails d'une application",
    "description": """
    **Récupère les détails complets d'une application générée.**
    
    ## 📖 GET - Voir l'application
    
    ### Retourne :
    - Informations générales
    - URLs d'accès (API, Admin)
    - Statut de déploiement
    - Configuration Docker
    - Logs récents
    
    ## ✏️ PATCH - Modifier l'application
    
    ### Vous pouvez modifier :
    - Nom de l'application
    - Configuration
    - Cible de déploiement
    
    ## 🗑️ DELETE - Supprimer l'application
    
    ### ⚠️ Attention :
    - Suppression définitive
    - Arrête les conteneurs Docker
    - Supprime les données
    - Nécessite confirmation
    
    ## 💡 Exemple frontend :
    ```javascript
    // Récupérer les détails
    const app = await fetch(`/api/v1/runtime/apps/${appId}/`, {
        headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json());
    
    console.log('URLs:', {
        api: app.api_base_url,
        admin: app.admin_url,
        docs: app.api_base_url + 'docs/'
    });
    ```
    """,
    "tags": ["🚀 Runtime - Applications"]
}

GENERATED_APP_DEPLOY = {
    "summary": "🐳 Déployer l'application",
    "description": """
    **Déploie l'application dans son environnement cible.**
    
    ## 🎯 Que fait le déploiement ?
    
    ### Pour Docker (recommandé) :
    
    1. **Génération des fichiers**
       - Crée Dockerfile, docker-compose.yml
       - Configure l'entrypoint
       - Prépare requirements.txt
    
    2. **Build de l'image Docker**
       - Image Python 3.11
       - Installation des dépendances
       - Configuration PostgreSQL
    
    3. **Démarrage des conteneurs**
       - Conteneur web (Django + Gunicorn)
       - Conteneur PostgreSQL dédié
       - Réseau isolé
       - Volumes pour data/logs
    
    4. **Configuration réseau**
       - Port dynamique (8000-9000)
       - Base sur hash du project_id
       - Pas de conflits
    
    5. **Initialisation**
       - Migrations automatiques
       - Collecte des statiques
       - Création superuser
    
    ## 📥 POST - Déployer
    
    ### Pas de données requises (utilise la config)
    
    ## 📤 Réponse :
    ```json
    {
        "status": "success",
        "message": "Application déployée avec succès",
        "deployment": {
            "target": "docker",
            "container_name": "nocode_app_123xyz",
            "port": 8456,
            "urls": {
                "api": "http://localhost:8456/api/v1/",
                "admin": "http://localhost:8456/admin/",
                "docs": "http://localhost:8456/api/docs/"
            }
        }
    }
    ```
    
    ## ⏱️ Durée :
    - **Premier déploiement** : 2-5 minutes (build image)
    - **Redéploiements** : 30-60 secondes (cache)
    
    ## 💡 Exemple frontend :
    ```javascript
    // Déployer l'application
    const deploy = async (appId) => {
        // Afficher loader
        setLoading(true);
        
        const result = await fetch(`/api/v1/runtime/apps/${appId}/deploy/`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        }).then(r => r.json());
        
        if (result.status === 'success') {
            // Rediriger vers l'app
            window.open(result.deployment.urls.api, '_blank');
        } else {
            alert('Erreur: ' + result.message);
        }
        
        setLoading(false);
    };
    ```
    
    ## 🔄 Redéploiement :
    - Appeler le même endpoint pour redéployer
    - Les conteneurs sont recréés
    - Les données sont préservées
    """,
    "tags": ["🚀 Runtime - Applications"]
}

GENERATED_APP_STATUS = {
    "summary": "📊 Statut de l'application",
    "description": """
    **Vérifie le statut de déploiement et la santé de l'application.**
    
    ## 📊 GET - Statut
    
    ### Retourne :
    
    #### Pour applications Docker :
    ```json
    {
        "status": "running",
        "deployment": {
            "target": "docker",
            "container": {
                "Service": "web",
                "State": "running",
                "Health": "healthy"
            },
            "database": {
                "State": "running",
                "Health": "healthy"
            }
        },
        "urls": {
            "api": "http://localhost:8456/api/v1/",
            "admin": "http://localhost:8456/admin/"
        },
        "uptime": "2h 15m",
        "last_deployment": "2025-12-31T10:00:00Z"
    }
    ```
    
    ### Statuts possibles :
    - **running** : Application en ligne
    - **stopped** : Application arrêtée
    - **error** : Erreur de déploiement
    - **deploying** : Déploiement en cours
    - **not_deployed** : Jamais déployée
    
    ## 💡 Polling automatique :
    ```javascript
    // Vérifier le statut toutes les 5 secondes
    const checkStatus = async (appId) => {
        const interval = setInterval(async () => {
            const status = await fetch(`/api/v1/runtime/apps/${appId}/status/`, {
                headers: { 'Authorization': `Bearer ${token}` }
            }).then(r => r.json());
            
            updateUI(status);
            
            // Arrêter si running ou error
            if (['running', 'error'].includes(status.status)) {
                clearInterval(interval);
            }
        }, 5000);
    };
    ```
    """,
    "tags": ["🚀 Runtime - Applications"]
}

GENERATED_APP_LOGS = {
    "summary": "📄 Logs de l'application",
    "description": """
    **Récupère les logs de l'application déployée.**
    
    ## 📄 GET - Voir les logs
    
    ### Paramètres query :
    - `?lines=100` : Nombre de lignes (défaut: 100)
    - `?follow=true` : Stream en temps réel (WebSocket)
    
    ### Retourne :
    ```json
    {
        "logs": [
            "2025-12-31 10:00:00 [INFO] Application démarrée",
            "2025-12-31 10:00:01 [INFO] Migrations appliquées",
            "2025-12-31 10:00:02 [INFO] Serveur écoute sur 0.0.0.0:8000",
            "2025-12-31 10:00:15 [INFO] GET /api/v1/clients/ 200",
            "2025-12-31 10:00:20 [ERROR] Erreur de connexion DB",
            "..."
        ],
        "total_lines": 245,
        "last_update": "2025-12-31T10:00:20Z"
    }
    ```
    
    ## 🔍 Filtrage des logs :
    ```javascript
    // Récupérer les logs
    const logs = await fetch(`/api/v1/runtime/apps/${appId}/logs/?lines=200`, {
        headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json());
    
    // Filtrer les erreurs
    const errors = logs.logs.filter(line => line.includes('[ERROR]'));
    console.error('Erreurs:', errors);
    
    // Filtrer par date
    const recent = logs.logs.filter(line => 
        line.includes('2025-12-31 10:')
    );
    ```
    
    ## 💡 Viewer en temps réel :
    ```javascript
    // WebSocket pour logs en temps réel
    const ws = new WebSocket(`ws://localhost:8000/ws/apps/${appId}/logs/`);
    
    ws.onmessage = (event) => {
        const logLine = event.data;
        appendToLogViewer(logLine);
    };
    ```
    """,
    "tags": ["🚀 Runtime - Applications"]
}

GENERATED_APP_STOP = {
    "summary": "⏹️ Arrêter l'application",
    "description": """
    **Arrête l'application déployée sans la supprimer.**
    
    ## ⏹️ POST - Arrêter
    
    ### Que fait cet action ?
    - Arrête les conteneurs Docker
    - Libère le port
    - Conserve les données
    - Conserve la configuration
    
    ### Différence avec DELETE :
    - **STOP** : Temporaire, redémarrage possible
    - **DELETE** : Définitif, suppression totale
    
    ## 💡 Cas d'usage :
    - Économiser des ressources
    - Maintenance planifiée
    - Tests terminés
    - Application inactive
    
    ## 💡 Exemple frontend :
    ```javascript
    // Arrêter l'application
    await fetch(`/api/v1/runtime/apps/${appId}/stop/`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
    });
    
    // Redémarrer plus tard
    await fetch(`/api/v1/runtime/apps/${appId}/deploy/`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
    });
    ```
    """,
    "tags": ["🚀 Runtime - Applications"]
}

GENERATED_APP_RESTART = {
    "summary": "🔄 Redémarrer l'application",
    "description": """
    **Redémarre l'application déployée.**
    
    ## 🔄 POST - Redémarrer
    
    ### Que fait cette action ?
    - Arrête les conteneurs
    - Redémarre les conteneurs
    - Applique les nouvelles migrations (si présentes)
    - Recharge la configuration
    
    ## 💡 Cas d'usage :
    - Appliquer des changements de config
    - Résoudre des problèmes de mémoire
    - Appliquer des mises à jour
    
    ## ⏱️ Temps d'arrêt :
    - Environ 10-30 secondes
    - Les requêtes en cours sont perdues
    
    ## 💡 Exemple frontend :
    ```javascript
    // Redémarrer l'application
    const restart = async (appId) => {
        const result = await fetch(`/api/v1/runtime/apps/${appId}/restart/`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        }).then(r => r.json());
        
        if (result.success) {
            // Attendre que l'app soit de nouveau running
            await waitForStatus(appId, 'running');
            alert('Application redémarrée');
        }
    };
    ```
    """,
    "tags": ["🚀 Runtime - Applications"]
}
