# 🤖 Automation API - Workflows et Intégrations

## 📋 Vue d'ensemble

Le module Automation permet de **créer des workflows intelligents** et d'intégrer des services externes. Il offre un système de graphes orientés avec des nœuds et des arêtes pour automatiser des processus complexes dans les applications NoCode.

**Base URL :** `/api/v1/automation/`

---

## 🔄 **Workflows**

### GET `/workflows/`
**Lister les workflows de l'utilisateur**

**Headers :**
```http
Authorization: Bearer <access_token>
```

**Réponse (200) :**
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "tracking_id": "workflow-uuid-here",
      "name": "Processus d'Onboarding Client",
      "description": "Workflow automatique pour l'intégration des nouveaux clients",
      "project": {
        "tracking_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Gestion Client"
      },
      "status": "active",
      "trigger_type": "webhook",
      "nodes_count": 8,
      "edges_count": 7,
      "executions_count": 245,
      "success_rate": 0.95,
      "last_executed": "2024-01-20T14:30:00Z",
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-15T16:20:00Z"
    },
    {
      "id": 2,
      "tracking_id": "workflow-uuid-2",
      "name": "Notification Email Quotidienne",
      "description": "Envoie un rapport quotidien par email",
      "project": {
        "tracking_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Gestion Client"
      },
      "status": "scheduled",
      "trigger_type": "cron",
      "nodes_count": 4,
      "edges_count": 3,
      "executions_count": 30,
      "success_rate": 1.0,
      "last_executed": "2024-01-20T08:00:00Z",
      "created_at": "2024-01-10T09:00:00Z",
      "updated_at": "2024-01-10T09:00:00Z"
    }
  ]
}
```

**Paramètres de requête :**
- `project` (optional) : Filtrer par projet UUID
- `status` (optional) : Filtrer par statut (active/inactive/draft/scheduled)
- `trigger_type` (optional) : Filtrer par type de déclencheur

---

### POST `/workflows/`
**Créer un nouveau workflow**

**Requête :**
```json
{
  "name": "Workflow de Validation Commande",
  "description": "Valide automatiquement les nouvelles commandes",
  "project": "550e8400-e29b-41d4-a716-446655440000",
  "trigger_type": "webhook",
  "trigger_config": {
    "event": "order.created",
    "endpoint": "/webhooks/order-validation"
  },
  "settings": {
    "timeout_seconds": 300,
    "retry_on_failure": true,
    "max_retries": 3,
    "notifications": {
      "on_success": false,
      "on_failure": true,
      "email": "admin@company.com"
    }
  }
}
```

**Réponse (201) :**
```json
{
  "id": 6,
  "tracking_id": "workflow-uuid-new",
  "name": "Workflow de Validation Commande",
  "description": "Valide automatiquement les nouvelles commandes",
  "project": {
    "tracking_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Gestion Client"
  },
  "status": "draft",
  "trigger_type": "webhook",
  "trigger_config": {
    "event": "order.created",
    "endpoint": "/webhooks/order-validation",
    "webhook_url": "https://api.nocode-platform.com/api/v1/automation/workflows/workflow-uuid-new/trigger/"
  },
  "nodes_count": 0,
  "edges_count": 0,
  "created_at": "2024-01-20T15:00:00Z",
  "settings": {
    "timeout_seconds": 300,
    "retry_on_failure": true,
    "max_retries": 3
  }
}
```

**Types de déclencheurs :**
- `webhook` : Déclenché par appel HTTP
- `cron` : Déclenché par planning CRON
- `manual` : Déclenché manuellement
- `event` : Déclenché par événement système
- `api_call` : Déclenché par appel API

---

### GET `/workflows/{workflow_id}/`
**Détails d'un workflow spécifique**

**Réponse (200) :**
```json
{
  "id": 1,
  "tracking_id": "workflow-uuid-here",
  "name": "Processus d'Onboarding Client",
  "description": "Workflow automatique pour l'intégration des nouveaux clients",
  "project": {
    "tracking_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Gestion Client"
  },
  "status": "active",
  "trigger_type": "webhook",
  "trigger_config": {
    "event": "client.created",
    "endpoint": "/webhooks/client-onboarding",
    "webhook_url": "https://api.nocode-platform.com/api/v1/automation/workflows/workflow-uuid-here/trigger/"
  },
  "nodes_count": 8,
  "edges_count": 7,
  "executions_count": 245,
  "success_rate": 0.95,
  "last_executed": "2024-01-20T14:30:00Z",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-15T16:20:00Z",
  "settings": {
    "timeout_seconds": 300,
    "retry_on_failure": true,
    "max_retries": 3,
    "notifications": {
      "on_success": false,
      "on_failure": true,
      "email": "admin@company.com"
    }
  },
  "statistics": {
    "executions_today": 12,
    "executions_this_week": 85,
    "average_execution_time_seconds": 45,
    "last_execution_status": "success",
    "last_execution_at": "2024-01-20T14:30:00Z"
  }
}
```

---

### PUT `/workflows/{workflow_id}/`
**Mettre à jour un workflow**

**Requête :**
```json
{
  "name": "Processus d'Onboarding Client v2",
  "description": "Workflow amélioré pour l'intégration des nouveaux clients",
  "status": "active",
  "settings": {
    "timeout_seconds": 600,
    "retry_on_failure": true,
    "max_retries": 5
  }
}
```

**Réponse (200) :**
```json
{
  "id": 1,
  "name": "Processus d'Onboarding Client v2",
  "description": "Workflow amélioré pour l'intégration des nouveaux clients",
  "updated_at": "2024-01-20T16:00:00Z",
  "settings": {
    "timeout_seconds": 600,
    "retry_on_failure": true,
    "max_retries": 5
  }
}
```

---

### DELETE `/workflows/{workflow_id}/`
**Supprimer un workflow**

**Réponse (204) :** Aucun contenu

**Note :** Supprime également tous les nœuds, arêtes et historique d'exécution.

---

### POST `/workflows/{workflow_id}/activate/`
**Activer un workflow**

**Réponse (200) :**
```json
{
  "message": "Workflow activé avec succès",
  "workflow_id": "workflow-uuid-here",
  "status": "active",
  "activated_at": "2024-01-20T16:30:00Z",
  "webhook_url": "https://api.nocode-platform.com/api/v1/automation/workflows/workflow-uuid-here/trigger/"
}
```

---

### POST `/workflows/{workflow_id}/deactivate/`
**Désactiver un workflow**

**Réponse (200) :**
```json
{
  "message": "Workflow désactivé",
  "workflow_id": "workflow-uuid-here",
  "status": "inactive",
  "deactivated_at": "2024-01-20T16:35:00Z"
}
```

---

### POST `/workflows/{workflow_id}/execute/`
**Exécuter manuellement un workflow**

**Requête :**
```json
{
  "input_data": {
    "client_id": 123,
    "client_email": "newclient@example.com",
    "client_name": "Nouveau Client"
  },
  "execution_context": {
    "triggered_by": "admin@company.com",
    "manual_execution": true
  }
}
```

**Réponse (202) :**
```json
{
  "execution_id": "exec-uuid-here",
  "workflow_id": "workflow-uuid-here",
  "status": "running",
  "started_at": "2024-01-20T16:40:00Z",
  "estimated_duration": "2-3 minutes",
  "input_data": {
    "client_id": 123,
    "client_email": "newclient@example.com",
    "client_name": "Nouveau Client"
  }
}
```

---

## 🔗 **Nœuds de Workflow**

### GET `/workflows/{workflow_id}/nodes/`
**Lister les nœuds d'un workflow**

**Réponse (200) :**
```json
{
  "count": 8,
  "results": [
    {
      "id": 1,
      "tracking_id": "node-uuid-1",
      "workflow": "workflow-uuid-here",
      "name": "Vérifier Client",
      "node_type": "condition",
      "position": {
        "x": 100,
        "y": 50
      },
      "config": {
        "condition": "input_data.client_exists == true",
        "true_path": "node-uuid-2",
        "false_path": "node-uuid-3"
      },
      "inputs": [
        {
          "name": "client_data",
          "type": "object",
          "required": true
        }
      ],
      "outputs": [
        {
          "name": "validation_result",
          "type": "boolean"
        }
      ],
      "created_at": "2024-01-01T10:30:00Z"
    },
    {
      "id": 2,
      "tracking_id": "node-uuid-2",
      "workflow": "workflow-uuid-here",
      "name": "Envoyer Email Bienvenue",
      "node_type": "action",
      "position": {
        "x": 250,
        "y": 50
      },
      "config": {
        "action_type": "send_email",
        "template": "welcome_email",
        "recipient": "{{input_data.client_email}}",
        "subject": "Bienvenue chez nous !",
        "variables": {
          "client_name": "{{input_data.client_name}}"
        }
      },
      "inputs": [
        {
          "name": "client_email",
          "type": "string",
          "required": true
        }
      ],
      "outputs": [
        {
          "name": "email_sent",
          "type": "boolean"
        }
      ]
    }
  ]
}
```

**Types de nœuds :**
- `trigger` : Point d'entrée du workflow
- `action` : Actions (email, API, database)
- `condition` : Conditions logiques
- `transform` : Transformation de données
- `delay` : Attente/temporisation
- `loop` : Boucles itératives
- `http_request` : Appels HTTP externes
- `database_query` : Requêtes base de données

---

### POST `/workflows/{workflow_id}/nodes/`
**Créer un nouveau nœud**

**Requête :**
```json
{
  "name": "Créer Tâche CRM",
  "node_type": "action",
  "position": {
    "x": 400,
    "y": 100
  },
  "config": {
    "action_type": "create_record",
    "table": "taches",
    "data": {
      "titre": "Suivi client {{input_data.client_name}}",
      "description": "Contacter le nouveau client",
      "priorite": "haute",
      "assigne_a": "commercial@company.com",
      "date_echeance": "{{now() + 7 days}}"
    }
  },
  "inputs": [
    {
      "name": "client_name",
      "type": "string",
      "required": true
    }
  ],
  "outputs": [
    {
      "name": "task_id",
      "type": "integer"
    }
  ]
}
```

**Réponse (201) :**
```json
{
  "id": 9,
  "tracking_id": "node-uuid-new",
  "workflow": "workflow-uuid-here",
  "name": "Créer Tâche CRM",
  "node_type": "action",
  "position": {
    "x": 400,
    "y": 100
  },
  "config": {
    "action_type": "create_record",
    "table": "taches",
    "data": {
      "titre": "Suivi client {{input_data.client_name}}",
      "description": "Contacter le nouveau client",
      "priorite": "haute",
      "assigne_a": "commercial@company.com",
      "date_echeance": "{{now() + 7 days}}"
    }
  },
  "created_at": "2024-01-20T17:00:00Z"
}
```

---

### GET `/workflows/{workflow_id}/nodes/{node_id}/`
**Détails d'un nœud spécifique**

**Réponse (200) :**
```json
{
  "id": 1,
  "tracking_id": "node-uuid-1",
  "workflow": "workflow-uuid-here",
  "name": "Vérifier Client",
  "node_type": "condition",
  "position": {
    "x": 100,
    "y": 50
  },
  "config": {
    "condition": "input_data.client_exists == true",
    "true_path": "node-uuid-2",
    "false_path": "node-uuid-3"
  },
  "inputs": [
    {
      "name": "client_data",
      "type": "object",
      "required": true,
      "description": "Données du client à vérifier"
    }
  ],
  "outputs": [
    {
      "name": "validation_result",
      "type": "boolean",
      "description": "Résultat de la validation"
    }
  ],
  "execution_statistics": {
    "executions_count": 245,
    "success_count": 238,
    "failure_count": 7,
    "average_execution_time_ms": 150,
    "last_executed": "2024-01-20T14:30:00Z"
  },
  "created_at": "2024-01-01T10:30:00Z",
  "updated_at": "2024-01-15T14:00:00Z"
}
```

---

### PUT `/workflows/{workflow_id}/nodes/{node_id}/`
**Mettre à jour un nœud**

**Requête :**
```json
{
  "name": "Vérifier Client VIP",
  "position": {
    "x": 120,
    "y": 60
  },
  "config": {
    "condition": "input_data.client_exists == true && input_data.is_vip == true",
    "true_path": "node-uuid-2",
    "false_path": "node-uuid-4"
  }
}
```

**Réponse (200) :**
```json
{
  "id": 1,
  "name": "Vérifier Client VIP",
  "updated_at": "2024-01-20T17:30:00Z"
}
```

---

### DELETE `/workflows/{workflow_id}/nodes/{node_id}/`
**Supprimer un nœud**

**Réponse (204) :** Aucun contenu

**Attention :** Supprime également les arêtes connectées à ce nœud.

---

## 🔗 **Arêtes (Edges) - Connexions**

### GET `/workflows/{workflow_id}/edges/`
**Lister les arêtes d'un workflow**

**Réponse (200) :**
```json
{
  "count": 7,
  "results": [
    {
      "id": 1,
      "tracking_id": "edge-uuid-1",
      "workflow": "workflow-uuid-here",
      "source_node": "node-uuid-1",
      "target_node": "node-uuid-2",
      "condition": "validation_result == true",
      "label": "Client valide",
      "style": {
        "color": "#10B981",
        "width": 2,
        "type": "solid"
      },
      "created_at": "2024-01-01T10:45:00Z"
    },
    {
      "id": 2,
      "tracking_id": "edge-uuid-2",
      "workflow": "workflow-uuid-here",
      "source_node": "node-uuid-1",
      "target_node": "node-uuid-3",
      "condition": "validation_result == false",
      "label": "Client invalide",
      "style": {
        "color": "#EF4444",
        "width": 2,
        "type": "dashed"
      },
      "created_at": "2024-01-01T10:45:00Z"
    }
  ]
}
```

---

### POST `/workflows/{workflow_id}/edges/`
**Créer une nouvelle arête**

**Requête :**
```json
{
  "source_node": "node-uuid-2",
  "target_node": "node-uuid-5",
  "condition": "email_sent == true",
  "label": "Email envoyé",
  "style": {
    "color": "#3B82F6",
    "width": 2,
    "type": "solid"
  }
}
```

**Réponse (201) :**
```json
{
  "id": 8,
  "tracking_id": "edge-uuid-new",
  "workflow": "workflow-uuid-here",
  "source_node": "node-uuid-2",
  "target_node": "node-uuid-5",
  "condition": "email_sent == true",
  "label": "Email envoyé",
  "created_at": "2024-01-20T18:00:00Z"
}
```

---

### DELETE `/workflows/{workflow_id}/edges/{edge_id}/`
**Supprimer une arête**

**Réponse (204) :** Aucun contenu

---

## 📊 **Graphe Complet du Workflow**

### GET `/workflows/{workflow_id}/graph/`
**Obtenir le graphe complet du workflow**

**Réponse (200) :**
```json
{
  "workflow": {
    "id": "workflow-uuid-here",
    "name": "Processus d'Onboarding Client",
    "status": "active"
  },
  "nodes": [
    {
      "id": "node-uuid-1",
      "name": "Trigger Client",
      "type": "trigger",
      "position": { "x": 50, "y": 100 },
      "config": {
        "trigger_type": "webhook",
        "event": "client.created"
      }
    },
    {
      "id": "node-uuid-2",
      "name": "Vérifier Client",
      "type": "condition",
      "position": { "x": 200, "y": 100 },
      "config": {
        "condition": "input_data.client_exists == true"
      }
    },
    {
      "id": "node-uuid-3",
      "name": "Envoyer Email",
      "type": "action",
      "position": { "x": 350, "y": 50 },
      "config": {
        "action_type": "send_email",
        "template": "welcome"
      }
    },
    {
      "id": "node-uuid-4",
      "name": "Créer Tâche",
      "type": "action",
      "position": { "x": 350, "y": 150 },
      "config": {
        "action_type": "create_record",
        "table": "taches"
      }
    }
  ],
  "edges": [
    {
      "id": "edge-uuid-1",
      "source": "node-uuid-1",
      "target": "node-uuid-2",
      "condition": null
    },
    {
      "id": "edge-uuid-2",
      "source": "node-uuid-2",
      "target": "node-uuid-3",
      "condition": "validation_result == true"
    },
    {
      "id": "edge-uuid-3",
      "source": "node-uuid-2",
      "target": "node-uuid-4",
      "condition": "validation_result == false"
    }
  ],
  "layout": {
    "direction": "horizontal",
    "spacing": 50,
    "algorithm": "dagre"
  },
  "metadata": {
    "total_nodes": 4,
    "total_edges": 3,
    "execution_paths": 2,
    "complexity_score": 7
  }
}
```

---

## 🔌 **Intégrations Externes**

### GET `/integrations/`
**Lister les intégrations disponibles**

**Réponse (200) :**
```json
{
  "count": 12,
  "results": [
    {
      "id": 1,
      "tracking_id": "integration-uuid-1",
      "name": "SendGrid Email",
      "type": "email",
      "provider": "sendgrid",
      "status": "configured",
      "description": "Envoi d'emails transactionnels via SendGrid",
      "configuration": {
        "api_key_configured": true,
        "from_email": "noreply@company.com",
        "from_name": "Company App"
      },
      "usage_statistics": {
        "emails_sent_today": 45,
        "emails_sent_this_month": 1250,
        "quota_used_percentage": 25
      },
      "created_at": "2024-01-01T10:00:00Z"
    },
    {
      "id": 2,
      "tracking_id": "integration-uuid-2",
      "name": "Slack Notifications",
      "type": "messaging",
      "provider": "slack",
      "status": "configured",
      "description": "Notifications et messages Slack",
      "configuration": {
        "webhook_url_configured": true,
        "default_channel": "#notifications",
        "bot_name": "WorkflowBot"
      },
      "usage_statistics": {
        "messages_sent_today": 12,
        "messages_sent_this_month": 340
      },
      "created_at": "2024-01-05T14:00:00Z"
    }
  ]
}
```

**Types d'intégrations :**
- `email` : Services d'email (SendGrid, Mailgun, SES)
- `messaging` : Messagerie (Slack, Teams, Discord)
- `storage` : Stockage (AWS S3, Google Cloud, Azure)
- `database` : Bases de données externes
- `payment` : Paiements (Stripe, PayPal)
- `analytics` : Analytics (Google Analytics, Mixpanel)

---

### POST `/integrations/`
**Créer une nouvelle intégration**

**Requête :**
```json
{
  "name": "Stripe Payments",
  "type": "payment",
  "provider": "stripe",
  "configuration": {
    "api_key": "sk_test_...",
    "webhook_secret": "whsec_...",
    "default_currency": "EUR",
    "success_url": "https://app.company.com/payment/success",
    "cancel_url": "https://app.company.com/payment/cancel"
  },
  "settings": {
    "test_mode": true,
    "retry_on_failure": true,
    "webhook_events": ["payment_intent.succeeded", "payment_intent.payment_failed"]
  }
}
```

**Réponse (201) :**
```json
{
  "id": 13,
  "tracking_id": "integration-uuid-new",
  "name": "Stripe Payments",
  "type": "payment",
  "provider": "stripe",
  "status": "configured",
  "configuration": {
    "api_key_configured": true,
    "webhook_configured": true,
    "default_currency": "EUR"
  },
  "created_at": "2024-01-20T18:30:00Z",
  "webhook_endpoint": "https://api.nocode-platform.com/api/v1/automation/integrations/integration-uuid-new/webhook/"
}
```

---

### GET `/integrations/{integration_id}/`
**Détails d'une intégration**

**Réponse (200) :**
```json
{
  "id": 1,
  "tracking_id": "integration-uuid-1",
  "name": "SendGrid Email",
  "type": "email",
  "provider": "sendgrid",
  "status": "configured",
  "description": "Envoi d'emails transactionnels via SendGrid",
  "configuration": {
    "api_key_configured": true,
    "from_email": "noreply@company.com",
    "from_name": "Company App",
    "reply_to": "support@company.com"
  },
  "settings": {
    "test_mode": false,
    "tracking_enabled": true,
    "bounce_handling": true
  },
  "usage_statistics": {
    "emails_sent_today": 45,
    "emails_sent_this_month": 1250,
    "quota_used_percentage": 25,
    "average_delivery_time_seconds": 2.5,
    "bounce_rate": 0.02
  },
  "health_status": {
    "overall": "healthy",
    "api_connection": "connected",
    "last_check": "2024-01-20T18:00:00Z",
    "error_rate": 0.01
  },
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-15T14:30:00Z"
}
```

---

## ⚡ **Exécutions de Workflows**

### GET `/executions/`
**Lister les exécutions de workflows**

**Paramètres de requête :**
- `workflow` (optional) : Filtrer par workflow UUID
- `status` (optional) : Filtrer par statut (running/completed/failed/cancelled)
- `date_from` (optional) : Filtrer par date de début
- `date_to` (optional) : Filtrer par date de fin

**Réponse (200) :**
```json
{
  "count": 245,
  "results": [
    {
      "id": 245,
      "tracking_id": "exec-uuid-here",
      "workflow": {
        "id": "workflow-uuid-here",
        "name": "Processus d'Onboarding Client"
      },
      "status": "completed",
      "started_at": "2024-01-20T14:30:00Z",
      "completed_at": "2024-01-20T14:31:45Z",
      "duration_seconds": 105,
      "trigger_type": "webhook",
      "input_data": {
        "client_id": 123,
        "client_email": "newclient@example.com",
        "client_name": "Nouveau Client"
      },
      "output_data": {
        "email_sent": true,
        "task_created": true,
        "task_id": 456
      },
      "nodes_executed": 5,
      "nodes_success": 5,
      "nodes_failed": 0,
      "execution_path": ["node-uuid-1", "node-uuid-2", "node-uuid-3", "node-uuid-5"],
      "performed_by": "system",
      "error_message": null
    }
  ]
}
```

---

### GET `/executions/{execution_id}/`
**Détails d'une exécution spécifique**

**Réponse (200) :**
```json
{
  "id": 245,
  "tracking_id": "exec-uuid-here",
  "workflow": {
    "id": "workflow-uuid-here",
    "name": "Processus d'Onboarding Client"
  },
  "status": "completed",
  "started_at": "2024-01-20T14:30:00Z",
  "completed_at": "2024-01-20T14:31:45Z",
  "duration_seconds": 105,
  "trigger_type": "webhook",
  "input_data": {
    "client_id": 123,
    "client_email": "newclient@example.com",
    "client_name": "Nouveau Client"
  },
  "output_data": {
    "email_sent": true,
    "task_created": true,
    "task_id": 456
  },
  "execution_details": [
    {
      "node_id": "node-uuid-1",
      "node_name": "Trigger Client",
      "status": "completed",
      "started_at": "2024-01-20T14:30:00Z",
      "completed_at": "2024-01-20T14:30:05Z",
      "duration_seconds": 5,
      "input_data": null,
      "output_data": {
        "client_data": {
          "id": 123,
          "email": "newclient@example.com",
          "name": "Nouveau Client"
        }
      }
    },
    {
      "node_id": "node-uuid-2",
      "node_name": "Vérifier Client",
      "status": "completed",
      "started_at": "2024-01-20T14:30:05Z",
      "completed_at": "2024-01-20T14:30:15Z",
      "duration_seconds": 10,
      "input_data": {
        "client_data": {
          "id": 123,
          "email": "newclient@example.com"
        }
      },
      "output_data": {
        "validation_result": true
      }
    }
  ],
  "performance_metrics": {
    "total_nodes": 5,
    "execution_path_length": 4,
    "average_node_execution_time": 21,
    "memory_usage_mb": 12.5,
    "api_calls_count": 3
  }
}
```

---

### POST `/executions/{execution_id}/cancel/`
**Annuler une exécution en cours**

**Réponse (200) :**
```json
{
  "message": "Exécution annulée",
  "execution_id": "exec-uuid-here",
  "status": "cancelled",
  "cancelled_at": "2024-01-20T19:00:00Z",
  "nodes_completed": 3,
  "nodes_remaining": 2
}
```

---

### POST `/executions/{execution_id}/retry/`
**Relancer une exécution échouée**

**Réponse (202) :**
```json
{
  "message": "Nouvelle exécution démarrée",
  "original_execution_id": "exec-uuid-failed",
  "new_execution_id": "exec-uuid-retry",
  "status": "running",
  "started_at": "2024-01-20T19:15:00Z",
  "retry_from_node": "node-uuid-3"
}
```

---

## 🎯 **Templates d'Actions**

### GET `/action-templates/`
**Lister les templates d'actions disponibles**

**Réponse (200) :**
```json
{
  "count": 25,
  "results": [
    {
      "id": 1,
      "name": "Send Email Template",
      "category": "communication",
      "description": "Envoyer un email avec template personnalisé",
      "node_type": "action",
      "config_template": {
        "action_type": "send_email",
        "integration": "sendgrid",
        "template": "{{template_name}}",
        "recipient": "{{recipient_email}}",
        "subject": "{{email_subject}}",
        "variables": {
          "{{variable_name}}": "{{variable_value}}"
        }
      },
      "required_inputs": [
        {
          "name": "recipient_email",
          "type": "string",
          "description": "Email du destinataire"
        },
        {
          "name": "template_name",
          "type": "string",
          "description": "Nom du template à utiliser"
        }
      ],
      "outputs": [
        {
          "name": "email_sent",
          "type": "boolean",
          "description": "Email envoyé avec succès"
        }
      ]
    },
    {
      "id": 2,
      "name": "Create Database Record",
      "category": "data",
      "description": "Créer un enregistrement dans une table",
      "node_type": "action",
      "config_template": {
        "action_type": "create_record",
        "table": "{{table_name}}",
        "data": {
          "{{field_name}}": "{{field_value}}"
        }
      }
    }
  ]
}
```

---

## 🧪 **Tests et Débogage**

### POST `/workflows/{workflow_id}/test/`
**Tester un workflow avec des données de test**

**Requête :**
```json
{
  "test_data": {
    "client_id": 999,
    "client_email": "test@example.com",
    "client_name": "Client Test"
  },
  "test_mode": "dry_run",
  "capture_outputs": true
}
```

**Réponse (200) :**
```json
{
  "test_execution_id": "test-uuid-here",
  "status": "completed",
  "test_results": {
    "nodes_executed": 5,
    "nodes_success": 5,
    "nodes_failed": 0,
    "execution_path": ["node-uuid-1", "node-uuid-2", "node-uuid-3"],
    "outputs": {
      "email_sent": true,
      "task_created": true,
      "task_id": "test-123"
    },
    "performance": {
      "duration_seconds": 45,
      "memory_usage_mb": 8.5
    }
  },
  "validation_results": {
    "all_nodes_connected": true,
    "no_circular_dependencies": true,
    "all_required_inputs_provided": true
  }
}
```

---

### GET `/workflows/{workflow_id}/validate/`
**Valider la configuration d'un workflow**

**Réponse (200) :**
```json
{
  "workflow_id": "workflow-uuid-here",
  "validation_status": "valid",
  "checks": [
    {
      "check": "nodes_connected",
      "status": "passed",
      "message": "Tous les nœuds sont correctement connectés"
    },
    {
      "check": "no_circular_dependencies",
      "status": "passed",
      "message": "Aucune dépendance circulaire détectée"
    },
    {
      "check": "required_inputs",
      "status": "passed",
      "message": "Tous les inputs requis sont fournis"
    },
    {
      "check": "integration_availability",
      "status": "warning",
      "message": "L'intégration SendGrid est en mode test"
    }
  ],
  "issues": [],
  "warnings": [
    {
      "type": "integration_test_mode",
      "message": "SendGrid est en mode test, les emails ne seront pas envoyés",
      "node_id": "node-uuid-3"
    }
  ],
  "can_execute": true
}
```

---

## 🔄 **Exemples d'Intégration**

### JavaScript Client pour Workflows
```javascript
class AutomationAPI {
    constructor(baseURL, token) {
        this.baseURL = baseURL;
        this.token = token;
    }

    async createWorkflow(workflowData) {
        const response = await fetch(`${this.baseURL}/api/v1/automation/workflows/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(workflowData)
        });
        return response.json();
    }

    async addNode(workflowId, nodeData) {
        const response = await fetch(`${this.baseURL}/api/v1/automation/workflows/${workflowId}/nodes/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(nodeData)
        });
        return response.json();
    }

    async connectNodes(workflowId, sourceNode, targetNode, condition = null) {
        const response = await fetch(`${this.baseURL}/api/v1/automation/workflows/${workflowId}/edges/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                source_node: sourceNode,
                target_node: targetNode,
                condition: condition
            })
        });
        return response.json();
    }

    async executeWorkflow(workflowId, inputData) {
        const response = await fetch(`${this.baseURL}/api/v1/automation/workflows/${workflowId}/execute/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                input_data: inputData
            })
        });
        return response.json();
    }

    async getWorkflowGraph(workflowId) {
        const response = await fetch(`${this.baseURL}/api/v1/automation/workflows/${workflowId}/graph/`, {
            headers: { 'Authorization': `Bearer ${this.token}` }
        });
        return response.json();
    }
}

// Utilisation
const automation = new AutomationAPI('https://api.nocode-platform.com', token);

// Créer un workflow
const workflow = await automation.createWorkflow({
    name: 'Workflow Test',
    project: 'project-uuid',
    trigger_type: 'webhook'
});

// Ajouter des nœuds
const trigger = await automation.addNode(workflow.tracking_id, {
    name: 'Trigger',
    node_type: 'trigger',
    position: { x: 50, y: 100 }
});

const emailNode = await automation.addNode(workflow.tracking_id, {
    name: 'Send Email',
    node_type: 'action',
    position: { x: 200, y: 100 },
    config: {
        action_type: 'send_email',
        recipient: '{{input_data.email}}'
    }
});

// Connecter les nœuds
await automation.connectNodes(workflow.tracking_id, trigger.tracking_id, emailNode.tracking_id);

// Exécuter
const execution = await automation.executeWorkflow(workflow.tracking_id, {
    email: 'test@example.com',
    name: 'Test User'
});
```

### React Component pour Workflow Builder
```jsx
import React, { useState, useEffect } from 'react';

function WorkflowBuilder({ projectId }) {
    const [workflow, setWorkflow] = useState(null);
    const [nodes, setNodes] = useState([]);
    const [edges, setEdges] = useState([]);
    const [selectedNode, setSelectedNode] = useState(null);

    useEffect(() => {
        if (workflow) {
            loadWorkflowGraph();
        }
    }, [workflow]);

    const loadWorkflowGraph = async () => {
        const response = await fetch(`/api/v1/automation/workflows/${workflow.id}/graph/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const graph = await response.json();
        setNodes(graph.nodes);
        setEdges(graph.edges);
    };

    const addNode = async (nodeType) => {
        const response = await fetch(`/api/v1/automation/workflows/${workflow.id}/nodes/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: `Nouveau ${nodeType}`,
                node_type: nodeType,
                position: { x: 100, y: 100 }
            })
        });
        const newNode = await response.json();
        setNodes([...nodes, newNode]);
    };

    const connectNodes = async (sourceId, targetId) => {
        const response = await fetch(`/api/v1/automation/workflows/${workflow.id}/edges/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                source_node: sourceId,
                target_node: targetId
            })
        });
        const newEdge = await response.json();
        setEdges([...edges, newEdge]);
    };

    return (
        <div className="workflow-builder">
            <div className="toolbar">
                <button onClick={() => addNode('action')}>Ajouter Action</button>
                <button onClick={() => addNode('condition')}>Ajouter Condition</button>
                <button onClick={() => addNode('delay')}>Ajouter Délai</button>
            </div>
            
            <div className="canvas">
                {nodes.map(node => (
                    <div
                        key={node.id}
                        className={`node ${node.node_type}`}
                        style={{
                            left: node.position.x,
                            top: node.position.y
                        }}
                        onClick={() => setSelectedNode(node)}
                    >
                        {node.name}
                    </div>
                ))}
                
                {edges.map(edge => (
                    <svg key={edge.id} className="edge">
                        <line
                            x1={getNodePosition(edge.source).x}
                            y1={getNodePosition(edge.source).y}
                            x2={getNodePosition(edge.target).x}
                            y2={getNodePosition(edge.target).y}
                            stroke="#3B82F6"
                            strokeWidth="2"
                        />
                    </svg>
                ))}
            </div>
            
            {selectedNode && (
                <div className="node-editor">
                    <h3>Éditer: {selectedNode.name}</h3>
                    <NodeEditor node={selectedNode} onUpdate={updateNode} />
                </div>
            )}
        </div>
    );
}
```

---

## 📊 **Monitoring et Statistiques**

### Statistiques Workflow
```json
{
  "workflow_id": "workflow-uuid-here",
  "statistics": {
    "executions_total": 1250,
    "executions_today": 45,
    "executions_this_week": 280,
    "success_rate": 0.95,
    "average_execution_time_seconds": 65,
    "error_rate": 0.05,
    "last_execution_status": "success",
    "last_execution_at": "2024-01-20T14:30:00Z"
  },
  "performance": {
    "fastest_execution_seconds": 15,
    "slowest_execution_seconds": 180,
    "average_memory_usage_mb": 25.5,
    "peak_memory_usage_mb": 45.2
  },
  "usage_by_day": [
    {
      "date": "2024-01-20",
      "executions": 45,
      "successes": 43,
      "failures": 2
    },
    {
      "date": "2024-01-19",
      "executions": 52,
      "successes": 50,
      "failures": 2
    }
  ]
}
```

---

## 🚨 **Codes d'Erreur**

| Code | Message | Contexte |
|------|---------|----------|
| `AUTO_001` | "Workflow non trouvé" | Endpoint workflow invalide |
| `AUTO_002` | "Nœud non connecté" | Graphe incomplet |
| `AUTO_003` | "Dépendance circulaire" | Boucle dans le workflow |
| `AUTO_004` | "Integration non configurée" | Action requiert une intégration |
| `AUTO_005` | "Exécution en cours" | Impossible d'exécuter |
| `AUTO_006` | "Timeout d'exécution" | Workflow trop long |
| `AUTO_007` | "Données invalides" | Input validation failed |

---

*Documentation Automation API - Version 1.0*
