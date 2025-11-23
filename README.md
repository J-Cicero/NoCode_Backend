# 🚀 Plateforme NoCode

Une plateforme complète de développement NoCode construite avec Django REST Framework, permettant de créer des applications web complètes sans code.

## 📋 Table des Matières

- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [API Documentation](#api-documentation)
- [Développement](#développement)
- [Déploiement](#déploiement)
- [Tests](#tests)
- [Contribuer](#contribuer)
- [Licence](#licence)

## ✨ Fonctionnalités

### 🏗️ Module Foundation
- **Authentification JWT** avec inscription, connexion, réinitialisation de mot de passe
- **Gestion des utilisateurs** avec profils et permissions avancées
- **Organisations multi-tenant** avec membres et invitations
- **Système de facturation Stripe** intégré
- **Vérification de documents** (KYC/KYB)
- **Audit et logging** complets des actions utilisateur

### 🎨 Module Studio
- **Éditeur NoCode visuel** avec interface drag & drop
- **Gestion de projets** avec schémas PostgreSQL dynamiques
- **Composants configurables** avec métadonnées JSON
- **Pages dynamiques** avec configuration flexible
- **Export/Import** de projets complets
- **Gestion de schémas** de données personnalisables

### ⚡ Module Automation
- **Workflows automatisés** avec étapes conditionnelles
- **Intégrations API** externes (webhooks, REST APIs)
- **Planification** de tâches avec cron
- **Exécution asynchrone** via Celery
- **Gestion d'erreurs** et retry automatique

### 🚀 Module Runtime
- **Génération automatique** d'APIs Django
- **Applications complètes** générées dynamiquement
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   UTILISATEUR   │───▶│     STUDIO      │───▶│     RUNTIME     │
│                 │    │  (Drag & Drop)  │    │ (Apps générées) │
│ - Crée projets  │    │ - Pages JSON    │    │ - Fichiers      │
│ - Drag & Drop   │    │ - Composants    │    │ - Déploiements  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FOUNDATION    │    │   AUTOMATION    │    │    INSIGHTS     │
│                 │    │                 │    │                 │
│ - Authentif.    │    │ - Workflows     │    │ - Analytics     │
│ - Organisations │    │ - Triggers      │    │ - Métriques     │
│ - Utilisateurs  │    │ - Exécutions    │    │ - Logs          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔄 Flux de Données Automatique

### Ce que l'utilisateur fait :
1. **S'inscrit/Connecte** via Foundation
2. **Crée une organisation** via Foundation  
3. **Crée des projets** via Studio
4. **Fait du drag & drop** pour créer des pages via Studio

### Ce que le système fait automatiquement :
1. **Crée des workflows** quand un projet est créé (Automation)
2. **Déclenche des triggers** lors des modifications (Automation)
3. **Génère des applications JSON** (Runtime)
4. **Sauvegarde automatiquement** les changements (Runtime)
5. **Collecte les analytics** de toutes les actions (Insights)
6. **Monitor les performances** en temps réel (Insights)

## 🛠️ Stack Technologique

### Backend Core
- **Django 5.0.6** - Framework web principal
- **Django REST Framework** - API REST
- **PostgreSQL 15** - Base de données principale avec support JSON natif
- **Python 3.12.3** - Langage de programmation

### Communication & APIs
- **drf-spectacular** - Documentation OpenAPI/Swagger automatique
- **Django Channels** - WebSockets pour la collaboration temps réel
- **Redis** - Cache et broker de messages

### Traitement en Arrière-plan
- **Celery** - Tâches asynchrones et workflows
- **Flower** - Monitoring des tâches Celery
- **Django Signals** - Déclencheurs automatiques inter-modules

### Déploiement & Monitoring
- **Docker & Docker Compose** - Conteneurisation
- **Nginx** - Reverse proxy et serveur de fichiers statiques
- **Gunicorn** - Serveur WSGI pour Django

## 🚀 Démarrage Rapide

### Prérequis
```bash
# Python 3.12+ et PostgreSQL requis
sudo apt update
sudo apt install python3.12 python3.12-venv postgresql postgresql-contrib redis-server
```

### Installation
```bash
# Cloner le projet
git clone <repository-url>
cd NoCode_Backend

# Environnement virtuel
python3.12 -m venv .venv
source .venv/bin/activate

# Dépendances
pip install -r requirements.txt

# Configuration base de données
cp .env.example .env
# Éditer .env avec vos credentials PostgreSQL

# Migrations
python manage.py migrate

# Superutilisateur
python manage.py createsuperuser

# Démarrage
python manage.py runserver
```

### Accès
- **Swagger UI** : http://127.0.0.1:8000/api/docs/
- **Django Admin** : http://127.0.0.1:8000/admin/
- **API Foundation** : http://127.0.0.1:8000/api/foundation/
- **API Studio** : http://127.0.0.1:8000/api/studio/

## 📁 Structure du Projet

```
NoCode_Backend/
├── apps/
│   ├── foundation/          # Authentification & organisations
│   ├── studio/              # Drag & Drop & création d'applications
│   ├── automation/          # Workflows & triggers automatiques
│   ├── runtime/             # Génération & déploiement d'applications
│   └── insights/            # Analytics & monitoring
├── config/
│   ├── settings/            # Configuration Django (dev, prod, test)
│   ├── urls.py              # Routage principal
│   └── wsgi.py              # Interface WSGI
├── docker/                  # Configuration Docker
├── docs/                    # Documentation détaillée des modules
├── requirements/            # Dépendances par environnement
└── scripts/                 # Scripts utilitaires
```

## 🔧 Configuration des Services

### Redis (Cache & Broker)
```bash
# Installation
sudo apt install redis-server

# Configuration
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Test
redis-cli ping  # Doit répondre "PONG"
- `POST /api/v1/foundation/auth/login/` - Connexion
- `POST /api/v1/foundation/auth/logout/` - Déconnexion

#### Projets (Studio)
- `GET /api/v1/studio/projects/` - Liste des projets
- `POST /api/v1/studio/projects/` - Créer un projet
- `POST /api/v1/studio/projects/{id}/add_table/` - Ajouter une table

#### Workflows (Automation)
- `GET /api/v1/automation/workflows/` - Liste des workflows
- `POST /api/v1/automation/workflows/` - Créer un workflow
- `POST /api/v1/automation/workflows/{id}/execute/` - Exécuter un workflow

#### Applications (Runtime)
- `GET /api/v1/runtime/apps/` - Liste des applications
- `POST /api/v1/runtime/apps/` - Créer une application
- `POST /api/v1/runtime/apps/{id}/deploy/` - Déployer une application

## 📚 API Documentation

La documentation complète de l'API est disponible via Swagger UI :

- **URL**: http://localhost:8000/api/docs/
- **Format**: OpenAPI 3.0
- **Authentification**: JWT Bearer tokens

### Exemple d'utilisation de l'API

```python
import requests

# 1. Inscription
response = requests.post('http://localhost:8000/api/v1/foundation/auth/register/client/', json={
    'email': 'user@example.com',
    'password': 'securepassword',
    'first_name': 'John',
    'last_name': 'Doe'
})
user_data = response.json()

# 2. Connexion
response = requests.post('http://localhost:8000/api/v1/foundation/auth/login/', json={
    'email': 'user@example.com',
    'password': 'securepassword'
})
tokens = response.json()

# 3. Utilisation du token
headers = {'Authorization': f'Bearer {tokens["access"]}'}

# 4. Créer une organisation
response = requests.post('http://localhost:8000/api/v1/foundation/organizations/',
                        headers=headers, json={
    'name': 'Mon Entreprise',
    'description': 'Description de l\'entreprise'
})
org_data = response.json()
```

## 🔧 Développement

### Structure du Projet

```
NoCode/
├── apps/                    # Applications Django
│   ├── foundation/         # Module base (auth, org, billing)
│   ├── studio/            # Module éditeur NoCode
│   ├── automation/        # Module workflows
│   ├── runtime/           # Module génération d'apps
│   └── insights/          # Module analytics
├── config/                # Configuration Django
│   ├── settings/          # Paramètres par environnement
│   ├── urls.py           # URLs principales
│   └── wsgi.py           # Configuration WSGI
├── requirements.txt       # Dépendances Python
├── manage.py             # Script Django
└── launch.py             # Script de lancement rapide
```

### Utilitaires de Développement

```bash
# Script de lancement rapide
python3 launch.py setup    # Configuration complète
python3 launch.py check    # Vérification santé
python3 launch.py clean    # Nettoyage du projet

# Vérification de santé
python3 apps/foundation/utils/health_check.py

# Nettoyage du projet
python3 apps/foundation/utils/cleaner.py
```

## 🧪 Tests

### Exécution des Tests

```bash
# Tests unitaires
python manage.py test apps.foundation.tests.test_models

# Tests d'intégration
python manage.py test apps.studio.tests.test_views

# Tests avec options
python manage.py test --verbosity=2 --parallel 1

# Tests avec coverage
coverage run manage.py test
coverage html
```

## 🚀 Déploiement

### Variables d'environnement de production

```env
# Production .env
DEBUG=False
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://user:pass@db:5432/nocode_prod
REDIS_URL=redis://redis:6379/0
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
LOG_LEVEL=WARNING
```

## 📄 Licence

Ce projet est sous licence MIT.

## 🆘 Support

### Ressources

- **Documentation**: http://localhost:8000/api/docs/
- **Guide d'apprentissage**: [LEARNING_GUIDE.md](LEARNING_GUIDE.md)

### Problèmes Courants

#### Erreur de migration
```bash
# Réinitialiser les migrations
python manage.py migrate --fake-initial
python manage.py makemigrations
python manage.py migrate
```

#### Erreur Celery
```bash
# Vérifier Redis
redis-cli ping

# Redémarrer les workers
pkill -f celery
python manage.py celery worker -l info
```

## 🎯 Roadmap

### Version 1.0 (Actuelle)
- ✅ Architecture modulaire complète
- ✅ 5 modules principaux fonctionnels
- ✅ API REST complète
- ✅ Authentification JWT
- ✅ Multi-tenancy

### Version 1.1 (Prochaine)
- 🚧 Interface frontend React/Vue
- 🚧 Éditeur visuel drag & drop
- 🚧 Générateur d'APIs avancé
- 🚧 Webhooks personnalisés
- 🚧 Tests d'intégration complets

---

**Développé avec ❤️ par l'équipe NoCode**

Pour plus d'informations, consultez la [documentation complète](http://localhost:8000/api/docs/) et le [guide d'apprentissage](LEARNING_GUIDE.md).