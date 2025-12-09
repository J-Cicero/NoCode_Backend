# 🚀 NoCode Backend - Distribution Docker Hub

## 📋 Installation Rapide (3 étapes)

**Aucun clonage de code requis !** Les utilisateurs peuvent tester votre plateforme sans accéder au code source.

### 🎯 Étape 1: Télécharger les fichiers

```bash
# Télécharger le fichier de composition Docker
wget https://votre-domaine.com/docker-compose.hub.yml

# OU copier-coller le contenu dans un fichier local nommé docker-compose.hub.yml
```

### 🎯 Étape 2: Configuration de l'environnement

```bash
# Copier le template de configuration
cp .env.example .env

# Éditer .env si nécessaire (optionnel pour test)
nano .env
```

### 🎯 Étape 3: Démarrage

```bash
# Lancer tous les services
docker-compose -f docker-compose.hub.yml up -d

# Vérifier le statut
docker-compose -f docker-compose.hub.yml ps
```

## 🌐 Accès à l'Application

| Service | URL | Description |
|---------|-----|-------------|
| **API NoCode** | http://localhost:8000 | API REST principale |
| **Admin Django** | http://localhost:8000/admin/ | Interface d'administration |
| **Base de données** | localhost:5433 | PostgreSQL |
| **Redis** | localhost:6379 | Cache & Queue |

## 🔑 Compte Superutilisateur

Un superutilisateur est créé automatiquement au premier démarrage :

- **Email**: `admin@test.com`
- **Mot de passe**: `AdminPassword123!`

## 📊 Architecture Déployée

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Service   │    │   PostgreSQL    │    │      Redis      │
│   (API Django)  │────│    Database     │────│   Cache/Queue   │
│   Port: 8000    │    │    Port: 5433   │    │    Port: 6379   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────┐    └─────────────────┐
         │   Celery Worker │    │  Celery Beat     │
         │   (Async Tasks) │    │   (Scheduler)    │
         └─────────────────┘    └─────────────────┘
```

## 🧪 Test de l'API

```bash
# Test de santé de l'API
curl http://localhost:8000/api/v1/foundation/auth/login/

# Test de connexion (POST requis)
curl -X POST http://localhost:8000/api/v1/foundation/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "AdminPassword123!"}'
```

## 📚 Documentation Complète

- **API complète**: [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)
- **Guide rapide**: [docs/QUICK_START.md](docs/QUICK_START.md)
- **Architecture**: [docs/DOCKER_SERVICES.md](docs/DOCKER_SERVICES.md)

## 🔧 Commandes Utiles

```bash
# Voir les logs
docker-compose -f docker-compose.hub.yml logs -f

# Redémarrer les services
docker-compose -f docker-compose.hub.yml restart

# Arrêter tout
docker-compose -f docker-compose.hub.yml down

# Accéder au conteneur web
docker exec -it nocode_web_hub bash

# Créer un superutilisateur manuellement
docker exec -it nocode_web_hub python manage.py createsuperuser
```

## 🛠️ Personnalisation

### Modifier l'image Docker

Éditez `.env` et changez `DOCKER_IMAGE`:
```bash
# Pour utiliser votre propre image
DOCKER_IMAGE=votredockerhub/nocode-backend:v1.0.0
```

### Configuration de la base de données

Éditez `.env` pour personnaliser:
```bash
DB_NAME=ma_base_personnelle
DB_USER=mon_utilisateur
DB_PASSWORD=mon_mot_de_passe_secret
```

### Superutilisateur personnalisé

Éditez `.env`:
```bash
CREATE_SUPERUSER=True
SUPERUSER_EMAIL=admin@monentreprise.com
SUPERUSER_PASSWORD=MonSecret123!
```

## 🚨 Dépannage

### Ports déjà utilisés

```bash
# Vérifier les ports
netstat -tulpn | grep :8000
netstat -tulpn | grep :5433

# Changer les ports dans docker-compose.hub.yml si nécessaire
```

### Permissions refusées

```bash
# Vérifier les permissions Docker
sudo usermod -aG docker $USER
newgrp docker
```

### Conteneurs ne démarrent pas

```bash
# Vérifier les logs détaillés
docker-compose -f docker-compose.hub.yml logs web

# Recréer les conteneurs
docker-compose -f docker-compose.hub.yml down
docker-compose -f docker-compose.hub.yml up -d --force-recreate
```

## 📈 Mise à jour

```bash
# Arrêter les services
docker-compose -f docker-compose.hub.yml down

# Mettre à jour l'image (modifier DOCKER_IMAGE dans .env)
# Exemple: DOCKER_IMAGE=votredockerhub/nocode-backend:v2.0.0

# Redémarrer avec la nouvelle image
docker-compose -f docker-compose.hub.yml up -d
```

## 🎉 Succès !

Si tout fonctionne correctement, vous devriez voir :
- ✅ API accessible sur http://localhost:8000
- ✅ Base de données connectée
- ✅ Superutilisateur créé
- ✅ Services Celery actifs

**Votre plateforme NoCode Backend est maintenant prête !** 🚀
