#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════╗"
echo "║  🐳 Configuration Docker NoCode        ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"

# ============================================
# Détection de Docker Compose
# ============================================
echo -e "${YELLOW}🔍 Vérification...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker non installé${NC}"
    exit 1
fi

# Détecter docker compose v2 OU docker-compose v1
COMPOSE_CMD=""
if docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
    echo -e "${GREEN}✅ Docker Compose v2 : $(docker compose version --short)${NC}"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
    echo -e "${GREEN}✅ Docker Compose v1 : $(docker-compose --version)${NC}"
else
    echo -e "${RED}❌ Docker Compose introuvable${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker : $(docker --version)${NC}"
echo ""

# ============================================
# Sauvegarde
# ============================================
echo -e "${YELLOW}📦 Sauvegarde...${NC}"
BACKUP_DIR=".backup_docker_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
[ -d "docker" ] && cp -r docker/ "$BACKUP_DIR/" 2>/dev/null && echo "  ↳ docker/ sauvegardé"
[ -f ".env" ] && cp .env "$BACKUP_DIR/" 2>/dev/null && echo "  ↳ .env sauvegardé"
echo -e "${GREEN}✅ Sauvegarde OK${NC}"
echo ""

# ============================================
# Nettoyage
# ============================================
echo -e "${YELLOW}🧹 Nettoyage...${NC}"
rm -f Dockerfile docker-compose*.yml .dockerignore .env.example
rm -rf docker/
echo -e "${GREEN}✅ Nettoyage terminé${NC}"
echo ""

# ============================================
# Création structure
# ============================================
echo -e "${YELLOW}📁 Création structure...${NC}"
mkdir -p docker/nginx/ssl
echo -e "${GREEN}✅ Structure créée${NC}"
echo ""

# ============================================
# Création fichiers
# ============================================
echo -e "${YELLOW}📝 Création fichiers...${NC}"

# .dockerignore
cat > .dockerignore << 'EOF'
__pycache__/
*.py[cod]
.venv/
venv/
*.log
db.sqlite3
.env
.git/
staticfiles/
EOF
echo "  ↳ .dockerignore"

# Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
EOF
echo "  ↳ Dockerfile"

# .env.example
cat > .env.example << 'EOF'
SECRET_KEY=change-me-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=nocode_platform
DB_USER=nocode_user
DB_PASSWORD=nocode_password
DB_HOST=db
DB_PORT=5432

REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
FRONTEND_URL=http://localhost:3000
SITE_NAME=NoCode Platform
EOF
echo "  ↳ .env.example"

# docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: nocode_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: ${DB_NAME:-nocode_platform}
      POSTGRES_USER: ${DB_USER:-nocode_user}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-nocode_password}
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U nocode_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: nocode_redis
    ports:
      - "6379:6379"

  web:
    build: .
    container_name: nocode_web
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy

  celery:
    build: .
    container_name: nocode_celery
    command: celery -A config worker -l info
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - db
      - redis

  celery-beat:
    build: .
    container_name: nocode_celery_beat
    command: celery -A config beat -l info
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
EOF
echo "  ↳ docker-compose.yml"

# nginx.conf
cat > docker/nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream django {
        server web:8000;
    }
    server {
        listen 80;
        location / {
            proxy_pass http://django;
            proxy_set_header Host $host;
        }
        location /static/ {
            alias /app/staticfiles/;
        }
    }
}
EOF
echo "  ↳ docker/nginx/nginx.conf"

echo -e "${GREEN}✅ Fichiers créés${NC}"
echo ""

# ============================================
# .env
# ============================================
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}✅ .env créé${NC}"
else
    echo -e "${YELLOW}⚠️  .env existe (conservé)${NC}"
fi

# ============================================
# requirements.txt
# ============================================
if ! grep -q "gunicorn" requirements.txt 2>/dev/null; then
    echo "gunicorn==21.2.0" >> requirements.txt
    echo -e "${GREEN}✅ gunicorn ajouté${NC}"
fi
echo ""

# ============================================
# Build
# ============================================
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🐳 DÉMARRAGE DOCKER                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

read -p "Lancer le build ? (o/N) : " start

if [[ $start =~ ^[Oo]$ ]]; then
    echo -e "${YELLOW}🏗️  Build...${NC}"
    $COMPOSE_CMD build
    
    echo -e "${YELLOW}🚀 Up...${NC}"
    $COMPOSE_CMD up -d
    
    sleep 10
    
    echo -e "${YELLOW}📊 Status :${NC}"
    $COMPOSE_CMD ps
    
    echo ""
    echo -e "${YELLOW}🔧 Migrations...${NC}"
    $COMPOSE_CMD exec web python manage.py migrate
    
    echo -e "${YELLOW}📦 Collectstatic...${NC}"
    $COMPOSE_CMD exec web python manage.py collectstatic --noinput
    
    echo ""
    echo -e "${GREEN}🎉 Terminé !${NC}"
    echo ""
    echo "🌐 http://localhost:8000"
    echo "🔧 http://localhost:8000/admin"
    echo ""
    echo "Commandes :"
    echo "  Logs    : $COMPOSE_CMD logs -f"
    echo "  Arrêter : $COMPOSE_CMD down"
    echo "  Admin   : $COMPOSE_CMD exec web python manage.py createsuperuser"
else
    echo -e "${GREEN}✅ Prêt !${NC}"
    echo "Pour démarrer : $COMPOSE_CMD up -d --build"
fi

echo ""
echo -e "${GREEN}✨ Fini !${NC}"
