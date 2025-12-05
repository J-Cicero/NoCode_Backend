# 📊 Insights API - Analytics et Monitoring

## 📋 Vue d'ensemble

Le module Insights fournit des **fonctionnalités avancées d'analytics** et de monitoring pour la plateforme NoCode. Il permet de tracker les activités utilisateur, collecter des métriques système/applicatives, et générer des rapports détaillés.

**Base URL :** `/api/v1/insights/`

---

## 🎯 **Tracking d'Événements**

### POST `/track/`
**Tracker un événement (utilisateur ou système)**

**Headers :**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Requête :**
```json
{
  "event_type": "user_action",
  "event_name": "client_created",
  "properties": {
    "user_id": 123,
    "project_id": "project-uuid-here",
    "client_id": 456,
    "client_email": "newclient@example.com",
    "source": "web_app",
    "session_id": "session-uuid-here"
  },
  "timestamp": "2024-01-20T14:30:00Z",
  "context": {
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "page": "/clients/new",
    "referrer": "/clients"
  }
}
```

**Réponse (201) :**
```json
{
  "id": "track-uuid-here",
  "event_type": "user_action",
  "event_name": "client_created",
  "tracked_at": "2024-01-20T14:30:00Z",
  "processed": true,
  "user_id": 123,
  "project_id": "project-uuid-here"
}
```

**Types d'événements :**
- `user_action` : Actions utilisateur (création, modification, suppression)
- `system_event` : Événements système (déploiement, erreur)
- `api_call` : Appels API externes
- `page_view` : Vues de pages
- `feature_usage` : Utilisation de fonctionnalités spécifiques
- `error_occurred` : Erreurs et exceptions

---

### POST `/track/batch/`
**Tracker plusieurs événements en lot**

**Requête :**
```json
{
  "events": [
    {
      "event_type": "user_action",
      "event_name": "login",
      "properties": {
        "user_id": 123,
        "method": "jwt"
      },
      "timestamp": "2024-01-20T09:00:00Z"
    },
    {
      "event_type": "page_view",
      "event_name": "dashboard_viewed",
      "properties": {
        "user_id": 123,
        "page": "/dashboard",
        "duration_seconds": 45
      },
      "timestamp": "2024-01-20T09:01:00Z"
    },
    {
      "event_type": "user_action",
      "event_name": "client_created",
      "properties": {
        "user_id": 123,
        "client_id": 456
      },
      "timestamp": "2024-01-20T09:15:00Z"
    }
  ]
}
```

**Réponse (201) :**
```json
{
  "batch_id": "batch-uuid-here",
  "events_count": 3,
  "processed_count": 3,
  "failed_count": 0,
  "processed_at": "2024-01-20T09:16:00Z"
}
```

---

## 👥 **Activités Utilisateur**

### GET `/activities/`
**Lister les activités utilisateur**

**Paramètres de requête :**
- `user_id` (optional) : Filtrer par utilisateur
- `project_id` (optional) : Filtrer par projet
- `event_type` (optional) : Filtrer par type d'événement
- `date_from` (optional) : Date de début (YYYY-MM-DD)
- `date_to` (optional) : Date de fin (YYYY-MM-DD)
- `page` (optional) : Page (défaut: 1)
- `page_size` (optional) : Taille page (défaut: 20)

**Réponse (200) :**
```json
{
  "count": 1250,
  "results": [
    {
      "id": 1250,
      "tracking_id": "activity-uuid-here",
      "event_type": "user_action",
      "event_name": "client_created",
      "user": {
        "id": 123,
        "email": "user@company.com",
        "full_name": "John Doe"
      },
      "project": {
        "tracking_id": "project-uuid-here",
        "name": "Gestion Client"
      },
      "properties": {
        "client_id": 456,
        "client_email": "newclient@example.com",
        "source": "web_app"
      },
      "context": {
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0...",
        "page": "/clients/new"
      },
      "timestamp": "2024-01-20T14:30:00Z",
      "created_at": "2024-01-20T14:30:01Z"
    },
    {
      "id": 1249,
      "tracking_id": "activity-uuid-2",
      "event_type": "page_view",
      "event_name": "dashboard_viewed",
      "user": {
        "id": 123,
        "email": "user@company.com",
        "full_name": "John Doe"
      },
      "properties": {
        "page": "/dashboard",
        "duration_seconds": 45,
        "session_id": "session-uuid-here"
      },
      "timestamp": "2024-01-20T14:25:00Z",
      "created_at": "2024-01-20T14:25:01Z"
    }
  ],
  "filters_applied": {
    "user_id": 123,
    "date_from": "2024-01-20",
    "date_to": "2024-01-20"
  }
}
```

---

### GET `/activities/{activity_id}/`
**Détails d'une activité spécifique**

**Réponse (200) :**
```json
{
  "id": 1250,
  "tracking_id": "activity-uuid-here",
  "event_type": "user_action",
  "event_name": "client_created",
  "user": {
    "id": 123,
    "email": "user@company.com",
    "full_name": "John Doe",
    "role": "MEMBER"
  },
  "project": {
    "tracking_id": "project-uuid-here",
    "name": "Gestion Client",
    "organization_name": "Tech Company"
  },
  "properties": {
    "client_id": 456,
    "client_email": "newclient@example.com",
    "source": "web_app",
    "form_completion_time_seconds": 120
  },
  "context": {
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "page": "/clients/new",
    "referrer": "/clients",
    "session_id": "session-uuid-here",
    "device_type": "desktop",
    "browser": "Chrome",
    "os": "Windows"
  },
  "timestamp": "2024-01-20T14:30:00Z",
  "created_at": "2024-01-20T14:30:01Z",
  "processed": true,
  "enriched_data": {
    "geo_location": {
      "country": "France",
      "city": "Paris",
      "latitude": 48.8566,
      "longitude": 2.3522
    },
    "device_fingerprint": "fp-uuid-here"
  }
}
```

---

### GET `/activities/users/{user_id}/summary/`
**Résumé des activités d'un utilisateur**

**Réponse (200) :**
```json
{
  "user_id": 123,
  "period": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-20"
  },
  "summary": {
    "total_activities": 245,
    "activities_today": 12,
    "activities_this_week": 85,
    "most_active_day": "2024-01-15",
    "most_active_hour": 14,
    "average_activities_per_day": 12.25
  },
  "by_event_type": {
    "user_action": 180,
    "page_view": 45,
    "api_call": 15,
    "error_occurred": 5
  },
  "by_project": [
    {
      "project_id": "project-uuid-here",
      "project_name": "Gestion Client",
      "activities_count": 200
    },
    {
      "project_id": "project-uuid-2",
      "project_name": "E-commerce",
      "activities_count": 45
    }
  ],
  "top_actions": [
    {
      "action": "client_created",
      "count": 45
    },
    {
      "action": "client_updated",
      "count": 32
    },
    {
      "action": "dashboard_viewed",
      "count": 28
    }
  ]
}
```

---

## 📈 **Métriques Système**

### GET `/system-metrics/`
**Métriques système en temps réel**

**Réponse (200) :**
```json
{
  "timestamp": "2024-01-20T15:00:00Z",
  "server": {
    "hostname": "api-server-01",
    "uptime_seconds": 2592000,
    "cpu": {
      "usage_percentage": 45.2,
      "cores": 8,
      "load_average": [1.2, 1.5, 1.8]
    },
    "memory": {
      "total_gb": 32.0,
      "used_gb": 18.5,
      "available_gb": 13.5,
      "usage_percentage": 57.8
    },
    "disk": {
      "total_gb": 500.0,
      "used_gb": 125.5,
      "available_gb": 374.5,
      "usage_percentage": 25.1
    },
    "network": {
      "bytes_received": 1073741824,
      "bytes_sent": 536870912,
      "connections_active": 25
    }
  },
  "database": {
    "connections_active": 15,
    "connections_total": 20,
    "query_time_avg_ms": 25,
    "slow_queries_count": 3,
    "cache_hit_ratio": 0.95,
    "size_gb": 12.5
  },
  "cache": {
    "type": "redis",
    "memory_used_mb": 256,
    "memory_available_mb": 768,
    "hit_ratio": 0.92,
    "operations_per_second": 1250,
    "connected_clients": 5
  },
  "application": {
    "active_sessions": 45,
    "requests_per_minute": 85,
    "average_response_time_ms": 120,
    "error_rate_percentage": 0.2,
    "background_tasks_running": 8,
    "queue_size": 12
  }
}
```

---

### GET `/system-metrics/history/`
**Historique des métriques système**

**Paramètres de requête :**
- `metric` (required) : Type de métrique (cpu/memory/disk/network/database)
- `period` (optional) : Période (1h/24h/7d/30d) (défaut: 24h)
- `interval` (optional) : Intervalle (1m/5m/15m/1h) (défaut: 5m)

**Réponse (200) :**
```json
{
  "metric": "cpu",
  "period": "24h",
  "interval": "5m",
  "data_points": [
    {
      "timestamp": "2024-01-20T00:00:00Z",
      "value": 35.2,
      "metadata": {
        "cores": 8,
        "load_average": [0.8, 1.0, 1.2]
      }
    },
    {
      "timestamp": "2024-01-20T00:05:00Z",
      "value": 38.5,
      "metadata": {
        "cores": 8,
        "load_average": [1.0, 1.2, 1.4]
      }
    }
  ],
  "statistics": {
    "average": 42.1,
    "minimum": 25.3,
    "maximum": 68.9,
    "data_points_count": 288
  }
}
```

---

### GET `/system-metrics/alerts/`
**Alertes système actives**

**Réponse (200) :**
```json
{
  "active_alerts": 2,
  "alerts": [
    {
      "id": "alert-uuid-1",
      "type": "warning",
      "metric": "memory",
      "threshold": 80,
      "current_value": 85.2,
      "message": "Utilisation mémoire élevée",
      "description": "L'utilisation mémoire dépasse 80% du seuil critique",
      "started_at": "2024-01-20T14:30:00Z",
      "duration_minutes": 30,
      "severity": "medium",
      "acknowledged": false,
      "acknowledged_by": null
    },
    {
      "id": "alert-uuid-2",
      "type": "error",
      "metric": "disk",
      "threshold": 90,
      "current_value": 92.1,
      "message": "Espace disque critique",
      "description": "L'espace disque disponible est inférieur à 10%",
      "started_at": "2024-01-20T13:45:00Z",
      "duration_minutes": 75,
      "severity": "high",
      "acknowledged": true,
      "acknowledged_by": {
        "id": 1,
        "email": "admin@company.com",
        "acknowledged_at": "2024-01-20T14:00:00Z"
      }
    }
  ]
}
```

---

## 📊 **Métriques Applicatives**

### GET `/application-metrics/`
**Métriques des applications générées**

**Paramètres de requête :**
- `app_id` (optional) : Filtrer par application
- `project_id` (optional) : Filtrer par projet
- `period` (optional) : Période (1h/24h/7d/30d) (défaut: 24h)

**Réponse (200) :**
```json
{
  "period": "24h",
  "generated_at": "2024-01-20T15:00:00Z",
  "overview": {
    "total_applications": 15,
    "active_applications": 12,
    "total_requests": 15420,
    "requests_today": 450,
    "unique_users_today": 85,
    "average_response_time_ms": 120,
    "error_rate_percentage": 0.2
  },
  "applications": [
    {
      "app_id": "app-uuid-here",
      "app_name": "Gestion Client App",
      "project_name": "Gestion Client",
      "status": "deployed",
      "metrics": {
        "requests_today": 125,
        "requests_this_hour": 8,
        "unique_users_today": 25,
        "average_response_time_ms": 95,
        "error_rate_percentage": 0.1,
        "data_operations": {
          "reads": 450,
          "creates": 25,
          "updates": 15,
          "deletes": 5
        },
        "top_endpoints": [
          {
            "endpoint": "/tables/clients/",
            "requests": 85,
            "avg_response_time_ms": 85
          },
          {
            "endpoint": "/tables/produits/",
            "requests": 40,
            "avg_response_time_ms": 110
          }
        ]
      }
    }
  ]
}
```

---

### GET `/application-metrics/{app_id}/performance/`
**Métriques de performance d'une application**

**Réponse (200) :**
```json
{
  "app_id": "app-uuid-here",
  "app_name": "Gestion Client App",
  "period": "24h",
  "performance": {
    "response_times": {
      "average_ms": 95,
      "median_ms": 85,
      "p95_ms": 150,
      "p99_ms": 250,
      "minimum_ms": 25,
      "maximum_ms": 500
    },
    "throughput": {
      "requests_per_second": 0.8,
      "requests_per_minute": 48,
      "peak_rps": 2.5,
      "peak_time": "2024-01-20T14:30:00Z"
    },
    "availability": {
      "uptime_percentage": 99.9,
      "downtime_minutes": 1.44,
      "incidents_count": 1,
      "last_incident": "2024-01-20T10:15:00Z"
    },
    "errors": {
      "total_errors": 15,
      "error_rate_percentage": 0.1,
      "error_types": {
        "400_bad_request": 8,
        "404_not_found": 4,
        "500_server_error": 3
      },
      "top_error_endpoints": [
        {
          "endpoint": "/tables/clients/invalid/",
          "error_count": 5,
          "error_type": "404_not_found"
        }
      ]
    }
  },
  "database_performance": {
    "query_time_avg_ms": 25,
    "slow_queries_count": 3,
    "cache_hit_ratio": 0.92,
    "connections_active": 8
  },
  "user_experience": {
    "average_page_load_time_ms": 1200,
    "bounce_rate_percentage": 15.5,
    "average_session_duration_seconds": 285,
    "pages_per_session": 4.2
  }
}
```

---

## 👥 **Métriques Utilisateur**

### GET `/user-metrics/`
**Métriques d'utilisation par utilisateur**

**Paramètres de requête :**
- `user_id` (optional) : Utilisateur spécifique
- `project_id` (optional) : Filtrer par projet
- `period` (optional) : Période (7d/30d/90d) (défaut: 30d)

**Réponse (200) :**
```json
{
  "period": "30d",
  "generated_at": "2024-01-20T15:00:00Z",
  "summary": {
    "total_active_users": 125,
    "new_users_this_period": 15,
    "retention_rate_percentage": 85.5,
    "average_sessions_per_user": 12.5,
    "average_session_duration_minutes": 25.5
  },
  "users": [
    {
      "user_id": 123,
      "email": "user@company.com",
      "full_name": "John Doe",
      "role": "MEMBER",
      "metrics": {
        "sessions_count": 25,
        "total_duration_minutes": 450,
        "pages_viewed": 125,
        "actions_performed": 85,
        "last_active": "2024-01-20T14:30:00Z",
        "most_used_project": {
          "project_id": "project-uuid-here",
          "project_name": "Gestion Client",
          "usage_percentage": 75
        },
        "top_actions": [
          {
            "action": "client_created",
            "count": 15
          },
          {
            "action": "client_updated",
            "count": 12
          }
        ]
      }
    }
  ],
  "engagement_metrics": {
    "daily_active_users": 45,
    "weekly_active_users": 85,
    "monthly_active_users": 125,
    "stickiness_ratio": 0.36,
    "power_users_count": 15
  }
}
```

---

### GET `/user-metrics/{user_id}/behavior/`
**Analyse comportementale d'un utilisateur**

**Réponse (200) :**
```json
{
  "user_id": 123,
  "analysis_period": "30d",
  "behavior_patterns": {
    "usage_frequency": {
      "average_sessions_per_day": 0.8,
      "most_active_days": ["Lundi", "Mardi", "Mercredi"],
      "most_active_hours": [9, 14, 16],
      "peak_usage_time": "14:00-16:00"
    },
    "feature_adoption": {
      "features_used": 12,
      "features_total": 15,
      "adoption_rate_percentage": 80,
      "advanced_features_used": 5,
      "recently_discovered_features": ["workflows", "analytics"]
    },
    "navigation_patterns": {
      "most_visited_pages": [
        {
          "page": "/dashboard",
          "visits": 45,
          "avg_duration_seconds": 120
        },
        {
          "page": "/clients",
          "visits": 35,
          "avg_duration_seconds": 180
        }
      ],
      "common_flows": [
        {
          "flow": "dashboard -> clients -> new_client",
          "frequency": 15
        }
      ]
    },
    "productivity_metrics": {
      "records_created_per_session": 3.2,
      "records_updated_per_session": 2.1,
      "tasks_completed_per_session": 1.5,
      "efficiency_score": 8.5
    }
  },
  "comparisons": {
    "vs_team_average": {
      "sessions_count": "+25%",
      "actions_performed": "+15%",
      "efficiency_score": "+10%"
    },
    "vs_previous_period": {
      "sessions_count": "+12%",
      "actions_performed": "+8%",
      "efficiency_score": "+5%"
    }
  }
}
```

---

## 📊 **Analytics et Rapports**

### GET `/analytics/`
**Tableau de bord analytics principal**

**Paramètres de requête :**
- `project_id` (optional) : Filtrer par projet
- `period` (optional) : Période (7d/30d/90d) (défaut: 30d)
- `granularity` (optional) : Granularité (day/week/month) (défaut: day)

**Réponse (200) :**
```json
{
  "period": "30d",
  "granularity": "day",
  "generated_at": "2024-01-20T15:00:00Z",
  "overview": {
    "total_users": 125,
    "active_users": 85,
    "total_sessions": 1250,
    "total_actions": 5420,
    "total_requests": 15420,
    "average_response_time_ms": 120,
    "error_rate_percentage": 0.2
  },
  "trends": {
    "user_growth": {
      "current_period": 15,
      "previous_period": 12,
      "growth_percentage": 25.0
    },
    "usage_growth": {
      "current_period": 5420,
      "previous_period": 4850,
      "growth_percentage": 11.8
    },
    "performance_trend": {
      "current_avg_response_time_ms": 120,
      "previous_avg_response_time_ms": 135,
      "improvement_percentage": 11.1
    }
  },
  "time_series": [
    {
      "date": "2024-01-01",
      "users": 45,
      "sessions": 85,
      "actions": 180,
      "requests": 450,
      "avg_response_time_ms": 125,
      "error_rate_percentage": 0.3
    },
    {
      "date": "2024-01-02",
      "users": 48,
      "sessions": 92,
      "actions": 195,
      "requests": 485,
      "avg_response_time_ms": 118,
      "error_rate_percentage": 0.2
    }
  ],
  "top_metrics": {
    "most_active_users": [
      {
        "user_id": 123,
        "email": "user@company.com",
        "actions_count": 245
      }
    ],
    "most_used_projects": [
      {
        "project_id": "project-uuid-here",
        "project_name": "Gestion Client",
        "actions_count": 1250
      }
    ],
    "most_performed_actions": [
      {
        "action": "client_created",
        "count": 245
      },
      {
        "action": "client_updated",
        "count": 180
      }
    ]
  }
}
```

---

### GET `/analytics/usage/`
**Rapport d'utilisation détaillé**

**Réponse (200) :**
```json
{
  "report_period": "30d",
  "generated_at": "2024-01-20T15:00:00Z",
  "usage_summary": {
    "total_api_requests": 15420,
    "unique_users": 85,
    "average_requests_per_user": 181.4,
    "peak_usage_day": "2024-01-15",
    "peak_usage_requests": 620
  },
  "by_feature": {
    "crud_operations": {
      "total": 8950,
      "percentage": 58.0,
      "breakdown": {
        "reads": 5420,
        "creates": 1850,
        "updates": 1250,
        "deletes": 430
      }
    },
    "authentication": {
      "total": 1250,
      "percentage": 8.1,
      "breakdown": {
        "login": 850,
        "logout": 400
      }
    },
    "file_operations": {
      "total": 620,
      "percentage": 4.0,
      "breakdown": {
        "uploads": 420,
        "downloads": 200
      }
    }
  },
  "by_time_of_day": [
    {
      "hour": 9,
      "requests": 1250,
      "users": 25
    },
    {
      "hour": 14,
      "requests": 1680,
      "users": 35
    }
  ],
  "by_day_of_week": [
    {
      "day": "Lundi",
      "requests": 2450,
      "users": 45
    },
    {
      "day": "Mardi",
      "requests": 2680,
      "users": 48
    }
  ]
}
```

---

### GET `/analytics/performance/`
**Rapport de performance**

**Réponse (200) :**
```json
{
  "report_period": "30d",
  "generated_at": "2024-01-20T15:00:00Z",
  "performance_summary": {
    "overall_availability_percentage": 99.9,
    "average_response_time_ms": 120,
    "error_rate_percentage": 0.2,
    "slow_requests_percentage": 5.2,
    "uptime_hours": 718.2,
    "downtime_hours": 0.8
  },
  "response_time_distribution": {
    "under_100ms": {
      "count": 8540,
      "percentage": 55.4
    },
    "100ms_to_500ms": {
      "count": 5420,
      "percentage": 35.2
    },
    "500ms_to_1s": {
      "count": 1250,
      "percentage": 8.1
    },
    "over_1s": {
      "count": 210,
      "percentage": 1.3
    }
  },
  "slow_endpoints": [
    {
      "endpoint": "/tables/clients/export/",
      "average_response_time_ms": 1850,
      "requests_count": 45,
      "slow_requests_percentage": 85.2
    },
    {
      "endpoint": "/analytics/reports/",
      "average_response_time_ms": 1250,
      "requests_count": 120,
      "slow_requests_percentage": 65.8
    }
  ],
  "error_analysis": {
    "total_errors": 31,
    "error_rate_percentage": 0.2,
    "error_types": {
      "400_bad_request": 18,
      "404_not_found": 8,
      "500_server_error": 5
    },
    "top_error_endpoints": [
      {
        "endpoint": "/tables/invalid/",
        "error_count": 12,
        "error_type": "404_not_found"
      }
    ]
  },
  "performance_trends": {
    "response_time_trend": "improving",
    "response_time_change_percentage": -8.5,
    "error_rate_trend": "stable",
    "error_rate_change_percentage": 0.0
  }
}
```

---

### GET `/analytics/user-retention/`
**Rapport de rétention utilisateur**

**Réponse (200) :**
```json
{
  "cohort_analysis": {
    "period": "90d",
    "cohorts": [
      {
        "cohort_date": "2024-01-01",
        "initial_users": 25,
        "retention_rates": [
          {
            "day": 1,
            "retained_users": 23,
            "retention_percentage": 92.0
          },
          {
            "day": 7,
            "retained_users": 20,
            "retention_percentage": 80.0
          },
          {
            "day": 30,
            "retained_users": 18,
            "retention_percentage": 72.0
          }
        ]
      }
    ]
  },
  "retention_summary": {
    "day_1_retention_percentage": 88.5,
    "day_7_retention_percentage": 75.2,
    "day_30_retention_percentage": 68.5,
    "average_lifespan_days": 45.2
  },
  "churn_analysis": {
    "total_churned_users": 15,
    "churn_rate_percentage": 12.0,
    "churn_reasons": [
      {
        "reason": "inactivity",
        "count": 8,
        "percentage": 53.3
      },
      {
        "reason": "subscription_cancelled",
        "count": 5,
        "percentage": 33.3
      }
    ],
    "churn_prediction": {
      "at_risk_users_count": 12,
      "at_risk_percentage": 9.6
    }
  }
}
```

---

## 📈 **Performance Monitoring**

### GET `/performance/`
**Métriques de performance en temps réel**

**Réponse (200) :**
```json
{
  "timestamp": "2024-01-20T15:00:00Z",
  "application_performance": {
    "current_rps": 0.8,
    "average_response_time_ms": 120,
    "p95_response_time_ms": 250,
    "p99_response_time_ms": 450,
    "error_rate_percentage": 0.2,
    "active_connections": 25
  },
  "database_performance": {
    "connection_pool": {
      "active": 15,
      "idle": 5,
      "total": 20,
      "utilization_percentage": 75.0
    },
    "query_performance": {
      "average_time_ms": 25,
      "slow_queries_count": 3,
      "queries_per_second": 45.2
    },
    "cache_performance": {
      "hit_ratio": 0.92,
      "miss_ratio": 0.08,
      "evictions_per_minute": 2
    }
  },
  "resource_utilization": {
    "cpu": {
      "usage_percentage": 45.2,
      "load_average": [1.2, 1.5, 1.8]
    },
    "memory": {
      "used_gb": 18.5,
      "available_gb": 13.5,
      "usage_percentage": 57.8
    },
    "disk": {
      "read_iops": 125,
      "write_iops": 85,
      "usage_percentage": 25.1
    }
  },
  "background_tasks": {
    "active_tasks": 8,
    "pending_tasks": 12,
    "failed_tasks_24h": 2,
    "queue_depth": 15
  }
}
```

---

### GET `/performance/slow-queries/`
**Requêtes lentes identifiées**

**Réponse (200) :**
```json
{
  "period": "24h",
  "slow_queries": [
    {
      "query_hash": "hash-uuid-1",
      "query": "SELECT * FROM project_1_clients WHERE email LIKE '%@company.com%'",
      "execution_count": 45,
      "average_time_ms": 1250,
      "total_time_ms": 56250,
      "first_seen": "2024-01-20T09:15:00Z",
      "last_seen": "2024-01-20T14:30:00Z",
      "impact_score": 8.5,
      "recommendations": [
        "Ajouter un index sur la colonne email",
        "Éviter les recherches avec LIKE commençant par %",
        "Utiliser la recherche plein texte si disponible"
      ]
    },
    {
      "query_hash": "hash-uuid-2",
      "query": "SELECT c.*, p.* FROM project_1_clients c LEFT JOIN project_1_projects p ON c.project_id = p.id",
      "execution_count": 25,
      "average_time_ms": 850,
      "total_time_ms": 21250,
      "impact_score": 6.2,
      "recommendations": [
        "Sélectionner uniquement les colonnes nécessaires",
        "Vérifier les index sur les colonnes de jointure"
      ]
    }
  ],
  "summary": {
    "total_slow_queries": 8,
    "total_slow_executions": 125,
    "impact_on_performance_percentage": 15.2
  }
}
```

---

## 📋 **Export de Données**

### POST `/export/`
**Exporter des données analytics**

**Requête :**
```json
{
  "export_type": "user_activity",
  "format": "csv",
  "filters": {
    "date_from": "2024-01-01",
    "date_to": "2024-01-20",
    "project_id": "project-uuid-here",
    "user_id": 123
  },
  "fields": [
    "timestamp",
    "user_email",
    "event_name",
    "properties",
    "context.ip_address"
  ],
  "options": {
    "include_headers": true,
    "date_format": "YYYY-MM-DD HH:mm:ss",
    "compression": "gzip"
  }
}
```

**Réponse (202) :**
```json
{
  "export_id": "export-uuid-here",
  "status": "processing",
  "estimated_completion_time": "2-3 minutes",
  "download_url": null,
  "file_size_estimate_mb": 15.2,
  "created_at": "2024-01-20T15:30:00Z"
}
```

**Types d'export :**
- `user_activity` : Activités utilisateur
- `system_metrics` : Métriques système
- `application_performance` : Performance applicative
- `error_logs` : Journaux d'erreurs
- `usage_statistics` : Statistiques d'utilisation

---

### GET `/export/{export_id}/status/`
**Statut d'un export**

**Réponse (200) :**
```json
{
  "export_id": "export-uuid-here",
  "status": "completed",
  "progress_percentage": 100,
  "created_at": "2024-01-20T15:30:00Z",
  "completed_at": "2024-01-20T15:32:45Z",
  "file_info": {
    "filename": "user_activity_2024-01-01_to_2024-01-20.csv",
    "size_bytes": 15974400,
    "size_mb": 15.2,
    "format": "csv",
    "compression": "gzip",
    "records_count": 1250
  },
  "download_url": "https://api.nocode-platform.com/api/v1/insights/export/export-uuid-here/download/",
  "expires_at": "2024-01-27T15:32:45Z"
}
```

---

### GET `/export/{export_id}/download/`
**Télécharger un fichier d'export**

**Headers :**
```http
Authorization: Bearer <access_token>
```

**Réponse (200) :**
- **Content-Type** : application/octet-stream
- **Content-Disposition** : attachment; filename="export.csv.gz"
- **Body** : Fichier binaire compressé

---

## 🧪 **Tests et Validation**

### POST `/track/test/`
**Tester le tracking d'événements**

**Requête :**
```json
{
  "test_events": [
    {
      "event_type": "user_action",
      "event_name": "test_action",
      "properties": {
        "test": true,
        "user_id": 999
      }
    }
  ],
  "dry_run": true,
  "validate_schema": true
}
```

**Réponse (200) :**
```json
{
  "test_results": {
    "events_processed": 1,
    "validation_passed": true,
    "estimated_storage_impact_bytes": 512,
    "processing_time_ms": 15
  },
  "validation_details": {
    "schema_valid": true,
    "required_fields_present": true,
    "data_types_correct": true,
    "no_sensitive_data": true
  }
}
```

---

## 🔄 **Exemples d'Intégration**

### JavaScript Client pour Tracking
```javascript
class InsightsAPI {
    constructor(baseURL, token) {
        this.baseURL = baseURL;
        this.token = token;
        this.batchEvents = [];
        this.batchTimeout = null;
    }

    async track(eventType, eventName, properties = {}, context = {}) {
        const event = {
            event_type: eventType,
            event_name: eventName,
            properties: {
                ...properties,
                timestamp: new Date().toISOString()
            },
            context: {
                ...context,
                user_agent: navigator.userAgent,
                page: window.location.pathname
            }
        };

        // Ajouter au batch pour envoi différé
        this.batchEvents.push(event);
        
        if (this.batchEvents.length >= 10) {
            await this.flushBatch();
        } else if (!this.batchTimeout) {
            this.batchTimeout = setTimeout(() => this.flushBatch(), 5000);
        }
    }

    async flushBatch() {
        if (this.batchEvents.length === 0) return;

        try {
            const response = await fetch(`${this.baseURL}/api/v1/insights/track/batch/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    events: this.batchEvents
                })
            });

            this.batchEvents = [];
            clearTimeout(this.batchTimeout);
            this.batchTimeout = null;

            return response.json();
        } catch (error) {
            console.error('Failed to send events batch:', error);
        }
    }

    async getAnalytics(filters = {}) {
        const params = new URLSearchParams(filters);
        const response = await fetch(
            `${this.baseURL}/api/v1/insights/analytics/?${params}`,
            {
                headers: { 'Authorization': `Bearer ${this.token}` }
            }
        );
        return response.json();
    }

    async exportData(exportConfig) {
        const response = await fetch(`${this.baseURL}/api/v1/insights/export/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(exportConfig)
        });
        return response.json();
    }
}

// Utilisation dans une application React
const insights = new InsightsAPI('https://api.nocode-platform.com', token);

// Tracker des actions utilisateur
insights.track('user_action', 'client_created', {
    client_id: 456,
    client_email: 'newclient@example.com'
});

// Tracker des vues de page
insights.track('page_view', 'dashboard_viewed', {
    page: '/dashboard',
    duration_seconds: 45
});

// Analytics dashboard
const analytics = await insights.getAnalytics({
    period: '30d',
    project_id: 'project-uuid-here'
});
```

### React Hook pour Analytics
```jsx
import { useState, useEffect } from 'react';

function useAnalytics(filters = {}) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadAnalytics = async (newFilters = {}) => {
        try {
            setLoading(true);
            const params = { ...filters, ...newFilters };
            const response = await fetch(
                `/api/v1/insights/analytics/?${new URLSearchParams(params)}`,
                {
                    headers: { 'Authorization': `Bearer ${token}` }
                }
            );
            const result = await response.json();
            setData(result);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadAnalytics();
    }, [filters]);

    return {
        data,
        loading,
        error,
        refresh: () => loadAnalytics(),
        updateFilters: (newFilters) => loadAnalytics(newFilters)
    };
}

// Composant Dashboard Analytics
function AnalyticsDashboard({ projectId }) {
    const { data, loading, error, refresh } = useAnalytics({
        project_id: projectId,
        period: '30d'
    });

    if (loading) return <div>Chargement des analytics...</div>;
    if (error) return <div>Erreur: {error}</div>;

    return (
        <div className="analytics-dashboard">
            <div className="overview">
                <h3>Vue d'ensemble</h3>
                <div className="metrics-grid">
                    <div className="metric">
                        <h4>Utilisateurs actifs</h4>
                        <span className="value">{data.overview.active_users}</span>
                    </div>
                    <div className="metric">
                        <h4>Requêtes totales</h4>
                        <span className="value">{data.overview.total_requests}</span>
                    </div>
                    <div className="metric">
                        <h4>Temps de réponse moyen</h4>
                        <span className="value">{data.overview.average_response_time_ms}ms</span>
                    </div>
                    <div className="metric">
                        <h4>Taux d'erreur</h4>
                        <span className="value">{data.overview.error_rate_percentage}%</span>
                    </div>
                </div>
            </div>

            <div className="charts">
                <h3>Évolution sur 30 jours</h3>
                <LineChart data={data.time_series} />
            </div>

            <div className="top-metrics">
                <h3>Top métriques</h3>
                <div className="top-lists">
                    <div>
                        <h4>Utilisateurs les plus actifs</h4>
                        <ul>
                            {data.top_metrics.most_active_users.map(user => (
                                <li key={user.user_id}>
                                    {user.email} - {user.actions_count} actions
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
}
```

---

## 📊 **Monitoring et Alertes**

### Configuration d'Alertes
```json
{
  "alert_rules": [
    {
      "name": "High CPU Usage",
      "metric": "cpu.usage_percentage",
      "operator": ">",
      "threshold": 80,
      "duration_minutes": 5,
      "severity": "warning",
      "notification_channels": ["email", "slack"]
    },
    {
      "name": "Error Rate Spike",
      "metric": "application.error_rate_percentage",
      "operator": ">",
      "threshold": 5,
      "duration_minutes": 2,
      "severity": "critical",
      "notification_channels": ["email", "slack", "sms"]
    }
  ]
}
```

---

## 🚨 **Codes d'Erreur**

| Code | Message | Contexte |
|------|---------|----------|
| `INSIGHTS_001` | "Type d'événement invalide" | Tracking event |
| `INSIGHTS_002` | "Propriétés requises manquantes" | Event validation |
| `INSIGHTS_003` | "Période d'analyse invalide" | Analytics request |
| `INSIGHTS_004` | "Export en cours" | Duplicate export |
| `INSIGHTS_005` | "Fichier d'export expiré" | Download attempt |
| `INSIGHTS_006` | "Limite de stockage atteinte" | Event storage |
| `INSIGHTS_007` | "Métrique non disponible" | System metrics |

---

*Documentation Insights API - Version 1.0*
