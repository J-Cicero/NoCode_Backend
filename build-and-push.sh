#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════╗"
echo "║  🐳 Build & Push Docker Hub Images     ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"

# Configuration
DOCKER_IMAGE=${1:-jude789/nocode-backend}
TAG=${2:-latest}

echo -e "${YELLOW}📋 Configuration:${NC}"
echo "  Image: $DOCKER_IMAGE"
echo "  Tag: $TAG"
echo ""

# Vérifier Docker Hub login
if ! docker info | grep -q "Username"; then
    echo -e "${YELLOW}🔐 Connexion à Docker Hub requise...${NC}"
    echo "Exécutez: docker login"
    read -p "Appuyez sur Entrée une fois connecté..."
fi

# Build images
echo -e "${YELLOW}🏗️  Build de l'image web...${NC}"
docker build -t ${DOCKER_IMAGE}:${TAG} .

echo -e "${YELLOW}🏷️  Tagging des images...${NC}"
docker tag ${DOCKER_IMAGE}:${TAG} ${DOCKER_IMAGE}:celery
docker tag ${DOCKER_IMAGE}:${TAG} ${DOCKER_IMAGE}:celery-beat

# Push images
echo -e "${YELLOW}📤 Push vers Docker Hub...${NC}"
docker push ${DOCKER_IMAGE}:${TAG}
docker push ${DOCKER_IMAGE}:celery
docker push ${DOCKER_IMAGE}:celery-beat

echo ""
echo -e "${GREEN}✅ Images publiées sur Docker Hub!${NC}"
echo ""
echo "📋 Images disponibles:"
echo "  ${DOCKER_IMAGE}:${TAG}"
echo "  ${DOCKER_IMAGE}:celery"
echo "  ${DOCKER_IMAGE}:celery-beat"
echo ""
echo "🚀 Pour tester la distribution:"
echo "  1. Téléchargez docker-compose.hub.yml"
echo "  2. Copiez .env.example vers .env"
echo "  3. docker-compose -f docker-compose.hub.yml up -d"
