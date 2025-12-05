# 🏗️ Docker Services Architecture - NoCode Backend

## 🎯 Vue d'ensemble

L'architecture NoCode Backend repose sur **5 services Docker** qui collaborent pour fournir une plateforme complète de création d'API dynamique.

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│     Web     │  │   Redis     │  │   Celery    │
│  (Django +  │  │   (Cache +  │  │   (Worker)  │
│  Gunicorn)  │──│   Broker)   │──│             │
│   Port 8000 │  │   Port 6379 │  │   No Port   │
└─────────────┘  └─────────────┘  └─────────────┘
       │                │                │
       │                │                │
       ▼                ▼                ▼
┌─────────────────┐  ┌─────────────────┐
│   PostgreSQL    │  │  Celery Beat    │
│   (Base de      │  │   (Scheduler)   │
│    données)     │  │                 │
│    Port 5432    │  │   No Port       │
└─────────────────┘  └─────────────────┘
```

---

## 📊 Services Détaillés

### 1. **Web Service** - Django + Gunicorn

**Rôle principal :** Serveur d'application Django

**Configuration :**
```yaml
web:
  build: .
  command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
  environment:
    - DEBUG=False
    - DATABASE_URL=postgresql://user:pass@db:5432/nocode
    - REDIS_URL=redis://redis:6379/0
    - CELERY_BROKER_URL=redis://redis:6379/0
```

**Responsabilités :**
- **API REST** : Gère tous les endpoints HTTP (80+ endpoints)
- **Authentification JWT** : Tokens et permissions
- **CRUD Dynamique** : Création/mise à jour des tables
- **Validation** : Schémas et contraintes de données
- **Middleware** : CORS, sécurité, logging
- **Admin Django** : Interface d'administration

**Processus internes :**
```
Request → Gunicorn → Django → Response
          ↓
    API Calls → Django → Database/Redis
          ↓
    Static Files → Django Static Files
```

**Ports exposés :**
- `8000` : API REST + Admin Django
- **Aucun port reverse proxy** (direct Gunicorn)

**Volumes montés :**
- `./static` : Fichiers statiques Django
- `./media` : Fichiers uploadés
- `./logs` : Logs d'application

---

### 2. **Database Service** - PostgreSQL

**Rôle principal :** Base de données principale

**Configuration :**
```yaml
db:
  image: postgres:15-alpine
  environment:
    - POSTGRES_DB=nocode_backend
    - POSTGRES_USER=nocode_user
    - POSTGRES_PASSWORD=secure_password
  volumes:
    - postgres_data:/var/lib/postgresql/data
```

**Responsabilités :**
- **Données utilisateur** : Comptes, organisations, permissions
- **Projets NoCode** : Schémas, configurations
- **Tables dynamiques** : Données utilisateur avec préfixes `project_{id}_`
- **Sessions** : Stockage des sessions Django
- **Tâches Celery** : Queue et résultats des tâches

**Structure des tables :**
```sql
-- Tables système
users, organizations, projects, data_schemas

-- Tables dynamiques (créées automatiquement)
project_1_clients, project_1_produits
project_2_orders, project_2_customers
```

---

### 3. **Redis Service** - Cache + Message Broker

**Rôle principal :** Cache et broker pour Celery

**Configuration :**
```yaml
redis:
  image: redis:7-alpine
  command: redis-server --requirepass redis_password
  volumes:
    - redis_data:/data
```

**Responsabilités :**
- **Cache Django** : Sessions, fragments de vue
- **Cache API** : Réponses fréquentes, métadonnées
- **Message Broker** : Queue pour Celery
- **Real-time** : WebSocket, notifications
- **Rate Limiting** : Limitation de débit API

**Patterns Redis utilisés :**
```
cache:project:{id} → Métadonnées projet
cache:schema:{table} → Configuration table
celery:task:{id} → Résultats tâches
session:{key} → Sessions utilisateur
```

---

### 4. **Celery Service** - Worker Asynchrone

**Rôle principal :** Exécution des tâches en arrière-plan

**Configuration :**
```yaml
celery:
  build: .
  command: celery -A config worker -l info --concurrency=4
  environment:
    - DATABASE_URL=postgresql://user:pass@db:5432/nocode
    - CELERY_BROKER_URL=redis://redis:6379/0
```

**Responsabilités :**
- **Génération d'applications** : Création des modèles Django
- **Déploiement Runtime** : Mise en production des apps
- **Workflows Automation** : Exécution des graphes
- **Analytics Processing** : Agrégation des métriques
- **Email Notifications** : Envoi d'emails asynchrones
- **File Processing** : Upload, conversion, export

**Types de tâches :**
```python
# Tâches de génération
generate_application(project_id)
deploy_application(app_id)

# Tâches automation
execute_workflow(workflow_id, data)
process_integration(integration_id)

# Tâches analytics
process_events_batch(event_data)
generate_analytics_report(project_id)
```

---

### 5. **Celery Beat Service** - Scheduler

**Rôle principal :** Planification des tâches récurrentes

**Configuration :**
```yaml
celery-beat:
  build: .
  command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
  environment:
    - DATABASE_URL=postgresql://user:pass@db:5432/nocode
    - CELERY_BROKER_URL=redis://redis:6379/0
```

**Responsabilités :**
- **Tâches planifiées** : Rapports quotidiens/hebdomadaires
- **Maintenance** : Nettoyage des logs, cache
- **Analytics** : Agrégations périodiques
- **Notifications** : Rappels, alertes
- **Backup** : Sauvegardes automatiques

**Schedule types :**
```python
# Tâches quotidiennes
daily_analytics_report → 00:00 UTC
cleanup_old_sessions → 02:00 UTC

# Tâches hebdomadaires
weekly_usage_report → Lundi 08:00 UTC
database_maintenance → Dimanche 03:00 UTC

# Tâches mensuelles
monthly_billing_report → 1er du mois
```

---

### 2. **PostgreSQL** - Base de données principale

**Rôle principal :** Stockage persistant des données

**Configuration :**
```yaml
db:
  image: postgres:15-alpine
  environment:
    POSTGRES_DB: nocode_prod
    POSTGRES_USER: nocode_user
    POSTGRES_PASSWORD: secure_password
  volumes:
    - postgres_data:/var/lib/postgresql/data
```

**Structure des données :**
```sql
-- Tables Django (fixes)
django_migrations
auth_user
foundation_organization
studio_dataschema
studio_fieldschema

-- Tables dynamiques (créées à l'exécution)
project_{uuid}_products
project_{uuid}_customers
project_{uuid}_tasks
```

**Responsabilités :**
- **Données utilisateur** : Authentification, organisations
- **Métadonnées** : Schémas de tables, définitions de champs
- **Données dynamiques** : Tables créées par les utilisateurs
- **Transactions** : ACID compliance pour la cohérence
- **Persistance** : Sauvegarde et récupération

**Performance :**
- **Indexation automatique** sur les clés primaires
- **Connections pooling** via Django
- **Health checks** pour monitoring

---

### 3. **Redis** - Cache et Message Broker

**Rôle principal :** Cache et file d'attente pour tâches asynchrones

**Configuration :**
```yaml
redis:
  image: redis:7-alpine
  command: redis-server --requirepass secure_password
  volumes:
    - redis_data:/data
```

**Utilisations multiples :**

#### 🗄️ **Cache Django**
```python
# Cache des schémas fréquemment accédés
CACHE_KEY = "project_{uuid}_schema"
TTL = 3600  # 1 heure

# Cache des permissions utilisateur
CACHE_KEY = "user_{user_id}_permissions"
TTL = 1800  # 30 minutes
```

#### 📨 **Celery Message Broker**
```python
# File d'attente des tâches
CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_RESULT_BACKEND = "redis://redis:6379/0"

# Types de tâches
- backup_database
- generate_report
- send_notifications
- cleanup_temp_files
```

#### 🔄 **Session Storage**
```python
# Sessions utilisateur (optionnel)
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
```

---

### 4. **Celery Worker** - Tâches asynchrones

**Rôle principal :** Exécution des tâches en arrière-plan

**Configuration :**
```yaml
celery:
  image: your-dockerhub-username/nocode-backend:latest
  command: celery -A config worker -l info --concurrency=4
  environment:
    - DATABASE_URL=postgresql://user:pass@db:5432/nocode
    - CELERY_BROKER_URL=redis://redis:6379/0
```

**Types de tâches :**

#### 📊 **Tâches de traitement**
```python
@shared_task
def generate_project_report(project_id, format="pdf"):
    """Générer un rapport de projet"""
    # Récupérer les données
    # Générer le PDF/Excel
    # Envoyer par email
    pass

@shared_task
def backup_project_data(project_id):
    """Sauvegarder les données d'un projet"""
    # Exporter toutes les tables
    # Compresser l'archive
    # Stocker sur S3/FTP
    pass
```

#### 🔔 **Tâches de notification**
```python
@shared_task
def send_welcome_email(user_id):
    """Envoyer email de bienvenue"""
    pass

@shared_task
def notify_project_changes(project_id, changes):
    """Notifier les modifications"""
    pass
```

#### 🧹 **Tâches de maintenance**
```python
@shared_task
def cleanup_old_sessions():
    """Nettoyer les anciennes sessions"""
    pass

@shared_task
def update_project_statistics():
    """Mettre à jour les statistiques"""
    pass
```

---

### 5. **Celery Beat** - Planificateur de tâches

**Rôle principal :** Exécution planifiée des tâches récurrentes

**Configuration :**
```yaml
celery-beat:
  image: your-dockerhub-username/nocode-backend:latest
  command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

**Tâches planifiées :**

```python
# Tâches quotidiennes
0 2 * * *   → backup_all_projects()      # 2h du matin
0 3 * * *   → cleanup_temp_files()       # 3h du matin
0 4 * * *   → update_analytics()         # 4h du matin

# Tâches hebdomadaires  
0 6 * * 1   → generate_weekly_report()   # Lundi 6h
0 7 * * 1   → system_health_check()      # Lundi 7h

# Tâches mensuelles
0 8 1 * *   → monthly_usage_report()     # 1er du mois 8h
```

---

## 🔄 Communication Entre Services

### Flow de Requête API

```
1. Client → Nginx (Port 80/443)
2. Nginx → Web Service (Port 8000)
3. Web → Redis (Cache/Permissions)
4. Web → PostgreSQL (Données)
5. Web → Redis (Celery Queue) [si tâche async]
6. Celery Worker → Redis (prend tâche)
7. Celery Worker → PostgreSQL (exécute tâche)
```

### Flow de Tâche Asynchrone

```
1. API POST /api/v1/automation/tasks/
2. Web Service → Redis Queue (task_data)
3. Celery Worker → Redis (prend tâche)
4. Celery Worker → PostgreSQL (traitement)
5. Celery Worker → Redis (resultat)
6. Client → API GET /api/v1/automation/tasks/{id}/status/
```

### Flow de Cache

```
1. Request API → Web Service
2. Web Service → Redis (vérifie cache)
3. Si HIT: Retourne données cachees
4. Si MISS: 
   - Web Service → PostgreSQL
   - PostgreSQL → Web Service  
   - Web Service → Redis (stocke cache)
   - Web Service → Client
```

---

## 📁 Volumes et Persistance

### Volumes PostgreSQL
```yaml
volumes:
  postgres_data:
    driver: local
    # Contient: 
    # - Données utilisateur
    # - Tables dynamiques
    # - Métadonnées Django
```

### Volumes Redis
```yaml
volumes:
  redis_data:
    driver: local
    # Contient:
    # - Cache persistant
    # - Files d'attente Celery
    # - Sessions utilisateur
```

### Volumes Application
```yaml
volumes:
  static_files:
    # Fichiers statiques collectés
  media_files:
    # Uploads utilisateurs
  logs:
    # Logs applicatifs
```

---

## 🌐 Réseaux Docker

### Architecture réseau
```yaml
networks:
  nocode_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Communication inter-services
```bash
# Résolution DNS automatique
web → db:5432          # PostgreSQL
web → redis:6379       # Redis
celery → db:5432       # PostgreSQL  
celery → redis:6379    # Redis
nginx → web:8000       # Django
```

### Sécurité réseau
```yaml
# Seul Nginx expose des ports publics
ports:
  - "80:80"     # Nginx HTTP
  - "443:443"   # Nginx HTTPS
  
# Services internes uniquement
# db:5432, redis:6379, web:8000 non exposés
```

---

## 📊 Monitoring et Health Checks

### Health Checks par service

#### Web Service
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/foundation/health/"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

#### PostgreSQL
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U nocode_user"]
  interval: 10s
  timeout: 5s
  retries: 5
```

#### Redis
```yaml
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 10s
  timeout: 5s
  retries: 3
```

### Metrics collectées

#### Application Metrics
```python
# API Metrics
- Requests par minute
- Temps de réponse moyen
- Taux d'erreur 4xx/5xx
- Utilisateurs actifs

# Business Metrics  
- Nombre de projets
- Tables créées par jour
- Volume de données stockées
- Tâches Celery exécutées
```

#### Infrastructure Metrics
```bash
# Docker Stats
CPU Usage par conteneur
Memory Usage par conteneur
Network I/O
Disk I/O

# PostgreSQL
Connections actives
Query performance
Database size
Index usage

# Redis
Memory usage
Keyspace hits/misses
Connected clients
Queue length
```

---

## 🚨 Gestion des Erreurs

### Stratégies de retry

#### Celery Tasks
```python
@app.task(bind=True, max_retries=3)
def unreliable_task(self, data):
    try:
        # Logique métier
        pass
    except Exception as exc:
        # Retry avec backoff exponentiel
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

#### Database Connections
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'connect_timeout': 10,
            'MAX_CONNS': 20,
            'RETRY_ATTEMPTS': 3
        }
    }
}
```

### Logging Strategy

#### Structure des logs
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '{"level": "%(levelname)s", "time": "%(asctime)s", "service": "web", "message": "%(message)s"}'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
}
```

#### Logs par service
```bash
# Web Service logs
docker-compose logs web | grep "ERROR\|WARNING"

# Database logs  
docker-compose logs db | grep "ERROR\|FATAL"

# Celery task logs
docker-compose logs celery | grep "FAILED\|RETRY"
```

---

## 🔧 Optimisations et Performance

### Scaling Horizontal

#### Web Service Scaling
```yaml
# docker-compose.prod.yml
services:
  web:
    deploy:
      replicas: 3  # 3 instances web
    load_balancing: nginx
  
  celery:
    deploy:
      replicas: 2  # 2 workers
```

#### Database Scaling
```yaml
# Read replicas pour lectures
db_read_replica:
  image: postgres:15-alpine
  environment:
    POSTGRES_MASTER_SERVICE: db
  
# Connection pooling
pgbouncer:
  image: pgbouncer/pgbouncer
  environment:
    DATABASES_HOST: db
    DATABASES_PORT: 5432
```

### Performance Tuning

#### Django Settings
```python
# Database optimization
DATABASES = {
    'default': {
        'CONN_MAX_AGE': 60,
        'OPTIONS': {
            'MAX_CONNS': 20,
            'application_name': 'nocode_backend'
        }
    }
}

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'MAX_CONNECTIONS': 50
        }
    }
}

# Celery optimization
CELERY_WORKER_CONCURRENCY = 4
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True
```

#### Resource Limits
```yaml
services:
  web:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
  
  db:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
```

---

## 🔄 Cycle de Vie des Services

### Démarrage (Startup Order)
```
1. db (PostgreSQL) → Health check ready
2. redis → Health check ready  
3. web → Attend db + redis + migrations
4. celery → Attend db + redis
5. celery-beat → Attend db + redis
6. nginx → Attend web ready
```

### Arrêt (Shutdown Order)
```
1. nginx → Stop nouvelles requêtes
2. web → Finish requêtes en cours
3. celery-beat → Stop planification
4. celery → Finish tâches en cours
5. redis → Flush et stop
6. db → Flush et stop
```

### Mises à jour (Rolling Update)
```
1. Pull nouvelle image
2. Update service par service
3. Health check validation
4. Passer au service suivant
5. Rollback si erreur
```

---

## 📈 Capacité et Limites

### Limites techniques

#### Par projet
- **Tables maximum** : 100 tables
- **Champs par table** : 50 champs
- **Enregistrements** : Illimité (performance dépend de la DB)
- **Stockage** : Limité par le disque

#### Par instance
- **Utilisateurs simultanés** : 1000 (avec 3 workers)
- **Requêtes/second** : ~500 (dépend de la complexité)
- **Tâches Celery** : 100 concurrentes
- **Cache Redis** : 1GB (configurable)

### Scaling recommendations

#### Petites installations (< 100 users)
```yaml
web: 1 worker (1 CPU, 512MB RAM)
celery: 1 worker (1 CPU, 512MB RAM)  
db: 1 CPU, 1GB RAM
redis: 512MB RAM
```

#### Moyennes installations (100-1000 users)
```yaml
web: 3 workers (2 CPU, 2GB RAM)
celery: 2 workers (2 CPU, 2GB RAM)
db: 2 CPU, 4GB RAM
redis: 1GB RAM
```

#### Grandes installations (> 1000 users)
```yaml
web: 5+ workers (4+ CPU, 4GB+ RAM)
celery: 3+ workers (4+ CPU, 4GB+ RAM)
db: Cluster PostgreSQL
redis: Cluster Redis
nginx: Load balancer
```

---

*Documentation de l'architecture Docker - Version 1.0*
