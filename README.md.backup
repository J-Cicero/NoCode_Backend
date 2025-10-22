# Usanidi NoCode Platform

Une plateforme Django NoCode complète permettant aux utilisateurs de créer des applications web sans écrire de code.

## 🏗️ Architecture

La plateforme est organisée en 6 modules principaux :

- **Foundation** : Services de base (authentification, facturation, permissions)
- **Studio** : Interface de création de projets et gestion des métadonnées
- **Automation** : Moteur de workflows et intégrations externes
- **Runtime** : Génération de code Django et déploiement automatisé
- **Insights** : Analytics, monitoring et rapports
- **Marketplace** : Store de composants et templates

## 🚀 Installation Rapide

### Prérequis

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optionnel)

### Configuration locale

1. **Cloner le projet**
```bash
git clone <repository-url>
cd usanidi_platform
```

2. **Créer l'environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Installer les dépendances**
```bash
pip install -r requirements/development.txt
```

4. **Configuration des variables d'environnement**
```bash
cp .env.example .env
# Éditer le fichier .env avec vos paramètres
```

5. **Préparer la base de données PostgreSQL**
```bash
# Créer la base de données
createdb usanidi_platform

# Appliquer les migrations
python manage.py migrate
```

6. **Créer un superutilisateur**
```bash
python manage.py createsuperuser
```

7. **Lancer Redis et Celery**
```bash
# Terminal 1: Redis (si pas via Docker)
redis-server

# Terminal 2: Celery worker
celery -A config worker -l info

# Terminal 3: Celery beat (tâches périodiques)
celery -A config beat -l info
```

8. **Lancer le serveur de développement**
```bash
python manage.py runserver
```

### Installation avec Docker

```bash
# Lancer tous les services
docker-compose up -d

# Voir les logs
docker-compose logs -f web
```

## 🔧 Configuration des Services

### PostgreSQL
```sql
-- Créer la base de données
CREATE DATABASE usanidi_platform;
CREATE USER usanidi WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE usanidi_platform TO usanidi;
```

### Redis
Redis est utilisé pour :
- Cache Django
- File d'attente Celery
- Sessions WebSocket

### Stripe (Paiements)
1. Créer un compte Stripe
2. Récupérer les clés API (test/production)
3. Configurer les webhooks pour `/webhooks/stripe/`

## 📖 Documentation API

Une fois le serveur lancé, la documentation interactive est disponible :
- Swagger UI : `http://localhost:8000/api/docs/`
- Redoc : `http://localhost:8000/api/redoc/`
- Schéma OpenAPI : `http://localhost:8000/api/schema/`

## 🧪 Tests

```bash
# Lancer tous les tests
pytest

# Tests avec couverture
pytest --cov=apps --cov-report=html

# Tests d'un module spécifique
pytest apps/foundation/tests/
```

## 📦 Structure du Projet

```
usanidi_platform/
├── config/              # Configuration Django
├── apps/                # Modules métier
│   ├── foundation/      # Base technique
│   ├── studio/          # Projets NoCode
│   ├── automation/      # Workflows
│   ├── runtime/         # Génération code
│   ├── insights/        # Analytics
│   └── marketplace/     # Store
├── generated_apps/      # Apps générées
└── requirements/        # Dépendances
```

## 🚀 Déploiement

### Développement
```bash
python manage.py runserver --settings=config.settings.development
```

### Production
```bash
# Variables d'environnement
export DJANGO_SETTINGS_MODULE=config.settings.production
export SECRET_KEY=your-production-secret-key

# Migrations et collecte des fichiers statiques
python manage.py migrate
python manage.py collectstatic --noinput

# Lancer avec Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Docker Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 🔒 Sécurité

### Checklist de sécurité
- [ ] SECRET_KEY unique en production
- [ ] DEBUG=False en production
- [ ] HTTPS activé
- [ ] Variables sensibles dans .env
- [ ] Backup base de données
- [ ] Monitoring avec Sentry

## 📊 Monitoring

### Métriques disponibles
- Performance des APIs
- Utilisation des resources
- Erreurs et exceptions
- Activité utilisateur

### Logs
Les logs sont stockés dans `logs/django.log` et envoyés vers Sentry en production.

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit les changes (`git commit -am 'Ajouter nouvelle fonctionnalité'`)
4. Push vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request

## 📝 License

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🆘 Support

- Documentation : `/docs/`
- Issues : GitHub Issues
- Email : support@usanidi.com