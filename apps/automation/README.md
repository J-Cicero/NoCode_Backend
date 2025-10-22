# Module Automation - Documentation

## Vue d'ensemble

Le module **Automation** permet de créer et d'exécuter des workflows automatisés pour orchestrer des tâches complexes sans coder. Il offre :

- ✅ **Moteur de Workflows** : Exécution séquentielle d'étapes avec conditions et branches
- ✅ **Hub d'Intégrations** : Connexions sécurisées aux services externes (Email, Stripe, etc.)
- ✅ **Système de Déclencheurs** : Événements, webhooks, planification (cron)
- ✅ **Exécution Asynchrone** : Via Celery pour performances optimales
- ✅ **Monitoring Temps Réel** : WebSockets pour suivre les exécutions
- ✅ **Gestion d'Erreurs** : Retry automatique, logging détaillé

---

## Architecture

```
apps/automation/
├── models.py              # Modèles de données
├── serializers.py         # Serializers DRF
├── views.py               # ViewSets API
├── urls.py                # Routes API
├── admin.py               # Interface admin
├── signals.py             # Signaux Django
├── tasks.py               # Tâches Celery
├── services/
│   ├── workflow_engine.py     # Moteur d'exécution
│   ├── action_executor.py     # Exécuteur d'actions
│   └── integration_service.py # Gestion des intégrations
└── websockets/
    ├── consumers.py       # Consumers WebSocket
    └── routing.py         # Routes WebSocket
```

---

## Modèles de Données

### 1. Workflow
Définit un flux d'automatisation.

**Champs principaux** :
- `name` : Nom du workflow
- `status` : DRAFT, ACTIVE, PAUSED, ARCHIVED
- `organization` : Organisation propriétaire
- `project` : Projet Studio lié (optionnel)
- `variables` : Variables globales
- `config` : Configuration générale

**Statistiques** :
- `execution_count` : Nombre total d'exécutions
- `success_count` / `failure_count` : Compteurs de résultats
- `success_rate` : Taux de succès (calculé)

### 2. WorkflowStep
Représente une étape dans un workflow.

**Types d'actions** :
- `validate_data` : Validation de données
- `database_save` : Sauvegarde en base
- `database_query` : Requête SQL
- `integration_call` : Appel d'intégration
- `send_email` : Envoi d'email
- `send_webhook` : Webhook HTTP
- `transform_data` : Transformation de données
- `conditional` : Logique conditionnelle
- `loop` : Boucle
- `wait` : Attente
- `custom_code` : Code personnalisé

**Gestion d'erreurs** :
- `on_error` : stop, continue, retry, goto
- `retry_count` : Nombre de tentatives
- `retry_delay` : Délai entre tentatives

### 3. Trigger
Définit un déclencheur pour un workflow.

**Types de déclencheurs** :
- `manual` : Déclenchement manuel
- `event` : Événement système (via EventBus)
- `webhook` : Webhook entrant
- `schedule` : Planification (cron)
- `form_submit` : Soumission de formulaire
- `data_change` : Modification de données
- `api_call` : Appel API

### 4. Integration
Connexion à un service externe.

**Types disponibles** :
- `email` : SMTP / SendGrid
- `stripe` : Paiements
- `webhook` : HTTP
- `slack` : Notifications
- `database` : Bases de données
- `api` : API REST personnalisée

**Sécurité** :
- Credentials encryptés via `IntegrationCredential`
- Rate limiting configurable
- Statistiques d'utilisation

### 5. WorkflowExecution
Enregistre une exécution de workflow.

**Données trackées** :
- `status` : pending, running, completed, failed, cancelled
- `input_data` / `output_data` : Données entrée/sortie
- `context` : Variables et état durant l'exécution
- `current_step_id` : Étape en cours
- `completed_steps` : Étapes terminées
- `duration` : Durée totale

### 6. WorkflowExecutionLog
Logs détaillés de l'exécution.

**Niveaux** : DEBUG, INFO, WARNING, ERROR, CRITICAL

---

## API REST

### Workflows

#### Liste des workflows
```http
GET /api/v1/automation/workflows/
```

**Réponse** :
```json
{
  "count": 5,
  "results": [
    {
      "id": "uuid",
      "name": "Contact Form Workflow",
      "status": "ACTIVE",
      "execution_count": 42,
      "success_rate": 95.2,
      "triggers_count": 2,
      "steps_count": 5
    }
  ]
}
```

#### Créer un workflow
```http
POST /api/v1/automation/workflows/
```

**Body** :
```json
{
  "name": "New Contact Workflow",
  "description": "Traite les nouveaux contacts",
  "organization": 1,
  "status": "DRAFT",
  "steps": [
    {
      "step_id": "validate",
      "name": "Valider les données",
      "action_type": "validate_data",
      "order": 1,
      "params": {
        "schema": "contact_schema"
      }
    },
    {
      "step_id": "save",
      "name": "Sauvegarder en base",
      "action_type": "database_save",
      "order": 2,
      "params": {
        "table": "contacts",
        "data": "{{input.form_data}}"
      }
    }
  ],
  "triggers": [
    {
      "trigger_type": "form_submit",
      "config": {
        "form_id": "contact_form_1"
      }
    }
  ]
}
```

#### Exécuter un workflow
```http
POST /api/v1/automation/workflows/{id}/execute/
```

**Body** :
```json
{
  "input_data": {
    "form_data": {
      "name": "John Doe",
      "email": "john@example.com"
    }
  },
  "async_execution": true
}
```

**Réponse** :
```json
{
  "message": "Workflow démarré en arrière-plan",
  "task_id": "celery-task-id",
  "async": true
}
```

#### Historique des exécutions
```http
GET /api/v1/automation/workflows/{id}/executions/
```

#### Valider un workflow
```http
POST /api/v1/automation/workflows/{id}/validate/
```

#### Dupliquer un workflow
```http
POST /api/v1/automation/workflows/{id}/duplicate/
```

### Intégrations

#### Intégrations disponibles
```http
GET /api/v1/automation/integrations/available/
```

**Réponse** :
```json
{
  "integrations": [
    {
      "type": "email",
      "name": "Email",
      "description": "Envoi d'emails via SMTP ou SendGrid",
      "icon": "mail",
      "config_fields": ["provider", "smtp_host", "smtp_port"]
    }
  ]
}
```

#### Configurer une intégration
```http
POST /api/v1/automation/integrations/configure/
```

**Body** :
```json
{
  "name": "SendGrid Email",
  "integration_type": "email",
  "organization": 1,
  "config": {
    "provider": "sendgrid",
    "from_email": "noreply@example.com"
  },
  "credentials": {
    "credential_type": "api_key",
    "credentials_data": {
      "api_key": "SG.xxx"
    }
  }
}
```

#### Tester une intégration
```http
POST /api/v1/automation/integrations/{id}/test/
```

#### Exécuter une action
```http
POST /api/v1/automation/integrations/{id}/execute/
```

### Exécutions

#### Liste des exécutions
```http
GET /api/v1/automation/executions/
```

#### Détails d'une exécution
```http
GET /api/v1/automation/executions/{id}/
```

#### Logs d'une exécution
```http
GET /api/v1/automation/executions/{id}/logs/
```

#### Annuler une exécution
```http
POST /api/v1/automation/executions/{id}/cancel/
```

---

## WebSockets

### Suivi d'une exécution en temps réel

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/automation/execution/{execution_id}/');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'initial_state':
      console.log('État initial:', data.execution);
      break;
    
    case 'step_started':
      console.log('Étape démarrée:', data.step_name);
      break;
    
    case 'step_completed':
      console.log('Étape terminée:', data.step_name, data.result);
      break;
    
    case 'execution_completed':
      console.log('Workflow terminé:', data.status);
      break;
    
    case 'log':
      console.log(`[${data.log.level}] ${data.log.message}`);
      break;
  }
};

// Demander les logs
ws.send(JSON.stringify({
  action: 'get_logs'
}));
```

### Monitoring de l'organisation

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/automation/monitor/');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'initial_stats') {
    console.log('Statistiques:', data.stats);
  } else if (data.type === 'execution_started') {
    console.log('Nouvelle exécution:', data.execution);
  }
};

// Demander les stats
ws.send(JSON.stringify({
  action: 'get_stats'
}));
```

---

## Exemples de Workflows

### 1. Workflow de Contact

```json
{
  "id": "contact_form_workflow",
  "name": "Formulaire de Contact",
  "trigger": {
    "type": "form_submit",
    "form_id": "contact_form_1"
  },
  "steps": [
    {
      "id": "validate",
      "action": "validate_data",
      "params": {
        "schema": "contact_schema"
      }
    },
    {
      "id": "save_db",
      "action": "database_save",
      "params": {
        "table": "contacts",
        "data": "{{form_data}}"
      }
    },
    {
      "id": "send_email",
      "action": "integration_call",
      "integration": "sendgrid",
      "params": {
        "to": "admin@example.com",
        "template": "new_contact",
        "data": "{{form_data}}"
      }
    },
    {
      "id": "send_slack",
      "action": "integration_call",
      "integration": "slack",
      "params": {
        "channel": "#sales",
        "message": "Nouveau contact: {{form_data.name}}"
      }
    }
  ]
}
```

### 2. Workflow de Paiement

```json
{
  "id": "payment_workflow",
  "name": "Traitement de Paiement",
  "trigger": {
    "type": "event",
    "event_type": "payment.created"
  },
  "steps": [
    {
      "id": "create_stripe_customer",
      "action": "integration_call",
      "integration": "stripe",
      "params": {
        "action": "create_customer",
        "email": "{{input.customer_email}}",
        "name": "{{input.customer_name}}"
      }
    },
    {
      "id": "create_subscription",
      "action": "integration_call",
      "integration": "stripe",
      "params": {
        "action": "create_subscription",
        "customer_id": "{{steps.create_stripe_customer.customer_id}}",
        "price_id": "{{input.price_id}}"
      }
    },
    {
      "id": "send_confirmation",
      "action": "send_email",
      "params": {
        "to": "{{input.customer_email}}",
        "subject": "Abonnement confirmé",
        "template": "subscription_confirmed"
      }
    }
  ]
}
```

### 3. Workflow de Sauvegarde Planifiée

```json
{
  "id": "daily_backup_workflow",
  "name": "Sauvegarde Quotidienne",
  "trigger": {
    "type": "schedule",
    "cron_expression": "0 2 * * *"
  },
  "steps": [
    {
      "id": "export_data",
      "action": "database_query",
      "params": {
        "query": "SELECT * FROM important_data WHERE updated_at >= NOW() - INTERVAL '1 day'"
      }
    },
    {
      "id": "upload_to_s3",
      "action": "integration_call",
      "integration": "aws_s3",
      "params": {
        "bucket": "backups",
        "key": "backup_{{timestamp}}.json",
        "data": "{{steps.export_data.results}}"
      }
    },
    {
      "id": "notify_admin",
      "action": "send_email",
      "params": {
        "to": "admin@example.com",
        "subject": "Sauvegarde complétée",
        "message": "{{steps.export_data.count}} enregistrements sauvegardés"
      }
    }
  ]
}
```

---

## Tâches Celery

### Configuration dans `celerybeat_schedule`

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Traiter les triggers planifiés (chaque minute)
    'process-scheduled-triggers': {
        'task': 'apps.automation.tasks.process_scheduled_triggers',
        'schedule': crontab(minute='*'),
    },
    
    # Nettoyer les anciennes exécutions (chaque jour à 3h)
    'cleanup-old-executions': {
        'task': 'apps.automation.tasks.cleanup_old_executions',
        'schedule': crontab(hour=3, minute=0),
        'kwargs': {'days': 30},
    },
    
    # Nettoyer les exécutions bloquées (toutes les heures)
    'cleanup-stale-executions': {
        'task': 'apps.automation.tasks.cleanup_stale_executions',
        'schedule': crontab(minute=0),
    },
}
```

### Tâches disponibles

- `execute_workflow_async` : Exécute un workflow en arrière-plan
- `process_webhook_trigger` : Traite un webhook
- `process_scheduled_triggers` : Traite les crons
- `cleanup_old_executions` : Nettoie les vieilles exécutions
- `cleanup_stale_executions` : Nettoie les exécutions bloquées
- `send_workflow_notification` : Envoie une notification
- `retry_failed_step` : Réessaie une étape
- `export_workflow_execution_logs` : Exporte les logs

---

## Variables et Contexte

### Syntaxe des variables

Les variables utilisent la notation `{{variable_name}}` et peuvent référencer :

- `{{input.field}}` : Données d'entrée
- `{{variables.name}}` : Variables globales du workflow
- `{{steps.step_id.result}}` : Résultat d'une étape
- `{{form_data.email}}` : Données de formulaire
- `{{context.user_id}}` : Contexte d'exécution

### Exemple

```json
{
  "step_id": "send_email",
  "action": "send_email",
  "params": {
    "to": "{{input.customer_email}}",
    "subject": "Bienvenue {{input.customer_name}}",
    "message": "Votre ID: {{steps.create_user.user_id}}"
  }
}
```

---

## Gestion d'Erreurs

### Configuration par étape

```json
{
  "step_id": "call_external_api",
  "action": "integration_call",
  "on_error": "retry",
  "retry_count": 3,
  "retry_delay": 60,
  "params": {...}
}
```

**Options `on_error`** :
- `stop` : Arrête le workflow (défaut)
- `continue` : Continue malgré l'erreur
- `retry` : Réessaie avec backoff
- `goto` : Va à une étape spécifique

---

## Sécurité

### Credentials

Les credentials sont **chiffrés** avec Fernet avant stockage :

```python
from apps.automation.services import IntegrationService

service = IntegrationService()
service.save_credentials(
    integration=my_integration,
    credential_type='api_key',
    credentials_data={'api_key': 'secret_key'},
    expires_at=None
)
```

### Configuration requise

Ajouter dans `settings.py` :

```python
# Clé de chiffrement (générer avec Fernet.generate_key())
INTEGRATION_ENCRYPTION_KEY = b'votre-cle-de-chiffrement'
```

---

## Déploiement

### 1. Migrations

```bash
python manage.py makemigrations automation
python manage.py migrate
```

### 2. Celery

```bash
# Worker
celery -A config worker -l info

# Beat (pour les crons)
celery -A config beat -l info
```

### 3. Serveur ASGI

```bash
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

---

## Tests

### Test d'un workflow

```python
from apps.automation.models import Workflow
from apps.automation.services import WorkflowEngine

workflow = Workflow.objects.get(id='workflow_id')
engine = WorkflowEngine(workflow)

execution = engine.execute(
    input_data={'test': 'data'},
    triggered_by=user
)

assert execution.status == 'completed'
```

### Test d'une intégration

```python
from apps.automation.services import IntegrationService

service = IntegrationService()
success, message = service.test_integration(integration)

assert success is True
```

---

## Bonnes Pratiques

1. **Nommer clairement** : Utilisez des noms descriptifs pour workflows et étapes
2. **Gérer les erreurs** : Configurez `on_error` et `retry_count`
3. **Logger** : Le moteur log automatiquement, consultez les logs
4. **Tester** : Validez les workflows avant de les activer
5. **Monitorer** : Utilisez les WebSockets pour le suivi en temps réel
6. **Rate limiting** : Configurez les limites sur les intégrations
7. **Sécurité** : Ne jamais exposer les credentials en clair

---

## Support

Pour toute question ou problème :
- Consultez les logs d'exécution via l'API
- Utilisez l'interface admin Django
- Vérifiez les tâches Celery avec Flower

---

## Évolutions Futures

- [ ] Éditeur visuel de workflows (drag & drop)
- [ ] Plus d'intégrations natives (Twilio, AWS, etc.)
- [ ] Marketplace de templates de workflows
- [ ] Analytics et rapports détaillés
- [ ] Versioning des workflows
- [ ] A/B testing de workflows
