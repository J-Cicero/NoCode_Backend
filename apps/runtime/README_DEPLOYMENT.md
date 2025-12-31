# Guide de Déploiement - Module Runtime

## Vue d'ensemble

Le module Runtime permet de déployer automatiquement les applications NoCode générées via plusieurs stratégies :

1. **Local** : Génération de fichiers uniquement (développement)
2. **Docker** : Déploiement dans des conteneurs isolés (recommandé)
3. **Kubernetes** : Déploiement en production (à venir)

## Déploiement Docker (Recommandé)

### Prérequis

- Docker installé : `docker --version`
- Docker Compose installé : `docker-compose --version`

### Architecture

Chaque application NoCode est déployée dans :
- **1 conteneur web** : Application Django + API REST
- **1 conteneur PostgreSQL** : Base de données dédiée
- **Volumes** : Pour les fichiers statiques, médias et logs
- **Réseau isolé** : Communication sécurisée entre conteneurs

### Ports Dynamiques

Chaque application reçoit un port unique calculé automatiquement :
```
Port = 8000 + (hash(project_id) % 1000)
```

Exemple : Application avec `project_id = abc-123` → Port `8456`

### Processus de Déploiement

```python
from apps.runtime.models import GeneratedApp

# 1. Créer une application générée
app = GeneratedApp.objects.create(
    project=my_project,
    name="Mon Application",
    deployment_target='docker'
)

# 2. Déployer
success = app.deploy()

# 3. Vérifier le statut
status = app.deployment_logs.last()
print(status.status)  # 'completed'

# 4. Accéder à l'application
print(app.api_base_url)  # http://localhost:8456/api/v1/
print(app.admin_url)      # http://localhost:8456/admin/
```

### Structure Générée

Pour chaque application, le système génère :

```
generated_apps/
└── app_{project_id}/
    ├── Dockerfile              # Image Docker
    ├── docker-compose.yml      # Orchestration
    ├── entrypoint.sh          # Script de démarrage
    ├── requirements.txt       # Dépendances Python
    ├── models.py              # Modèles Django générés
    ├── serializers.py         # Serializers DRF
    ├── views.py               # ViewSets API
    ├── urls.py                # Routes API
    ├── apps.py                # Configuration Django
    ├── admin.py               # Interface admin
    ├── __init__.py
    ├── static/                # Fichiers statiques
    ├── media/                 # Fichiers uploadés
    └── logs/                  # Logs applicatifs
```

### Commandes Docker Utiles

#### Voir les conteneurs actifs
```bash
docker ps | grep nocode
```

#### Voir les logs d'une application
```bash
cd generated_apps/app_{project_id}
docker-compose logs -f web
```

#### Arrêter une application
```bash
cd generated_apps/app_{project_id}
docker-compose down
```

#### Redémarrer une application
```bash
cd generated_apps/app_{project_id}
docker-compose restart
```

#### Accéder au shell du conteneur
```bash
docker exec -it nocode_app_{project_id} bash
```

## API de Déploiement

### Endpoints

#### Déployer une application
```http
POST /api/v1/runtime/apps/{id}/deploy/
```

**Réponse :**
```json
{
  "status": "success",
  "message": "Application déployée avec succès",
  "app_url": "http://localhost:8456/api/v1/",
  "admin_url": "http://localhost:8456/admin/"
}
```

#### Obtenir le statut
```http
GET /api/v1/runtime/apps/{id}/status/
```

**Réponse :**
```json
{
  "status": "running",
  "container": {
    "Service": "web",
    "State": "running",
    "Health": "healthy"
  }
}
```

#### Obtenir les logs
```http
GET /api/v1/runtime/apps/{id}/logs/?lines=100
```

**Réponse :**
```json
{
  "logs": [
    "2025-01-01 10:00:00 [INFO] Application démarrée",
    "2025-01-01 10:00:01 [INFO] Migrations appliquées",
    "..."
  ]
}
```

## Variables d'Environnement

### Dans le conteneur

Les variables suivantes sont automatiquement configurées :

- `DATABASE_URL` : Connexion PostgreSQL
- `DJANGO_SECRET_KEY` : Clé secrète Django
- `DJANGO_DEBUG` : Mode debug (False en production)
- `ALLOWED_HOSTS` : Hôtes autorisés

### Personnalisation

Modifiez `docker-compose.yml` pour ajouter vos variables :

```yaml
environment:
  - MY_API_KEY=xxxxx
  - STRIPE_SECRET_KEY=sk_test_xxxxx
```

## Gestion des Bases de Données

### PostgreSQL Isolé

Chaque application a sa propre base PostgreSQL :
- **Nom de la base** : `app_{project_id}`
- **Utilisateur** : `nocode`
- **Mot de passe** : `nocode` (à changer en production)

### Migrations Automatiques

Les migrations sont appliquées automatiquement au démarrage via `entrypoint.sh`.

### Backup Manuel

```bash
docker exec nocode_app_{project_id}_db pg_dump -U nocode app_{project_id} > backup.sql
```

### Restauration

```bash
cat backup.sql | docker exec -i nocode_app_{project_id}_db psql -U nocode -d app_{project_id}
```

## Monitoring et Logs

### Logs en Temps Réel

```bash
# Via Docker Compose
docker-compose logs -f web

# Via Python/API
from apps.runtime.services.docker_deployment import DockerDeploymentService
service = DockerDeploymentService(app)
logs = service.get_logs(lines=100)
```

### Santé du Conteneur

```bash
docker inspect nocode_app_{project_id} | grep Health
```

## Scaling et Performance

### Augmenter les Workers Gunicorn

Modifiez le `CMD` dans le Dockerfile :

```dockerfile
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "5"]
```

### Limiter les Ressources

Ajoutez dans `docker-compose.yml` :

```yaml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
```

## Sécurité

### En Production

1. **Changer le secret Django** :
   ```yaml
   environment:
     - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
   ```

2. **Changer le mot de passe PostgreSQL** :
   ```yaml
   environment:
     - POSTGRES_PASSWORD=${DB_PASSWORD}
   ```

3. **Limiter ALLOWED_HOSTS** :
   ```yaml
   environment:
     - ALLOWED_HOSTS=mondomaine.com,www.mondomaine.com
   ```

4. **Utiliser HTTPS** :
   Ajoutez un reverse proxy (Nginx, Traefik) devant les conteneurs.

## Dépannage

### Le conteneur ne démarre pas

```bash
# Vérifier les logs
docker-compose logs web

# Vérifier la base de données
docker-compose logs db

# Reconstruire l'image
docker-compose build --no-cache
```

### Erreur de connexion à la base

```bash
# Vérifier que la base est prête
docker exec nocode_app_{project_id}_db pg_isready

# Redémarrer la base
docker-compose restart db
```

### Port déjà utilisé

Modifiez le port dans `docker-compose.yml` :

```yaml
ports:
  - "8001:8000"  # Utiliser 8001 au lieu du port calculé
```

## Migration vers Kubernetes (Futur)

Le système est conçu pour faciliter la migration vers Kubernetes :

1. Les images Docker sont déjà créées
2. Les variables d'environnement sont externalisées
3. Les volumes sont isolés

Un `deployment.yaml` sera généré automatiquement lors de l'activation du support Kubernetes.

## Support

Pour toute question ou problème :
1. Vérifiez les logs : `docker-compose logs`
2. Consultez la documentation Django/Docker
3. Créez une issue sur le projet
