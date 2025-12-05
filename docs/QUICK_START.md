# 🚀 Quick Start Guide - NoCode Backend

## 🎯 Vue d'ensemble

Ce guide vous montre comment **déployer et utiliser** la plateforme NoCode Backend de bout en bout : de l'installation à la création d'une application complète avec CRUD dynamique.

**Temps estimé :** 15-20 minutes

---

## 📋 Prérequis

- **Docker** et **Docker Compose** installés
- **Git** pour cloner le dépôt
- **4GB+ RAM** disponible
- **Ports 8000, 5432, 6379** libres

---

## 🐳 Étape 1: Déploiement de la Plateforme

### 1.1 Cloner le Code Source
```bash
git clone https://github.com/your-org/NoCode_Backend.git
cd NoCode_Backend
```

### 1.2 Configurer les Variables d'Environnement
```bash
# Copier le template
cp .env.example .env

# Éditer .env avec vos valeurs
nano .env
```

**Variables essentielles :**
```bash
# Base de données
POSTGRES_DB=nocode_backend
POSTGRES_USER=nocode_user
POSTGRES_PASSWORD=your_secure_password

# Redis
REDIS_PASSWORD=your_redis_password

# Application
SECRET_KEY=your_very_long_secret_key_here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Superutilisateur
CREATE_SUPERUSER=True
SUPERUSER_EMAIL=admin@yourcompany.com
SUPERUSER_PASSWORD=admin_password
```

### 1.3 Démarrer les Services
```bash
# Production (recommandé)
docker-compose -f docker-compose.prod.yml up -d

# Ou développement
docker-compose -f docker-compose.dev.yml up -d
```

### 1.4 Vérifier le Déploiement
```bash
# Vérifier que tous les services sont actifs
docker-compose -f docker-compose.prod.yml ps

# Attendre 1-2 minutes pour l'initialisation
# Vérifier la santé de l'API
curl http://localhost:8000/api/v1/foundation/health/
```

**Réponse attendue :**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "redis": "connected",
    "celery": "running"
  }
}
```

---

## 🔐 Étape 2: Première Connexion et Authentification

### 2.1 Créer un Compte Utilisateur
```bash
curl -X POST http://localhost:8000/api/v1/foundation/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@yourcompany.com",
    "password": "UserPassword123!",
    "password_confirm": "UserPassword123!",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

**Réponse :**
```json
{
  "message": "Utilisateur créé avec succès",
  "user": {
    "id": 1,
    "email": "user@yourcompany.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

### 2.2 Se Connecter (Obtenir Tokens JWT)
```bash
curl -X POST http://localhost:8000/api/v1/foundation/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@yourcompany.com",
    "password": "UserPassword123!"
  }'
```

**Réponse :**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "user@yourcompany.com",
    "full_name": "John Doe"
  },
  "organizations": [],
  "permissions": {
    "can_create_projects": true,
    "can_create_organizations": true
  }
}
```

**Conservez le token `access` pour les prochaines étapes !**

---

## 🏗️ Étape 3: Créer un Projet NoCode

### 3.1 Créer le Projet
```bash
# Remplacer YOUR_ACCESS_TOKEN par le token obtenu
ACCESS_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

curl -X POST http://localhost:8000/api/v1/studio/projects/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gestion Client CRM"
  }'
```

**Réponse :**
```json
{
  "tracking_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Gestion Client CRM",
  "schema_name": "project_1",
  "status": "draft",
  "created_at": "2024-01-20T10:00:00Z"
}
```

**Conservez le `tracking_id` du projet !**

---

## 📊 Étape 4: Définir le Schéma de Données

### 4.1 Créer une Table "Clients"
```bash
PROJECT_ID="550e8400-e29b-41d4-a716-446655440000"

curl -X POST http://localhost:8000/api/v1/studio/schemas/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project": "'$PROJECT_ID'",
    "table_name": "clients",
    "display_name": "Clients",
    "fields_config": [
      {
        "name": "nom",
        "type": "string",
        "label": "Nom complet",
        "required": true,
        "max_length": 100
      },
      {
        "name": "email",
        "type": "string",
        "label": "Email professionnel",
        "required": true,
        "unique": true
      },
      {
        "name": "telephone",
        "type": "string",
        "label": "Téléphone",
        "required": false
      },
      {
        "name": "entreprise",
        "type": "string",
        "label": "Entreprise",
        "required": false
      },
      {
        "name": "notes",
        "type": "text",
        "label": "Notes",
        "required": false
      }
    ]
  }'
```

**Réponse :**
```json
{
  "id": 1,
  "table_name": "clients",
  "display_name": "Clients",
  "sql_table_created": true,
  "table_name_full": "project_1_clients",
  "created_at": "2024-01-20T11:00:00Z"
}
```

### 4.2 Créer une Table "Produits"
```bash
curl -X POST http://localhost:8000/api/v1/studio/schemas/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project": "'$PROJECT_ID'",
    "table_name": "produits",
    "display_name": "Produits",
    "fields_config": [
      {
        "name": "reference",
        "type": "string",
        "label": "Référence",
        "required": true,
        "unique": true
      },
      {
        "name": "nom",
        "type": "string",
        "label": "Nom du produit",
        "required": true
      },
      {
        "name": "description",
        "type": "text",
        "label": "Description",
        "required": false
      },
      {
        "name": "prix",
        "type": "float",
        "label": "Prix",
        "required": true
      },
      {
        "name": "stock",
        "type": "integer",
        "label": "Stock",
        "required": true
      }
    ]
  }'
```

---

## 🚀 Étape 5: Publier et Déployer l'Application

### 5.1 Publier le Projet
```bash
curl -X POST http://localhost:8000/api/v1/studio/projects/$PROJECT_ID/publish/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Réponse :**
```json
{
  "message": "Génération de l'application démarrée",
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "generation_task_id": "task-uuid-here",
  "estimated_time": "2-3 minutes",
  "status": "generating"
}
```

### 5.2 Vérifier le Statut de Génération
```bash
# Attendre 2-3 minutes puis vérifier
curl -X GET http://localhost:8000/api/v1/studio/projects/$PROJECT_ID/deployment_status/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Réponse attendue :**
```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "published",
  "deployment": {
    "status": "deployed",
    "url": "http://localhost:8000/runtime/project_1/",
    "api_url": "http://localhost:8000/api/v1/runtime/projects/550e8400-e29b-41d4-a716-446655440000/",
    "deployed_at": "2024-01-20T12:00:00Z"
  }
}
```

---

## 📝 Étape 6: Utiliser l'Application (CRUD Dynamique)

### 6.1 Explorer le Schéma de l'Application
```bash
curl -X GET http://localhost:8000/api/v1/runtime/projects/$PROJECT_ID/schema/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 6.2 Créer un Client
```bash
curl -X POST http://localhost:8000/api/v1/runtime/projects/$PROJECT_ID/tables/clients/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Marie Dupont",
    "email": "marie.dupont@entreprise.com",
    "telephone": "+33612345678",
    "entreprise": "Tech Corp",
    "notes": "Client VIP, intérêt pour solution premium"
  }'
```

**Réponse :**
```json
{
  "id": 1,
  "nom": "Marie Dupont",
  "email": "marie.dupont@entreprise.com",
  "telephone": "+33612345678",
  "entreprise": "Tech Corp",
  "notes": "Client VIP, intérêt pour solution premium",
  "created_at": "2024-01-20T13:00:00Z"
}
```

### 6.3 Créer un Produit
```bash
curl -X POST http://localhost:8000/api/v1/runtime/projects/$PROJECT_ID/tables/produits/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reference": "PROD-001",
    "nom": "Licence NoCode Pro",
    "description": "Licence annuelle pour plateforme NoCode",
    "prix": 999.99,
    "stock": 100
  }'
```

### 6.4 Lister tous les Clients
```bash
curl -X GET http://localhost:8000/api/v1/runtime/projects/$PROJECT_ID/tables/clients/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 6.5 Mettre à jour un Client
```bash
curl -X PUT http://localhost:8000/api/v1/runtime/projects/$PROJECT_ID/tables/clients/1/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "Client VIP - Contrat signé le 20/01/2024",
    "telephone": "+33612345679"
  }'
```

---

## 📊 Étape 7: Analytics et Monitoring

### 7.1 Tracker une Activité
```bash
curl -X POST http://localhost:8000/api/v1/insights/track/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "user_action",
    "event_name": "client_created",
    "properties": {
      "project_id": "'$PROJECT_ID'",
      "client_id": 1,
      "source": "quick_start_guide"
    }
  }'
```

### 7.2 Voir les Analytics
```bash
curl -X GET "http://localhost:8000/api/v1/insights/analytics/?project_id=$PROJECT_ID&period=24h" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

---

## 🎉 Félicitations !

Votre application NoCode est maintenant **complètement fonctionnelle** avec :

✅ **Infrastructure Docker** déployée (5 services)  
✅ **Authentification JWT** sécurisée  
✅ **Projet CRM** créé et publié  
✅ **Tables dynamiques** (clients, produits)  
✅ **API CRUD** opérationnelle  
✅ **Analytics** activés  

---

## 🔗 URLs Importantes

| Service | URL | Description |
|---------|-----|-------------|
| **API REST** | `http://localhost:8000/api/v1/` | API principale |
| **Admin Django** | `http://localhost:8000/admin/` | Interface admin |
| **Application CRM** | `http://localhost:8000/runtime/project_1/` | Votre application |
| **Documentation API** | `http://localhost:8000/api/docs/` | Swagger UI |

---

## 🛠️ Prochaines Étapes

### 1. Créer une Interface Frontend
```javascript
// Exemple React
const API_BASE = 'http://localhost:8000/api/v1';

// Lister les clients
const clients = await fetch(`${API_BASE}/runtime/projects/${PROJECT_ID}/tables/clients/`, {
  headers: { 'Authorization': `Bearer ${ACCESS_TOKEN}` }
});
```

### 2. Ajouter des Workflows d'Automatisation
```bash
# Créer un workflow d'envoi d'email
curl -X POST http://localhost:8000/api/v1/automation/workflows/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Email Bienvenue Client",
    "project": "'$PROJECT_ID'",
    "trigger_type": "webhook"
  }'
```

### 3. Explorer les Analytics Avancés
```bash
# Exporter les données d'utilisation
curl -X POST http://localhost:8000/api/v1/insights/export/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "export_type": "user_activity",
    "format": "csv",
    "filters": {
      "project_id": "'$PROJECT_ID'",
      "date_from": "2024-01-20"
    }
  }'
```

---

## 🚨 Dépannage Commun

### Problème: "Connection refused" sur port 8000
```bash
# Vérifier si le service web est actif
docker-compose -f docker-compose.prod.yml ps web

# Redémarrer le service web
docker-compose -f docker-compose.prod.yml restart web

# Vérifier les logs
docker-compose -f docker-compose.prod.yml logs web
```

### Problème: "Database connection failed"
```bash
# Attendre l'initialisation complète de PostgreSQL
docker-compose -f docker-compose.prod.yml logs db

# Redémarrer tous les services
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### Problème: Token JWT expiré
```bash
# Rafraîchir le token
curl -X POST http://localhost:8000/api/v1/foundation/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

### Problème: Permission refusée
```bash
# Vérifier que vous utilisez le bon token
curl -X GET http://localhost:8000/api/v1/foundation/auth/profile/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Se reconnecter si nécessaire
curl -X POST http://localhost:8000/api/v1/foundation/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@yourcompany.com", "password": "UserPassword123!"}'
```

---

## 📚 Ressources Additionnelles

- **Documentation complète** : `/docs/API_OVERVIEW.md`
- **Référence API** : `/docs/FOUNDATION_API.md`
- **Guide Docker** : `/docs/DOCKER_DEPLOYMENT.md`
- **Support** : Créer une issue sur GitHub

---

**🎯 Vous êtes prêt à construire des applications NoCode complexes !**

Pour toute question ou problème, consultez la documentation complète ou contactez le support technique.
