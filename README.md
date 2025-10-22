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
- **Déploiement automatique** des applications
- **Gestion de bases de données** PostgreSQL
- **Monitoring** des applications déployées

### 📊 Module Insights
- **Analytics utilisateurs** et métriques d'usage
- **Monitoring système** (CPU, mémoire, performance)
- **Rapports automatiques** et tableaux de bord
- **Tracking d'activités** en temps réel
- **Audit complet** de toutes les actions

## 🏛️ Architecture

La plateforme suit une architecture modulaire avec 5 modules principaux :

```
📦 NoCode Platform
├── 🎯 Foundation (Base technique)
│   ├── 👤 Authentification & Utilisateurs
│   ├── 🏢 Organisations & Multi-tenancy
│   ├── 💳 Facturation & Abonnements
│   └── ✅ Vérification & Conformité
├── 🎨 Studio (Éditeur NoCode)
│   ├── 📁 Gestion de projets
│   ├── 🧩 Composants & Métadonnées
│   ├── 📄 Pages & Interface
│   └── 🗄️ Schémas de données
├── ⚡ Automation (Logique métier)
│   ├── 🔄 Workflows & Étapes
│   ├── 🔗 Intégrations externes
│   ├── ⏰ Planification
│   └── 📊 Exécution & Monitoring
├── 🚀 Runtime (Génération d'apps)
│   ├── ⚙️ Génération automatique
│   ├── 🚀 Déploiement
│   ├── 🗄️ Bases de données dynamiques
│   └── 📈 Monitoring d'applications
└── 📊 Insights (Analytics)
    ├── 📈 Métriques & Analytics
    ├── 👁️ Monitoring & Alertes
    ├── 📋 Audit & Traçabilité
    └── 📊 Rapports & Dashboards
```

## 🛠️ Installation

### Prérequis

- **Python** 3.8 ou supérieur
- **PostgreSQL** 12 ou supérieur
- **Redis** 6 ou supérieur (pour Celery)
- **Node.js** 16+ (pour le frontend optionnel)

### Installation Rapide

1. **Cloner le repository**
```bash
git clone <repository-url>
cd NoCode
```

2. **Configuration avec le script de lancement**
```bash
python3 launch.py setup
```

3. **Ou installation manuelle**
```bash
# 1. Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer l'environnement
cp .env.example .env
# Éditer le fichier .env avec vos paramètres

# 4. Exécuter les migrations
python manage.py migrate

# 5. Créer un superutilisateur
python manage.py createsuperuser

# 6. Collecter les fichiers statiques
python manage.py collectstatic
```

4. **Démarrer le serveur**
```bash
python manage.py runserver
```

5. **Accéder à la plateforme**
- API Documentation: http://localhost:8000/api/docs/
- Interface Admin: http://localhost:8000/admin/

## ⚙️ Configuration

### Variables d'environnement

Créez un fichier `.env` à la racine du projet :

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key-change-this-in-production
DJANGO_SETTINGS_MODULE=config.settings.development

# Base de données
DATABASE_URL=postgresql://nocode_user:nocode_pass@localhost:5432/nocode_db

# Redis (pour Celery)
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Stripe
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Sécurité
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Logging
LOG_LEVEL=INFO
```

### Configuration Celery (Tâches asynchrones)

```bash
# Démarrer le worker Celery
python manage.py celery worker -l info

# Démarrer le beat pour les tâches planifiées
python manage.py celery beat -l info
```

## 🚀 Utilisation

### Démarrage Rapide

```bash
# Utiliser le script de lancement
python3 launch.py setup    # Configuration complète
python3 launch.py server   # Démarrer le serveur
python3 launch.py check    # Vérifier les prérequis
python3 launch.py test     # Exécuter les tests
```

### Workflow Utilisateur Type

1. **Inscription & Configuration**
   - Créer un compte utilisateur
   - Créer ou rejoindre une organisation
   - Configurer l'abonnement (si nécessaire)

2. **Création de Projet**
   - Accéder au module Studio
   - Créer un nouveau projet
   - Configurer les schémas de données

3. **Conception de l'Interface**
   - Ajouter des pages au projet
   - Configurer les composants via l'interface drag & drop
   - Personnaliser le style et la logique

4. **Automatisation**
   - Créer des workflows automatisés
   - Configurer des intégrations externes
   - Planifier des tâches récurrentes

5. **Déploiement**
   - Générer l'application complète
   - Déployer automatiquement
   - Monitorer les performances

### API Endpoints Principaux

#### Authentification
- `POST /api/v1/foundation/auth/register/client/` - Inscription
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