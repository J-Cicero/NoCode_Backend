# 🐳 Docker Deployment Guide - NoCode Backend

## 🎯 Vue d'ensemble

Ce guide explique comment déployer l'application NoCode Backend **avec** le code source complet, incluant les 5 services Docker : web, db, redis, celery, celery-beat.

---

## 📋 Architecture des Services

### Services Principaux
- **web** : Application Django (API REST + Admin)
- **db** : PostgreSQL (base de données principale)
- **redis** : Redis (cache + broker Celery)
- **celery** : Worker pour tâches asynchrones
- **celery-beat** : Scheduler pour tâches planifiées

### Communication Inter-Services
```
web ↔ db (port 5432)
web ↔ redis (port 6379)
celery ↔ db (port 5432)
celery ↔ redis (port 6379)
celery-beat ↔ redis (port 6379)
```

---

## 📋 Prérequis

- **Docker** 20.10+ et **Docker Compose** 2.0+
- **Code source** du projet NoCode Backend
- **Ports disponibles** : 8000, 5432, 6379
- **4GB+ RAM** recommandée (5 services)
- **10GB+ espace disque** pour les données

---

## 🚀 Déploiement Rapide (Production)

### 1. Télécharger docker-compose.prod.yml

Créez un fichier `docker-compose.prod.yml` avec le contenu suivant :

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: nocode_db_prod
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - nocode_network

  redis:
    image: redis:7-alpine
    container_name: nocode_redis_prod
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_prod_data:/data
    restart: unless-stopped
    networks:
      - nocode_network

  web:
    build: .
    container_name: nocode_web_prod
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS}
      - CREATE_SUPERUSER=${CREATE_SUPERUSER}
      - SUPERUSER_EMAIL=${SUPERUSER_EMAIL}
      - SUPERUSER_PASSWORD=${SUPERUSER_PASSWORD}
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - nocode_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/foundation/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery:
    build: .
    container_name: nocode_celery_prod
    command: celery -A config worker -l info --concurrency=4
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      - db
      - redis
    restart: unless-stopped
    networks:
      - nocode_network

  celery-beat:
    build: .
    container_name: nocode_celery_beat_prod
    command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      - db
      - redis
    restart: unless-stopped
    networks:
      - nocode_network

volumes:
  postgres_prod_data:
  redis_prod_data:

networks:
  nocode_network:
    driver: bridge
```

### 2. Créer le fichier .env

Créez un fichier `.env` avec vos variables d'environnement :

```bash
# Base de données PostgreSQL
POSTGRES_DB=nocode_prod
POSTGRES_USER=nocode_user
POSTGRES_PASSWORD=votre_mot_de_passe_db_tres_securise

# Redis
REDIS_PASSWORD=votre_mot_de_passe_redis_tres_securise

# Application Django
SECRET_KEY=votre_secret_key_django_tres_long_et_aleatoire
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com,localhost
CORS_ALLOWED_ORIGINS=https://votre-domaine.com,https://www.votre-domaine.com

# Superutilisateur (optionnel)
CREATE_SUPERUSER=True
SUPERUSER_EMAIL=admin@votre-domaine.com
SUPERUSER_PASSWORD=votre_mot_de_passe_admin

# Domaine pour les emails
DOMAIN_NAME=votre-domaine.com
```

### 3. Lancer l'application

```bash
# Télécharger et démarrer tous les services
docker-compose -f docker-compose.prod.yml up -d

# Voir les logs de démarrage
docker-compose -f docker-compose.prod.yml logs -f

# Vérifier l'état des services
docker-compose -f docker-compose.prod.yml ps
```

### 4. Vérifier le déploiement

```bash
# Tester l'API
curl http://localhost:8000/api/v1/foundation/health/

# Accéder à la documentation
# http://localhost:8000/api/docs/
# http://localhost:8000/api/redoc/
```

---

## 🔧 Configuration Avancée

### Variables d'Environnement

| Variable | Requise | Description | Exemple |
|----------|---------|-------------|---------|
| `DEBUG` | Oui | Mode debug (False en prod) | `False` |
| `SECRET_KEY` | Oui | Clé secrète Django | `django-insecure-...` |
| `DATABASE_URL` | Oui | URL de base de données | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | Oui | URL Redis | `redis://:password@host:6379/0` |
| `ALLOWED_HOSTS` | Oui | Hosts autorisés | `domain.com,www.domain.com` |
| `CORS_ALLOWED_ORIGINS` | Oui | Origines CORS autorisées | `https://domain.com` |
| `CREATE_SUPERUSER` | Non | Créer auto superuser | `True` |
| `SUPERUSER_EMAIL` | Non | Email superuser | `admin@domain.com` |
| `SUPERUSER_PASSWORD` | Non | Password superuser | `secure_password` |

### Configuration SSL avec Nginx

Créez un fichier `nginx.conf` :

```nginx
events {
    worker_connections 1024;
}

http {
    upstream app {
        server web:8000;
    }

    server {
        listen 80;
        server_name votre-domaine.com www.votre-domaine.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name votre-domaine.com www.votre-domaine.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /static/ {
            alias /app/staticfiles/;
        }

        location /media/ {
            alias /app/media/;
        }
    }
}
```

---

## 📊 Monitoring et Logs

### Consulter les logs

```bash
# Logs de tous les services
docker-compose -f docker-compose.prod.yml logs

# Logs d'un service spécifique
docker-compose -f docker-compose.prod.yml logs web
docker-compose -f docker-compose.prod.yml logs db
docker-compose -f docker-compose.prod.yml logs celery

# Logs en temps réel
docker-compose -f docker-compose.prod.yml logs -f web
```

### Monitoring de santé

```bash
# État des conteneurs
docker-compose -f docker-compose.prod.yml ps

# Utilisation des ressources
docker stats

# Health checks détaillés
docker inspect nocode_web_prod | grep Health -A 10
```

---

## 🔄 Mises à Jour

### Mettre à jour l'application

```bash
# Télécharger la nouvelle image
docker-compose -f docker-compose.prod.yml pull

# Redémarrer avec la nouvelle image
docker-compose -f docker-compose.prod.yml up -d

# Nettoyer les anciennes images
docker image prune -f
```

### Sauvegardes

```bash
# Sauvegarder la base de données
docker-compose -f docker-compose.prod.yml exec db pg_dump -U nocode_user nocode_prod > backup.sql

# Restaurer la base de données
docker-compose -f docker-compose.prod.yml exec -T db psql -U nocode_user nocode_prod < backup.sql

# Sauvegarder les volumes
docker run --rm -v postgres_prod_data:/data -v $(pwd):/backup ubuntu tar czf /backup/postgres_backup.tar.gz -C /data .
```

---

## 🚨 Dépannage

### Problèmes Communs

#### 1. Le service web ne démarre pas
```bash
# Vérifier les logs
docker-compose -f docker-compose.prod.yml logs web

# Vérifier la connexion à la base de données
docker-compose -f docker-compose.prod.yml exec web python manage.py check --database default
```

#### 2. Erreur de connexion à la base de données
```bash
# Vérifier que la base de données est prête
docker-compose -f docker-compose.prod.yml exec db pg_isready -U nocode_user

# Vérifier les variables d'environnement
docker-compose -f docker-compose.prod.yml exec web env | grep DATABASE
```

#### 3. Les migrations ne s'appliquent pas
```bash
# Exécuter les migrations manuellement
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Vérifier l'état des migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py showmigrations
```

#### 4. Problèmes de mémoire
```bash
# Augmenter la mémoire swap dans docker-compose.yml
services:
  web:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

### Commandes Utiles

```bash
# Redémarrer un service
docker-compose -f docker-compose.prod.yml restart web

# Reconstruire un service
docker-compose -f docker-compose.prod.yml up --build web

# Accéder au shell d'un conteneur
docker-compose -f docker-compose.prod.yml exec web bash

# Supprimer tout et recommencer
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🔒 Sécurité

### Bonnes Pratiques

1. **Mots de passe forts** : Utilisez des mots de passe générés aléatoirement
2. **HTTPS obligatoire** : Configurez SSL en production
3. **Firewall** : N'exposez que les ports nécessaires (80, 443)
4. **Mises à jour** : Maintenez les images Docker à jour
5. **Monitoring** : Surveillez les logs et les métriques

### Configuration Firewall

```bash
# Autoriser HTTP/HTTPS uniquement
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 5432/tcp  # PostgreSQL
sudo ufw deny 6379/tcp  # Redis
sudo ufw enable
```

---

## 📈 Performance

### Optimisations

1. **Worker processes** : Ajustez le nombre de workers selon votre CPU
2. **Database pooling** : Configurez pgbouncer pour les hautes charges
3. **Redis persistence** : Activez AOF pour la persistance des données
4. **Static files** : Utilisez CDN pour les fichiers statiques

### Configuration Production

```yaml
# Dans docker-compose.prod.yml
web:
  environment:
    - GUNICORN_WORKERS=4
    - GUNICORN_WORKER_CLASS=gevent
    - GUNICORN_MAX_REQUESTS=1000
    - GUNICORN_MAX_REQUESTS_JITTER=100
```

---

## 🆘 Support

### En cas de problème

1. **Consultez les logs** : `docker-compose logs`
2. **Vérifiez la documentation** : `/api/docs/`
3. **Testez les health checks** : `/api/v1/foundation/health/`
4. **Contactez le support** avec les logs détaillés

### Informations à collecter

```bash
# Version Docker
docker --version
docker-compose --version

# État des services
docker-compose -f docker-compose.prod.yml ps

# Logs complets
docker-compose -f docker-compose.prod.yml logs > nocode-logs.txt

# Configuration système
docker info > docker-info.txt
```

---

*Guide de déploiement Docker - Version 1.0*
