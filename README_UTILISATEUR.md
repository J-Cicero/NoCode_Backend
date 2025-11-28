# 🚀 NoCode Backend - Guide pour Utilisateurs

## ⚡ **Vérification Rapide (1 seule commande)**

Copiez-collez cette commande pour vérifier que tout fonctionne :
```bash
curl -I http://localhost:8000/api/docs/ 2>/dev/null | head -1
```
**Résultat attendu :** `HTTP/1.1 200 OK`
Si vous voyez `200 OK`, ✅ votre API fonctionne !

---

## ⚠️ **SÉCURITÉ CRITIQUE**

Si vous voyez un mot de passe Gmail comme `zsat fbsy oytx mrlx` dans les fichiers, 
**RÉVOQUEZ-LE IMMÉDIATEMENT** : https://myaccount.google.com/apppasswords

---

## 📋 Démarrage Rapide (Même si vous n'êtes pas développeur)

### 🏠 **Lancement Local (Test sur votre machine)**

#### 1. Installation de Docker (une seule fois)
```bash
# Sur Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Redémarrer votre ordinateur ou faire:
newgrp docker

# Installer Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. Télécharger et lancer le projet
```bash
# Télécharger le projet (remplacer par l'URL réelle)
git clone https://github.com/votre-repo/NoCode_Backend.git
cd NoCode_Backend

# Lancer TOUS les services (base de données + API)
docker compose up -d

# Attendre 30 secondes que tout démarre
sleep 30

# Vérifier que tout fonctionne
docker compose ps
```

#### 3. Accéder aux services
🌐 **API principale**: http://localhost:8000
🔧 **Administration**: http://localhost:8000/admin
📚 **Documentation API**: http://localhost:8000/api/docs/

#### 🎯 **Test Visuel (Plus simple que curl)**
1. **Ouvrez votre navigateur web**
2. **Allez à**: http://localhost:8000/api/docs/
3. **Vous devriez voir**: Une interface Swagger/UI interactive avec tous les endpoints
4. **Testez**: Cliquez sur n'importe quel endpoint → "Try it out" → "Execute"

Si vous voyez l'interface Swagger, ✅ **votre API fonctionne parfaitement !**

### 🧪 **Tester les API (sans code)**

#### Créer un compte utilisateur
```bash
# Créer un superutilisateur pour tester
docker compose exec web python manage.py createsuperuser

# Répondre aux questions:
# Email: test@example.com
# Password: votre-mot-de-passe
# Password (again): votre-mot-de-passe
```

#### Tester avec curl (dans le terminal)
```bash
# 1. Obtenir un token d'authentification
curl -X POST http://localhost:8000/api/v1/foundation/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "votre-mot-de-passe"}'

# 2. Lister les projets (copier le token de la réponse 1)
TOKEN="votre-token-ici"
curl -X GET http://localhost:8000/api/v1/runtime/projects/ \
  -H "Authorization: Bearer $TOKEN"

# 3. Créer un projet
curl -X POST http://localhost:8000/api/v1/runtime/projects/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Mon Projet Test", "description": "Description de test"}'
```

#### Tester avec Postman (plus simple)
1. Ouvrir Postman
2. Importer cette URL: http://localhost:8000/api/docs/
3. Les endpoints apparaissent avec documentation interactive
4. Cliquer sur "Try it out" pour tester

### 🏭 **Lancement Production (Serveur)**

#### 1. Prérequis serveur
```bash
# Sur votre serveur (Ubuntu/Debian recommandé)
sudo apt update && sudo apt upgrade -y

# Installer Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Configurer le firewall
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

#### 2. Configurer le domaine
```bash
# Remplacer votredomaine.com par votre vrai domaine
DOMAIN="votredomaine.com"

# Créer le dossier pour les certificats SSL
mkdir -p /home/$USER/NoCode_Backend/ssl_certs
```

#### 3. Obtenir un certificat SSL (gratuit avec Let's Encrypt)
```bash
# Installer Certbot
sudo apt install certbot

# Obtenir le certificat (remplacer votredomaine.com)
sudo certbot certonly --standalone -d $DOMAIN -d www.$DOMAIN

# Copier les certificats pour Docker
sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /home/$USER/NoCode_Backend/ssl_certs/cert.pem
sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /home/$USER/NoCode_Backend/ssl_certs/key.pem
sudo chown $USER:$USER /home/$USER/NoCode_Backend/ssl_certs/*
```

#### 4. Configurer l'environnement production
```bash
cd /home/$USER/NoCode_Backend

# Créer le fichier de configuration production
cp .env.production .env.production.local

# Éditer le fichier (remplacer les valeurs)
nano .env.production.local
```

**Éditer `.env.production.local` avec vos vraies valeurs:**
```bash
# Django
SECRET_KEY=generer-une-nouvelle-clé-ici
DEBUG=False
ALLOWED_HOSTS=votredomaine.com,www.votredomaine.com

# Base de données
DB_NAME=nocode_platform_prod
DB_USER=nocode_user_prod
DB_PASSWORD=mot-de-passe-super-secret-ici
DB_HOST=db
DB_PORT=5432

# Email
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe-app-gmail
```

#### 5. Lancer en production
```bash
# Construire et démarrer
docker compose -f docker-compose.prod.yml --env-file .env.production.local up -d --build

# Attendre le démarrage
sleep 60

# Vérifier que tout fonctionne
docker compose -f docker-compose.prod.yml ps

# Créer le superutilisateur
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

#### 6. Accéder à votre API en production
🌐 **API principale**: https://votredomaine.com
🔧 **Administration**: https://votredomaine.com/admin
📚 **Documentation API**: https://votredomaine.com/api/docs/

## 🔧 **Commandes Utiles**

### Vérifier l'état des services
```bash
# Local
docker compose ps

# Production
docker compose -f docker-compose.prod.yml ps
```

### Voir les logs (en cas de problème)
```bash
# Local
docker compose logs -f web

# Production
docker compose -f docker-compose.prod.yml logs -f web
```

### Redémarrer les services
```bash
# Local
docker compose restart web

# Production
docker compose -f docker-compose.prod.yml restart web
```

### Arrêter tout
```bash
# Local
docker compose down

# Production
docker compose -f docker-compose.prod.yml down
```

## 📊 **Tester que tout fonctionne**

### Tests de base
```bash
# Test de documentation API (doit retourner 200)
curl -I http://localhost:8000/api/docs/

# Test de l'admin (doit afficher la page de login)
curl -I http://localhost:8000/admin/

# Test des endpoints disponibles (doit montrer la liste)
curl http://localhost:8000/ | grep -E "api/"
```

### Tests avec authentification
```bash
# 1. Créer un utilisateur de test d'abord
docker compose exec web python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='test@example.com').exists():
    User.objects.create_user('test@example.com', 'password123')
    print('Utilisateur test créé')
else:
    print('Utilisateur test existe déjà')
EOF

# 2. Se connecter et obtenir le token
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/foundation/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}')

echo "Réponse de connexion:"
echo "$RESPONSE"

# 3. Extraire le token (méthode simple)
TOKEN=$(echo "$RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'access' in data:
        print(data['access'])
    else:
        print('Token non trouvé dans:', data)
except:
    print('Erreur de parsing JSON')
")

echo "Token obtenu: ${TOKEN:0:50}..."

# 4. Tester un endpoint protégé
curl -X GET http://localhost:8000/api/v1/runtime/projects/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

## 🆘 **Dépannage Rapide**

### Problème: "Port déjà utilisé"
```bash
# Vérifier qui utilise le port 8000
sudo lsof -i :8000

# Arrêter le service conflictuel
sudo systemctl stop apache2 nginx
```

### Problème: "Conteneur ne démarre pas"
```bash
# Voir les logs d'erreur
docker compose logs web

# Reconstruire l'image
docker compose down
docker compose up -d --build
```

### Problème: "Base de données inaccessible"
```bash
# Redémarrer uniquement la base de données
docker compose restart db

# Vérifier la connexion
docker compose exec db pg_isready -U nocode_user
```

## 📞 **Support**

Si quelque chose ne fonctionne pas:
1. Vérifier les logs avec `docker compose logs`
2. Consulter la documentation complète: `DEPLOYMENT.md`
3. Redémarrer complètement: `docker compose down && docker compose up -d`

## 🎯 **Checklist de Vérification**

Avant de dire que c'est terminé:
- [ ] Docker installé et fonctionnel
- [ ] `docker compose ps` montre tous les services "Up"
- [ ] http://localhost:8000/admin affiche la page de login
- [ ] http://localhost:8000/api/docs/ charge la documentation
- [ ] Vous pouvez créer un utilisateur et vous connecter
- [ ] Les tests curl retournent des réponses JSON valides

**🎉 Si tout est coché, votre API NoCode est prête !**
