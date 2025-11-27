# 🐳 Docker Deployment Guide - NoCode Platform

## 📋 Overview

Ce guide explique comment déployer la plateforme NoCode avec Docker pour le développement et la production. La configuration inclut Django, PostgreSQL, Redis, Celery Worker, Celery Beat, et Nginx (production).

## 🏗️ Architecture

### Services inclus:
- **Web**: Django application (dev: runserver, prod: gunicorn)
- **DB**: PostgreSQL 15
- **Redis**: Redis 7 pour Celery et cache
- **Celery Worker**: Tâches asynchrones (Automation, Insights, Runtime)
- **Celery Beat**: Tâches planifiées (métriques, nettoyage)
- **Nginx**: Reverse proxy (production uniquement)

## 🚀 Développement Local

### Prérequis
```bash
# Docker et Docker Compose installés
docker --version
docker-compose --version
```

### Démarrage rapide
```bash
# Cloner le projet
git clone <repository-url>
cd NoCode_Backend

# Copier la configuration
cp .env.example .env

# Démarrer tous les services
docker-compose up -d

# Vérifier les services
docker-compose ps
```

### Services disponibles
- **API Django**: http://localhost:8000
- **Admin Django**: http://localhost:8000/admin
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Commandes utiles
```bash
# Voir les logs
docker-compose logs -f web
docker-compose logs -f celery
docker-compose logs -f celery-beat

# Exécuter des migrations
docker-compose exec web python manage.py migrate

# Créer un super utilisateur
docker-compose exec web python manage.py createsuperuser

# Redémarrer un service
docker-compose restart celery

# Arrêter tout
docker-compose down
```

## 🏭 Déploiement Production

### Prérequis
```bash
# Domaine configuré avec DNS
# SSL certficats (Let's Encrypt recommandé)
# Environnement variables configurées
```

### Configuration environnement
```bash
# .env
SECRET_KEY=votre-secret-key-production
DEBUG=False
ALLOWED_HOSTS=votredomaine.com,www.votredomaine.com

# Database
DB_NAME=nocode_production
DB_USER=nocode_user
DB_PASSWORD=votre-password-db
DB_HOST=db

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-app-password

# Frontend
FRONTEND_URL=https://votredomaine.com
SITE_NAME=NoCode Platform
```

### Configuration Nginx
```bash
# docker/nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream django {
        server web:8000;
    }

    server {
        listen 80;
        server_name votredomaine.com www.votredomaine.com;
        
        # Redirection HTTP -> HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name votredomaine.com www.votredomaine.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # Static files
        location /static/ {
            alias /app/staticfiles/;
            expires 30d;
        }

        # Media files
        location /media/ {
            alias /app/media/;
            expires 30d;
        }

        # Django application
        location / {
            proxy_pass http://django;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### Déploiement production
```bash
# Build et démarrage
docker-compose -f docker-compose.prod.yml up -d --build

# Initialisation
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Vérification
docker-compose -f docker-compose.prod.yml ps
```

## 🔧 Configuration Celery

### Tâches planifiées actives
```python
# Toutes les 5 minutes: Collecte métriques système
# Toutes les 10 minutes: Métriques performance
# Tous les jours à minuit: Agrégation métriques quotidiennes
# Tous les jours à 2h: Génération analytics
# Tous les lundis à 3h: Nettoyage logs anciens
# Tous les jours à 4h: Backup métadonnées projets
```

### Monitoring Celery
```bash
# Voir les tâches actives
docker-compose exec celery celery -A config inspect active

# Voir les statistiques
docker-compose exec celery celery -A config inspect stats

# Vider la queue (urgence)
docker-compose exec celery celery -A config purge
```

## 📊 Monitoring et Logs

### Logs par service
```bash
# Application Django
docker-compose logs -f web

# Tâches asynchrones
docker-compose logs -f celery

# Tâches planifiées
docker-compose logs -f celery-beat

# Database
docker-compose logs -f db

# Cache
docker-compose logs -f redis
```

### Health checks
```bash
# Vérifier l'état des services
docker-compose exec web python manage.py check --deploy

# Tester la connexion DB
docker-compose exec web python manage.py dbshell

# Tester Redis
docker-compose exec redis redis-cli ping
```

## 🔒 Sécurité

### Bonnes pratiques
1. **Utiliser des secrets Docker** pour les mots de passe
2. **HTTPS obligatoire** en production
3. **Firewall** configuré pour n'ouvrir que les ports nécessaires
4. **Backups réguliers** de la base de données
5. **Monitoring** des logs d'erreurs

### Commandes de sécurité
```bash
# Lister les secrets
docker secret ls

# Créer un secret
echo "votre-password" | docker secret create db_password -

# Rotater les secrets
docker-compose down
# Mettre à jour .env
docker-compose up -d
```

## 🚨 Dépannage

### Problèmes courants

#### Database connection failed
```bash
# Vérifier que DB est healthy
docker-compose ps db

# Restart DB
docker-compose restart db

# Vérifier les logs DB
docker-compose logs db
```

#### Celery ne traite pas les tâches
```bash
# Restart Celery
docker-compose restart celery

# Vérifier la connexion Redis
docker-compose exec redis redis-cli ping

# Vider les tâches bloquées
docker-compose exec celery celery -A config purge
```

#### Static files non trouvées
```bash
# Regénérer les static files
docker-compose exec web python manage.py collectstatic --noinput

# Vérifier permissions
docker-compose exec web ls -la staticfiles/
```

#### Migration échouée
```bash
# Vérifier l'état des migrations
docker-compose exec web python manage.py showmigrations

# Forcer une migration (urgence)
docker-compose exec web python manage.py migrate --fake
```

## 📈 Performance

### Optimisations recommandées
1. **Redis persistant** pour les queues Celery
2. **PostgreSQL tuning** dans postgresql.conf
3. **Nginx caching** pour les static files
4. **Docker limits** pour éviter l'overcommit

### Configuration recommandée
```yaml
# docker-compose.override.yml
services:
  web:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
  
  celery:
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
```

## 🔄 Mises à jour

### Procédure de mise à jour
```bash
# Backup avant mise à jour
docker-compose exec db pg_dump -U postgres nocode_platform > backup.sql

# Pull nouvelles versions
git pull origin main

# Rebuild et restart
docker-compose up -d --build

# Migrations
docker-compose exec web python manage.py migrate

# Vérification
docker-compose exec web python manage.py check --deploy
```

## 📞 Support

### En cas de problème
1. **Vérifier les logs** avec `docker-compose logs`
2. **Redémarrer les services** affectés
3. **Consulter la documentation** Django/Celery
4. **Contacter le support** avec les logs d'erreurs

### Logs à conserver
- `/var/log/nginx/error.log`
- Django logs (configurés dans settings)
- Celery worker logs
- PostgreSQL logs

---

## ✅ Checklist déploiement

- [ ] Configuration `.env` complétée
- [ ] Certificats SSL installés
- [ ] DNS configuré
- [ ] Firewall activé
- [ ] Database créée
- [ ] Migrations appliquées
- [ ] Super utilisateur créé
- [ ] Static files collectées
- [ ] Celery worker actif
- [ ] Celery beat actif
- [ ] Health checks OK
- [ ] Monitoring configuré
- [ ] Backup planifié

🚀 **Plateforme prête pour la production!**
