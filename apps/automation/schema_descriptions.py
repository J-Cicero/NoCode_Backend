"""
Descriptions détaillées pour la documentation Swagger/OpenAPI
Module: Automation (Workflows, Nodes, Edges, Intégrations)
"""

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes


# ============================================================================
# ⚡ WORKFLOWS - Descriptions
# ============================================================================

WORKFLOW_LIST_CREATE = {
    "summary": "⚡ Gérer les workflows d'automatisation",
    "description": """
    **Les workflows automatisent les processus métier avec un éditeur visuel.**
    
    ## 🎯 C'est quoi un Workflow ?
    
    Un workflow = Processus automatisé qui :
    - Se déclenche sur un événement (trigger)
    - Exécute des actions en séquence
    - Prend des décisions (conditions)
    - Appelle des APIs externes
    - Envoie des emails, SMS, etc.
    
    ## 🧩 Architecture Node/Edge (Graphe Visuel)
    
    Les workflows utilisent un **système de graphe** :
    - **Nodes (Nœuds)** : Actions individuelles
    - **Edges (Connexions)** : Flux entre les nodes
    - **Éditeur visuel** : Drag & drop avec coordonnées X/Y
    
    ## 📋 GET - Lister les workflows
    
    ### Retourne :
    - Tous les workflows du projet
    - Statut (ACTIVE, INACTIVE, ERROR)
    - Dernière exécution
    - Statistiques
    
    ### Filtres :
    - `?status=ACTIVE` : Workflows actifs
    - `?project_id=xxx` : Workflows d'un projet
    - `?search=nom` : Recherche par nom
    
    ## ➕ POST - Créer un workflow
    
    ### Données requises :
    - **name** : Nom du workflow
    - **description** : Description (optionnel)
    - **project_id** : Projet lié (optionnel)
    
    ### Ce qui est créé :
    - ✅ Workflow vide
    - ✅ Prêt à recevoir des nodes
    - ✅ Statut INACTIVE par défaut
    
    ## 💡 Exemple frontend :
    ```javascript
    // Créer un workflow
    const workflow = await fetch('/api/v1/automation/workflows/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: 'Notification nouveau client',
            description: 'Envoie un email de bienvenue aux nouveaux clients',
            project_id: projectId
        })
    }).then(r => r.json());
    
    console.log(workflow.id);  // UUID du workflow
    ```
    
    ## 🔑 Permissions :
    - **OWNER/ADMIN** : Créer, modifier, supprimer
    - **CLIENT** : Lecture seule
    """,
    "tags": ["⚡ Automation - Workflows"],
    "examples": [
        OpenApiExample(
            name="Workflow notification",
            value={
                "name": "Notification nouveau client",
                "description": "Email automatique aux nouveaux inscrits",
                "project_id": "123e4567-e89b-12d3-a456-426614174000"
            },
            request_only=True
        )
    ]
}

WORKFLOW_ACTIVATE = {
    "summary": "▶️ Activer un workflow",
    "description": """
    **Active un workflow pour qu'il s'exécute automatiquement.**
    
    ## 🎯 Activation
    
    Quand vous activez un workflow :
    - ✅ Les triggers sont enregistrés
    - ✅ Les webhooks sont créés
    - ✅ Le workflow surveille les événements
    - ✅ Exécutions automatiques démarrent
    
    ## 📥 POST - Activer
    
    ### Prérequis :
    - Au moins 1 node de type "trigger"
    - Toutes les configurations valides
    - Pas d'erreurs de validation
    
    ## ⚠️ Validation automatique :
    - Vérifie la présence d'un trigger
    - Vérifie les connexions entre nodes
    - Vérifie les configurations requises
    - Retourne les erreurs si invalide
    
    ## 💡 Exemple frontend :
    ```javascript
    // Activer le workflow
    const result = await fetch(`/api/v1/automation/workflows/${workflowId}/activate/`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json());
    
    if (result.status === 'ACTIVE') {
        console.log('Workflow activé avec succès');
    } else {
        console.error('Erreurs:', result.errors);
    }
    ```
    """,
    "tags": ["⚡ Automation - Workflows"]
}

WORKFLOW_DEACTIVATE = {
    "summary": "⏸️ Désactiver un workflow",
    "description": """
    **Désactive un workflow pour arrêter les exécutions automatiques.**
    
    ## 🎯 Désactivation
    
    Quand vous désactivez :
    - ⏸️ Les triggers sont désactivés
    - ⏸️ Les webhooks sont suspendus
    - ⏸️ Aucune nouvelle exécution
    - ✅ Historique conservé
    
    ## 💡 Cas d'usage :
    - Maintenance temporaire
    - Tests et modifications
    - Économiser des ressources
    
    ## 💡 Exemple frontend :
    ```javascript
    // Désactiver temporairement
    await fetch(`/api/v1/automation/workflows/${workflowId}/deactivate/`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
    });
    ```
    """,
    "tags": ["⚡ Automation - Workflows"]
}

WORKFLOW_TEST = {
    "summary": "🧪 Tester un workflow",
    "description": """
    **Exécute le workflow manuellement pour tester.**
    
    ## 🎯 Test manuel
    
    Permet de :
    - Tester avant activation
    - Déboguer les erreurs
    - Vérifier les résultats
    - Voir les logs en temps réel
    
    ## 📥 Données de test (optionnel)
    
    Vous pouvez fournir des données de test :
    ```json
    {
        "test_data": {
            "client": {
                "nom": "Test User",
                "email": "test@example.com"
            }
        }
    }
    ```
    
    ## 📤 Résultat
    
    Retourne :
    - Statut de l'exécution (SUCCESS, FAILED)
    - Résultat de chaque node
    - Logs détaillés
    - Temps d'exécution
    
    ## 💡 Exemple frontend :
    ```javascript
    // Tester avec données
    const result = await fetch(`/api/v1/automation/workflows/${workflowId}/test/`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            test_data: {
                client: { nom: 'Test', email: 'test@example.com' }
            }
        })
    }).then(r => r.json());
    
    console.log('Statut:', result.status);
    console.log('Logs:', result.logs);
    console.log('Durée:', result.duration, 'ms');
    ```
    """,
    "tags": ["⚡ Automation - Workflows"]
}


# ============================================================================
# 🔵 NODES - Descriptions
# ============================================================================

NODE_LIST_CREATE = {
    "summary": "🔵 Gérer les nodes (nœuds) du workflow",
    "description": """
    **Les nodes sont les actions individuelles du workflow.**
    
    ## 🎯 Types de Nodes disponibles
    
    ### 🎬 Triggers (Déclencheurs)
    - **webhook** : Déclenchement via URL
    - **schedule** : Planification (cron)
    - **event** : Événement système (create, update, delete)
    - **manual** : Déclenchement manuel
    
    ### ⚙️ Actions
    - **create_record** : Créer un enregistrement
    - **update_record** : Modifier un enregistrement
    - **delete_record** : Supprimer un enregistrement
    - **send_email** : Envoyer un email
    - **send_sms** : Envoyer un SMS
    - **http_request** : Appel API externe
    
    ### 🔀 Conditions
    - **if_condition** : Si/Alors/Sinon
    - **switch** : Branchement multiple
    - **filter** : Filtrer des données
    
    ### 🔧 Utilitaires
    - **delay** : Temporisation
    - **loop** : Boucle
    - **transform** : Transformer des données
    - **math** : Opérations mathématiques
    - **string** : Manipulation de texte
    - **json** : Manipulation JSON
    
    ## 📋 GET - Lister les nodes
    
    ### Retourne :
    - Tous les nodes du workflow
    - Position X/Y pour l'éditeur
    - Configuration de chaque node
    - Connexions (edges)
    
    ## ➕ POST - Créer un node
    
    ### Données requises :
    - **workflow_id** : ID du workflow
    - **node_type** : Type du node (voir liste ci-dessus)
    - **label** : Nom affiché
    - **position_x, position_y** : Coordonnées dans l'éditeur
    - **config** : Configuration JSON spécifique
    
    ### Format config (exemple email) :
    ```json
    {
        "to": "{{client.email}}",
        "subject": "Bienvenue {{client.nom}}",
        "template": "welcome_email",
        "variables": {
            "client_name": "{{client.nom}}"
        }
    }
    ```
    
    ### Format config (exemple condition) :
    ```json
    {
        "condition": "{{client.age}} > 18",
        "operator": "greater_than",
        "value": 18
    }
    ```
    
    ## 💡 Exemple frontend (Éditeur visuel) :
    ```javascript
    // Ajouter un node lors du drop
    const addNode = async (type, position) => {
        const node = await fetch(`/api/v1/automation/workflows/${workflowId}/nodes/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                node_type: type,
                label: getDefaultLabel(type),
                position_x: position.x,
                position_y: position.y,
                config: getDefaultConfig(type)
            })
        }).then(r => r.json());
        
        return node;
    };
    
    // Mettre à jour la position (drag)
    const updateNodePosition = async (nodeId, x, y) => {
        await fetch(`/api/v1/automation/nodes/${nodeId}/`, {
            method: 'PATCH',
            body: JSON.stringify({
                position_x: x,
                position_y: y
            })
        });
    };
    ```
    """,
    "tags": ["🔵 Automation - Nodes"]
}


# ============================================================================
# 🔗 EDGES - Descriptions
# ============================================================================

EDGE_LIST_CREATE = {
    "summary": "🔗 Gérer les connexions entre nodes",
    "description": """
    **Les edges connectent les nodes pour définir le flux du workflow.**
    
    ## 🎯 C'est quoi un Edge ?
    
    Un edge = Connexion entre 2 nodes :
    - **Source Node** : Node de départ
    - **Target Node** : Node d'arrivée
    - **Source Port** : Port de sortie (output, success, error)
    - **Target Port** : Port d'entrée (input)
    
    ## 📋 GET - Lister les connexions
    
    ### Retourne :
    - Toutes les connexions du workflow
    - Nodes source et target
    - Ports utilisés
    
    ## ➕ POST - Créer une connexion
    
    ### Données requises :
    - **workflow_id** : ID du workflow
    - **source_node_id** : ID du node source
    - **target_node_id** : ID du node cible
    - **source_port** : Port de sortie (défaut: "output")
    - **target_port** : Port d'entrée (défaut: "input")
    
    ### Exemple avec condition (if/else) :
    ```json
    {
        "source_node_id": "condition_node_123",
        "target_node_id": "action_yes_456",
        "source_port": "success",
        "target_port": "input"
    }
    ```
    
    ```json
    {
        "source_node_id": "condition_node_123",
        "target_node_id": "action_no_789",
        "source_port": "error",
        "target_port": "input"
    }
    ```
    
    ## 💡 Exemple frontend (Connexion drag) :
    ```javascript
    // Lors de la connexion de 2 nodes
    const connectNodes = async (sourceNodeId, targetNodeId, sourcPort = 'output', targetPort = 'input') => {
        const edge = await fetch(`/api/v1/automation/workflows/${workflowId}/edges/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                source_node_id: sourceNodeId,
                target_node_id: targetNodeId,
                source_port: sourcePort,
                target_port: targetPort
            })
        }).then(r => r.json());
        
        return edge;
    };
    
    // Supprimer une connexion
    const deleteEdge = async (edgeId) => {
        await fetch(`/api/v1/automation/edges/${edgeId}/`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
    };
    ```
    
    ## ⚠️ Validation :
    - Empêche les boucles infinies
    - Vérifie la compatibilité des ports
    - Limite les connexions multiples sur un port
    """,
    "tags": ["🔗 Automation - Edges"]
}


# ============================================================================
# 🔌 INTÉGRATIONS - Descriptions
# ============================================================================

INTEGRATION_LIST_CREATE = {
    "summary": "🔌 Gérer les intégrations externes",
    "description": """
    **Les intégrations connectent vos workflows à des services externes.**
    
    ## 🎯 Intégrations disponibles
    
    ### 📧 Communication
    - **SendGrid** : Envoi d'emails
    - **Twilio** : SMS et appels
    - **Slack** : Notifications Slack
    - **Discord** : Notifications Discord
    
    ### 💳 Paiement
    - **Stripe** : Paiements en ligne
    - **PayPal** : Paiements PayPal
    
    ### 📊 CRM & Marketing
    - **Salesforce** : CRM
    - **HubSpot** : Marketing automation
    - **Mailchimp** : Email marketing
    
    ### 💾 Stockage
    - **AWS S3** : Stockage fichiers
    - **Google Drive** : Drive
    - **Dropbox** : Dropbox
    
    ### 🔧 Développement
    - **GitHub** : Gestion de code
    - **GitLab** : GitLab
    - **Jira** : Gestion de projets
    
    ## 📋 GET - Lister les intégrations
    
    ### Retourne :
    - Toutes vos intégrations configurées
    - Statut de connexion
    - Dernière utilisation
    
    ## ➕ POST - Ajouter une intégration
    
    ### Données requises :
    - **name** : Nom de l'intégration
    - **service_type** : Type de service
    - **credentials** : Identifiants (cryptés)
    
    ### Exemple SendGrid :
    ```json
    {
        "name": "Mon compte SendGrid",
        "service_type": "sendgrid",
        "credentials": {
            "api_key": "SG.xxxxxxxxxxxxx"
        },
        "config": {
            "from_email": "noreply@monapp.com",
            "from_name": "Mon Application"
        }
    }
    ```
    
    ### Exemple Stripe :
    ```json
    {
        "name": "Stripe Production",
        "service_type": "stripe",
        "credentials": {
            "secret_key": "sk_live_xxxxx",
            "publishable_key": "pk_live_xxxxx"
        }
    }
    ```
    
    ## 💡 Exemple frontend :
    ```javascript
    // Ajouter une intégration
    const integration = await fetch('/api/v1/automation/integrations/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: 'SendGrid Principal',
            service_type: 'sendgrid',
            credentials: {
                api_key: 'SG.xxxxxx'
            }
        })
    }).then(r => r.json());
    
    // Utiliser dans un workflow
    // Les intégrations apparaissent automatiquement dans les nodes compatibles
    ```
    
    ## 🔐 Sécurité :
    - Credentials cryptés en base
    - Jamais exposés dans les réponses API
    - Rotation des clés possible
    """,
    "tags": ["🔌 Automation - Intégrations"]
}


# ============================================================================
# 📊 EXÉCUTIONS - Descriptions
# ============================================================================

EXECUTION_LIST = {
    "summary": "📊 Historique des exécutions",
    "description": """
    **Visualisez l'historique de toutes les exécutions de workflows.**
    
    ## 🎯 Que contient un log d'exécution ?
    
    Chaque exécution enregistre :
    - **Statut** : SUCCESS, FAILED, RUNNING, CANCELLED
    - **Durée** : Temps d'exécution total
    - **Trigger** : Événement déclencheur
    - **Logs** : Logs détaillés de chaque node
    - **Erreurs** : Stack trace si échec
    - **Résultat** : Données finales
    
    ## 📋 GET - Lister les exécutions
    
    ### Filtres disponibles :
    - `?workflow_id=xxx` : Exécutions d'un workflow
    - `?status=SUCCESS` : Exécutions réussies
    - `?status=FAILED` : Exécutions échouées
    - `?date_from=2025-01-01` : Depuis une date
    - `?date_to=2025-01-31` : Jusqu'à une date
    
    ### Tri :
    - `?ordering=-created_at` : Plus récentes d'abord
    - `?ordering=duration` : Par durée
    
    ## 💡 Exemple frontend :
    ```javascript
    // Récupérer l'historique
    const executions = await fetch(`/api/v1/automation/executions/?workflow_id=${workflowId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json());
    
    // Afficher les logs d'une exécution
    const execution = executions.results[0];
    console.log('Statut:', execution.status);
    console.log('Durée:', execution.duration, 'ms');
    console.log('Logs:', execution.logs);
    
    // Voir les erreurs
    if (execution.status === 'FAILED') {
        console.error('Erreur:', execution.error_message);
        console.log('Node en échec:', execution.failed_node);
    }
    ```
    
    ## 📈 Statistiques
    
    Utilisez les exécutions pour :
    - Calculer le taux de succès
    - Identifier les goulots d'étranglement
    - Optimiser les performances
    - Déboguer les workflows
    """,
    "tags": ["📊 Automation - Exécutions"]
}
