# 🚀 Guide de Déploiement Docker - NoCode Backend

## 📋 Prérequis

- Docker 20.10+ et Docker Compose 2.0+
- Domaine configuré avec DNS pointant vers le serveur
- Certificats SSL (Let's Encrypt recommandé)

## 🔧 Développement Local

### Démarrage rapide
```bash
# Cloner le projet
git clone <repository-url>
cd NoCode_Backend

# Configuration (copier et adapter .env)
cp .env.example .env
# Éditer .env avec vos configurations

# Démarrer tous les services
docker compose up -d

# Appliquer les migrations
docker compose exec web python manage.py migrate

# Créer un superutilisateur
docker compose exec web python manage.py createsuperuser

# Vérifier les services
docker compose ps
```

### Services disponibles
- **API Django**: http://localhost:8000
- **Admin Django**: http://localhost:8000/admin
- **PostgreSQL**: localhost:5433
- **Redis**: localhost:6379

## 🏭 Déploiement Production

### 1. Préparation de l'environnement
```bash
# Sur le serveur de production
git clone <repository-url>
cd NoCode_Backend

# Configuration production
cp .env.production .env.production.local
# Éditer .env.production.local avec vos vraies valeurs
```

### 2. Configuration SSL
```bash
# Créer le dossier SSL
mkdir -p ssl_certs

# Avec Let's Encrypt (recommandé)
certbot certonly --standalone -d votredomaine.com -d www.votredomaine.com
cp /etc/letsencrypt/live/votredomaine.com/fullchain.pem ssl_certs/cert.pem
cp /etc/letsencrypt/live/votredomaine.com/privkey.pem ssl_certs/key.pem

# Ou avec vos propres certificats
# Copier cert.pem et key.pem dans ssl_certs/
```

### 3. Déploiement
```bash
# Construire et démarrer les services de production
docker compose -f docker-compose.prod.yml --env-file .env.production.local up -d --build

# Vérifier le déploiement
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs web
```

### 4. Vérification post-déploiement
```bash
# Tester l'API
curl -k https://votredomaine.com/api/v1/foundation/auth/login/

# Vérifier les certificats SSL
curl -I https://votredomaine.com/

# Tester l'admin Django
# Naviguer vers https://votredomaine.com/admin
```

## 🔍 Maintenance

### Logs et monitoring
```bash
# Voir tous les logs
docker compose -f docker-compose.prod.yml logs -f

# Logs spécifiques
docker compose -f docker-compose.prod.yml logs -f web
docker compose -f docker-compose.prod.yml logs -f celery

# Health checks
docker compose -f docker-compose.prod.yml exec web python manage.py check --deploy
```

### Sauvegarde de la base de données
```bash
# Exporter la base de données
docker compose -f docker-compose.prod.yml exec db pg_dump -U nocode_user_prod nocode_platform_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurer la base de données
docker compose -f docker-compose.prod.yml exec -T db psql -U nocode_user_prod nocode_platform_prod < backup_20241201_120000.sql
```

### Mises à jour
```bash
# Mettre à jour le code
git pull origin main

# Reconstruire et redémarrer
docker compose -f docker-compose.prod.yml up -d --build

# Appliquer les migrations si nécessaire
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

## 🚨 Dépannage

### Problèmes courants

#### Port déjà utilisé
```bash
# Vérifier les ports utilisés
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443

# Arrêter les services conflictuels
sudo systemctl stop nginx apache2
```

#### Problèmes de base de données
```bash
# Vérifier la connexion DB
docker compose -f docker-compose.prod.yml exec web python manage.py dbshell

# Redémarrer uniquement la base de données
docker compose -f docker-compose.prod.yml restart db
```

#### Certificats SSL expirés
```bash
# Renouveler avec Let's Encrypt
certbot renew
cp /etc/letsencrypt/live/votredomaine.com/fullchain.pem ssl_certs/cert.pem
cp /etc/letsencrypt/live/votredomaine.com/privkey.pem ssl_certs/key.pem
docker compose -f docker-compose.prod.yml restart nginx
```

## 🔐 Sécurité

### Checklist de sécurité
- [ ] Mot de passe base de données robuste
- [ ] Clé secrète Django unique et longue
- [ ] Certificats SSL valides
- [ ] Headers de sécurité configurés
- [ ] Rate limiting activé
- [ ] Logs activés et surveillés
- [ ] Sauvegardes automatiques
- [ ] Firewall configuré (ports 80, 443 uniquement)

### Variables d'environnement critiques
```bash
# Générer une nouvelle clé secrète Django
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Révoquer les mots de passe exposés
# Gmail: https://myaccount.google.com/apppasswords
```

## 📊 Monitoring

### Métriques à surveiller
- CPU et mémoire des conteneurs
- Espace disque (volumes Docker)
- Connexions à la base de données
- Taux d'erreurs HTTP (4xx, 5xx)
- Temps de réponse API

### Commandes utiles
```bash
# Statistiques Docker
docker stats

# Espace disque
df -h
docker system df

# Performance des conteneurs
docker compose -f docker-compose.prod.yml exec web python manage.py check --deploy
```

## 🔄 Rollback

En cas de problème après mise à jour :
```bash
# Revenir à la version précédente
git checkout <previous-commit-tag>

# Redémarrer avec l'ancienne version
docker compose -f docker-compose.prod.yml up -d --build

# Si nécessaire, restaurer la base de données
docker compose -f docker-compose.prod.yml exec -T db psql -U nocode_user_prod nocode_platform_prod < backup_avant_mise_a_jour.sql
```

## 📞 Support

Pour toute question ou problème :
1. Vérifier les logs avec `docker compose logs`
2. Consulter la documentation Django officielle
3. Vérifier l'état des services avec `docker compose ps`
