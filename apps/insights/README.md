# Module Insights - Analytics et Monitoring

Le module **Insights** fournit des fonctionnalités avancées d'analytics, de monitoring et d'audit pour la plateforme NoCode.

## Fonctionnalités Principales

### 5.1 Collecte de Métriques

**Métriques Système**
- Utilisation CPU, mémoire, disque
- Trafic réseau entrant/sortant
- Latence des requêtes
- Nombre d'erreurs serveur
- Connexions base de données

**Métriques d'Application**
- Temps de réponse des APIs générées
- Nombre de requêtes par application
- Taux d'erreur par application
- Disponibilité (uptime)
- Utilisation des ressources

**Métriques Utilisateur**
- Durée des sessions
- Pages visitées
- Actions effectuées
- Fonctionnalités utilisées
- Temps passé sur la plateforme

### 5.2 Système d'Audit

**Types d'Activités Suivies**
- Connexions/Déconnexions utilisateur
- Création/Modification/Suppression de projets
- Déploiement d'applications
- Exécution de workflows
- Actions de sécurité (changement mot de passe, 2FA)
- Erreurs système

**Informations Collectées**
- Utilisateur concerné
- Organisation
- Timestamp précis
- Adresse IP et User-Agent
- Objet générique associé (projet, app, etc.)
- Métadonnées contextuelles

## APIs Disponibles

### Tracking d'Événements
```http
POST /api/insights/track/
Content-Type: application/json

{
  "event_type": "button_click",
  "event_data": {
    "button_name": "submit",
    "page": "dashboard"
  },
  "session_id": "optional_session_id"
}
```

### Rapports d'Analytics
```http
POST /api/insights/analytics/
Content-Type: application/json

{
  "organization_id": "uuid",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "metrics": ["user_activity", "system_performance", "app_metrics"],
  "group_by": "day"
}
```

### Rapports de Performance
```http
POST /api/insights/performance/
Content-Type: application/json

{
  "app_id": "uuid",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "metrics": ["response_time", "error_rate", "uptime"]
}
```

## Auto-Tracking

Le module inclut des middlewares qui collectent automatiquement :

1. **InsightsMiddleware** : Trace les activités utilisateur importantes
2. **MetricsCollectionMiddleware** : Collecte les métriques système périodiquement

## Tâches Celery

**Tâches Périodiques**
- `collect_system_metrics_task` : Collecte CPU, mémoire, disque (toutes les 5 minutes)
- `aggregate_daily_metrics_task` : Agrégation quotidienne des métriques (minuit)
- `generate_analytics_reports_task` : Génération automatique de rapports (quotidienne)
- `cleanup_old_metrics_task` : Nettoyage des anciennes données (configurable)

## Sécurité et Performance

- **Filtrage par Organisation** : Les utilisateurs ne voient que les données de leur organisation
- **Superutilisateurs** : Accès à toutes les données
- **Optimisations** : Index sur les champs fréquemment utilisés
- **Cache** : Mise en cache des rapports fréquents
- **Nettoyage Automatique** : Suppression périodique des anciennes données

## Intégration

### Dans les Vues
```python
from apps.insights.services import ActivityTracker

# Dans une vue
ActivityTracker.track_user_action(
    user=request.user,
    action_type='project.created',
    description='Nouveau projet créé',
    content_object=project,
    request=request
)
```

### Dans les Services
```python
from apps.insights.services import MetricsCollector

# Collecter une métrique personnalisée
MetricsCollector.collect_event_metric(
    event_type='custom_event',
    user=user,
    organization=organization,
    metadata={'extra': 'data'}
)
```

## Configuration

Ajouter à `settings.py` :

```python
# Middleware pour le tracking automatique
MIDDLEWARE = [
    # ... autres middlewares
    'apps.insights.middleware.InsightsMiddleware',
    'apps.insights.middleware.MetricsCollectionMiddleware',
]

# Tâches Celery périodiques
CELERY_BEAT_SCHEDULE = {
    'collect-system-metrics': {
        'task': 'apps.insights.tasks.collect_system_metrics_task',
        'schedule': 300.0,  # Toutes les 5 minutes
    },
    'aggregate-daily-metrics': {
        'task': 'apps.insights.tasks.aggregate_daily_metrics_task',
        'schedule': crontab(hour=0, minute=0),  # Minuit tous les jours
    },
}
```

## Tests

```bash
# Tests unitaires
python manage.py test apps.insights.tests.test_models
python manage.py test apps.insights.tests.test_services
python manage.py test apps.insights.tests.test_views

# Tests d'intégration
python manage.py test apps.insights
```

## Métriques Disponibles

| Catégorie | Métriques | Description |
|-----------|-----------|-------------|
| **Système** | cpu.usage, memory.usage, disk.usage | Ressources serveur |
| **Application** | response.time, requests.count, errors.count | Performance APIs |
| **Utilisateur** | session.duration, pages.visited, actions.performed | Engagement |
| **Performance** | response_time, error_rate, uptime | Monitoring général |

## Rapports Générés

- **Rapports Quotidiens** : Agrégation automatique des métriques
- **Rapports d'Organisation** : Analytics par organisation
- **Rapports d'Application** : Performance détaillée par app
- **Rapports de Sécurité** : Activités sensibles et anomalies

## Monitoring et Alertes

Le module peut être étendu avec :
- Alertes sur seuils de performance
- Notifications d'erreurs critiques
- Dashboards temps réel
- Export de données (CSV, JSON)
- Intégration avec outils externes (Grafana, Datadog, etc.)
