# 🐳 Dockerisation & Déploiement de la Plateforme NoCode

## 🎯 Vue d'ensemble

Ce guide explique comment dockeriser la plateforme NoCode Backend avec tous ses services (Django, PostgreSQL, Redis, Celery, Nginx) pour un déploiement en production robuste et scalable.

---

## 🏗️ Architecture Docker

### Services Conteneurisés
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     nginx       │    │     django      │    │   postgresql    │
│   (Reverse      │    │   (Application  │    │   (Base de      │
│    Proxy)       │    │     Web)        │    │   Données)      │
│   Port: 80/443  │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     redis       │    │     celery      │    │     flower      │
│   (Cache &      │    │   (Tâches       │    │   (Monitoring   │
│   Broker)       │    │   Asynchrones)  │    │   Celery)       │
│   Port: 6379    │    │   Worker: N/A   │    │   Port: 5555    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 📁 Structure des Fichiers Docker

```
NoCode_Backend/
├── docker/
│   ├── Dockerfile                 # Image principale Django
│   ├── Dockerfile.prod            # Image production optimisée
│   ├── nginx/
│   │   ├── Dockerfile             # Image Nginx
│   │   ├── nginx.conf             # Configuration Nginx
│   │   └── ssl/                   # Certificats SSL
│   ├── postgresql/
│   │   ├── Dockerfile             # Image PostgreSQL personnalisée
│   │   └── init.sql               # Scripts d'initialisation
│   └── docker-compose.yml         # Développement
│   ├── docker-compose.prod.yml    # Production
│   └── docker-compose.override.yml # Overrides locaux
├── .dockerignore                  # Fichiers ignorés
└── docker-entrypoint.sh           # Script d'entrée
```

---

## 🐳 Dockerfile Principal

### Dockerfile (Développement)
```dockerfile
# Étape 1: Build
FROM python:3.12-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/production.txt

# Étape 2: Runtime
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application
COPY . .

# Create non-root user
RUN groupadd -r django && useradd -r -g django django
RUN chown -R django:django /app
USER django

# Collect static files
RUN python manage.py collectstatic --noinput --clear

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

EXPOSE 8000

# Use entrypoint script
COPY docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
```

### Dockerfile.prod (Production optimisée)
```dockerfile
# Multi-stage build pour production optimisée
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/production.txt

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    gettext \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Security: non-root user
RUN groupadd -r django && useradd -r -g django django
RUN chown -R django:django /app
USER django

# Production optimizations
RUN python manage.py collectstatic --noinput --clear
RUN python manage.py compress --force

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "config.wsgi:application"]
```

---

## 🔧 Configuration Docker Compose

### docker-compose.yml (Développement)
```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: nocode
      POSTGRES_USER: nocode_user
      POSTGRES_PASSWORD: cicero
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgresql/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U nocode_user -d nocode"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  web:
    build:
      context: .
      dockerfile: docker/Dockerfile
    environment:
      - DEBUG=True
      - DATABASE_URL=postgresql://nocode_user:cicero@db:5432/nocode
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: python manage.py runserver 0.0.0.0:8000

  celery:
    build:
      context: .
      dockerfile: docker/Dockerfile
    environment:
      - DEBUG=True
      - DATABASE_URL=postgresql://nocode_user:cicero@db:5432/nocode
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    volumes:
      - .:/app
    depends_on:
      - db
      - redis
    command: celery -A NoCode_Backend worker -l info

  celery-beat:
    build:
      context: .
      dockerfile: docker/Dockerfile
    environment:
      - DEBUG=True
      - DATABASE_URL=postgresql://nocode_user:cicero@db:5432/nocode
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    volumes:
      - .:/app
    depends_on:
      - db
      - redis
    command: celery -A NoCode_Backend beat -l info

  flower:
    build:
      context: .
      dockerfile: docker/Dockerfile
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    ports:
      - "5555:5555"
    depends_on:
      - redis
    command: celery -A NoCode_Backend flower --port=5555

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
```

### docker-compose.prod.yml (Production)
```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: nocode
      POSTGRES_USER: nocode_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U nocode_user -d nocode"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  web:
    build:
      context: .
      dockerfile: docker/Dockerfile.prod
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=postgresql://nocode_user:${POSTGRES_PASSWORD}@db:5432/nocode
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - generated_apps:/app/generated_apps
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery:
    build:
      context: .
      dockerfile: docker/Dockerfile.prod
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=postgresql://nocode_user:${POSTGRES_PASSWORD}@db:5432/nocode
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    volumes:
      - generated_apps:/app/generated_apps
    restart: unless-stopped
    depends_on:
      - db
      - redis
    command: celery -A NoCode_Backend worker -l info --concurrency=4

  celery-beat:
    build:
      context: .
      dockerfile: docker/Dockerfile.prod
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=postgresql://nocode_user:${POSTGRES_PASSWORD}@db:5432/nocode
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    restart: unless-stopped
    depends_on:
      - db
      - redis
    command: celery -A NoCode_Backend beat -l info

  nginx:
    build:
      context: ./docker/nginx
      dockerfile: Dockerfile
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - static_volume:/static
      - media_volume:/media
      - generated_apps:/apps
      - ./docker/nginx/ssl:/etc/nginx/ssl
    restart: unless-stopped
    depends_on:
      - web

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
  generated_apps:
```

---

## 🌐 Configuration Nginx

### docker/nginx/Dockerfile
```dockerfile
FROM nginx:alpine

# Copy configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/

# Copy SSL certificates (if any)
COPY ssl/ /etc/nginx/ssl/

# Create directories for logs
RUN mkdir -p /var/log/nginx

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
```

### docker/nginx/nginx.conf
```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging format
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;

    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Include site configurations
    include /etc/nginx/conf.d/*.conf;
}
```

### docker/nginx/conf.d/nocode.conf
```nginx
# Upstream Django application
upstream django {
    server web:8000;
    keepalive 32;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name nocode.com www.nocode.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name nocode.com www.nocode.com;

    # SSL configuration
    ssl_certificate /etc/nginx/ssl/nocode.com.crt;
    ssl_certificate_key /etc/nginx/ssl/nocode.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Static files
    location /static/ {
        alias /static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Media files
    location /media/ {
        alias /media/;
        expires 30d;
        add_header Cache-Control "public";
        access_log off;
    }

    # Generated applications
    location /apps/ {
        alias /apps/;
        expires 1h;
        add_header Cache-Control "public";
        
        # Security: prevent direct access to sensitive files
        location ~* \.(py|pyc|cfg|env|log)$ {
            deny all;
        }
    }

    # API endpoints with rate limiting
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Authentication endpoints with stricter rate limiting
    location /api/foundation/auth/ {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Django admin
    location /admin/ {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Additional security for admin
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny all;
    }

    # Swagger documentation
    location /api/docs/ {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # Default location
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 🔧 Scripts de Déploiement

### docker-entrypoint.sh
```bash
#!/bin/bash
set -e

# Wait for database
echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL is ready!"

# Wait for Redis
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 0.1
done
echo "Redis is ready!"

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if needed
if [ "$DJANGO_SUPERUSER_EMAIL" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser..."
    python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='$DJANGO_SUPERUSER_EMAIL').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
    print('Superuser created')
else:
    print('Superuser already exists')
EOF
fi

# Execute the command
exec "$@"
```

### scripts/deploy.sh
```bash
#!/bin/bash

# Deployment script for NoCode Backend
set -e

echo "🚀 Starting NoCode Backend deployment..."

# Load environment variables
if [ -f .env.prod ]; then
    export $(cat .env.prod | xargs)
else
    echo "❌ .env.prod file not found!"
    exit 1
fi

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Build and start services
echo "🔨 Building Docker images..."
docker-compose -f docker-compose.prod.yml build --no-cache

echo "🔄 Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Run health checks
echo "🏥 Running health checks..."
python scripts/health_check.py

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
echo "📁 Collecting static files..."
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

echo "✅ Deployment completed successfully!"
echo "🌐 Application is available at: https://nocode.com"
echo "📊 Flower monitoring: https://nocode.com:5555"
```

### scripts/backup.sh
```bash
#!/bin/bash

# Backup script for database and files
set -e

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

echo "🗄️ Starting backup process..."

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup PostgreSQL database
echo "💾 Backing up PostgreSQL database..."
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U nocode_user nocode | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Backup generated apps
echo "📦 Backing up generated applications..."
tar -czf $BACKUP_DIR/generated_apps_$DATE.tar.gz generated_apps/

# Backup media files
echo "🖼️ Backing up media files..."
tar -czf $BACKUP_DIR/media_$DATE.tar.gz media/

# Clean old backups (keep last 7 days)
echo "🧹 Cleaning old backups..."
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "✅ Backup completed successfully!"
echo "📍 Backup location: $BACKUP_DIR"
```

---

## 🚀 Commands de Déploiement

### Développement
```bash
# Démarrer l'environnement de développement
docker-compose up -d

# Voir les logs
docker-compose logs -f web

# Reconstruire après modifications
docker-compose build
docker-compose up -d

# Arrêter tout
docker-compose down

# Nettoyer les volumes
docker-compose down -v
```

### Production
```bash
# Déployer en production
./scripts/deploy.sh

# Vérifier l'état des services
docker-compose -f docker-compose.prod.yml ps

# Voir les logs de production
docker-compose -f docker-compose.prod.yml logs -f

# Mise à jour de l'application
git pull origin main
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Backup
./scripts/backup.sh
```

### Maintenance
```bash
# Nettoyer les images Docker inutilisées
docker system prune -f

# Nettoyer les volumes inutilisés
docker volume prune -f

# Surveiller l'utilisation des ressources
docker stats

# Accéder au conteneur pour debugging
docker-compose -f docker-compose.prod.yml exec web bash

# Redémarrer un service spécifique
docker-compose -f docker-compose.prod.yml restart celery
```

---

## 🔍 Monitoring et Logging

### Configuration des Logs
```yaml
# Dans docker-compose.prod.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Monitoring avec Flower
```bash
# Accéder à Flower
# URL: https://nocode.com:5555
# Username: admin
# Password: ${FLOWER_PASSWORD}

# Configuration dans docker-compose.prod.yml
flower:
  environment:
    - CELERY_BROKER_URL=redis://redis:6379/0
    - FLOWER_BASIC_AUTH=admin:${FLOWER_PASSWORD}
  command: celery -A NoCode_Backend flower --port=5555 --basic_auth=admin:${FLOWER_PASSWORD}
```

### Health Checks
```bash
# Script de health check
#!/bin/bash
# scripts/health_check.py

import requests
import sys
import time

def check_service(url, service_name):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"✅ {service_name} is healthy")
            return True
        else:
            print(f"❌ {service_name} returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {service_name} is unhealthy: {e}")
        return False

services = [
    ("http://localhost/health", "Nginx"),
    ("http://localhost/api/health/", "Django"),
    ("http://localhost:5555", "Flower"),
]

all_healthy = True
for url, name in services:
    if not check_service(url, name):
        all_healthy = False

if not all_healthy:
    sys.exit(1)
```

---

## 🔒 Sécurité Docker

### .dockerignore
```
# Git
.git
.gitignore

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Database
*.db
*.sqlite3

# Media (will be mounted as volume)
media/
generated_apps/

# Docker
Dockerfile*
docker-compose*
.dockerignore
```

### Security Hardening
```dockerfile
# Dans Dockerfile.prod
# Utiliser un utilisateur non-root
RUN groupadd -r django && useradd -r -g django django
USER django

# Limiter les permissions
RUN chmod 755 /app
RUN chmod -R 644 /app/staticfiles/
RUN chmod -R 755 /app/media/

# Installer les mises à jour de sécurité
RUN apt-get update && apt-get upgrade -y && apt-get clean
```

---

## 📈 Performance et Scaling

### Configuration Production Optimisée
```yaml
# docker-compose.prod.yml optimisé
web:
  deploy:
    replicas: 3
    resources:
      limits:
        cpus: '1.0'
        memory: 1G
      reservations:
        cpus: '0.5'
        memory: 512M
  restart_policy:
    condition: on-failure
    delay: 5s
    max_attempts: 3

celery:
  deploy:
    replicas: 2
    resources:
      limits:
        cpus: '0.5'
        memory: 512M
```

### Load Balancing
```nginx
# Configuration upstream avec load balancing
upstream django {
    least_conn;
    server web:8000 max_fails=3 fail_timeout=30s;
    server web2:8000 max_fails=3 fail_timeout=30s;
    server web3:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}
```

---

## 🔧 Dépannage Docker

### Problèmes Courants
```bash
# Conteneur ne démarre pas
docker-compose logs web
docker inspect nocode_backend_web_1

# Problèmes de connexion base de données
docker-compose exec web python manage.py dbshell
docker-compose exec db psql -U nocode_user -d nocode

# Problèmes Redis
docker-compose exec redis redis-cli ping
docker-compose exec redis redis-cli info

# Problèmes Celery
docker-compose exec celery celery -A NoCode_Backend inspect active
docker-compose logs celery

# Nettoyer tout et recommencer
docker-compose down -v
docker system prune -f
docker-compose build --no-cache
docker-compose up -d
```

### Commands Utiles
```bash
# Taille des images
docker images --format "table {{.Repository}}\t{{.Size}}"

# Taille des volumes
docker system df

# Entrer dans un conteneur
docker-compose exec web bash

# Copier des fichiers
docker cp ./local_file.txt nocode_backend_web_1:/app/

# Surveillance en temps réel
docker stats --no-stream
docker-compose top
```

---

## 📋 Checklist de Déploiement

### Pré-déploiement
- [ ] Variables d'environnement configurées
- [ ] Certificats SSL en place
- [ ] Base de données backupée
- [ ] Tests passés avec succès
- [ ] Images Docker construites

### Post-déploiement
- [ ] Health checks passent
- [ ] Logs sans erreurs
- [ ] Performance acceptable
- [ ] SSL configuré correctement
- [ ] Monitoring actif
- [ ] Backup automatique configuré

### Monitoring Continu
- [ ] Utilisation CPU/Mémoire < 80%
- [ ] Espace disque disponible > 20%
- [ ] Temps de réponse < 2s
- [ ] Taux d'erreur < 1%
- [ ] Certificats SSL valides

---

**Cette configuration Docker assure un déploiement production-ready, sécurisé et scalable de la plateforme NoCode Backend avec tous ses services intégrés.**
