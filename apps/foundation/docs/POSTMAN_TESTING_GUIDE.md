# Guide de Test avec Postman - Module Foundation

Ce guide vous explique comment tester le module Foundation avec Postman en contournant les problèmes de sécurité en développement.

## 🚀 Configuration Rapide

### 1. Préparer l'Environnement de Développement

```bash
# 1. Appliquer les migrations
python manage.py migrate

# 2. Configurer l'environnement de test
python manage.py setup_dev_environment

# 3. Lancer le serveur de développement
python manage.py runserver 0.0.0.0:8000
```

### 2. Configuration Django pour les Tests

Ajoutez ces paramètres dans votre `settings.py` ou `settings/development.py` :

```python
# settings/development.py
DEBUG = True
ALLOWED_HOSTS = ['*']

# CORS - Autoriser Postman
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-api-key',
    'stripe-signature',
]

# CSRF - Désactiver pour les tests API
CSRF_COOKIE_SECURE = False
CSRF_USE_SESSIONS = False
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Middleware de développement
MIDDLEWARE = [
    'apps.foundation.middleware.dev_middleware.DevCORSMiddleware',
    'apps.foundation.middleware.dev_middleware.DevCSRFExemptMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.foundation.middleware.dev_middleware.DevRequestLoggingMiddleware',
]

# JWT - Tokens plus longs en développement
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
}
```

## 🔑 Authentification avec Postman

### Étape 1: Connexion

**POST** `http://localhost:8000/api/auth/login/`

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "email": "client@test.dev",
    "password": "TestPass123!"
}
```

**Réponse attendue:**
```json
{
    "success": true,
    "user": {
        "id": 1,
        "email": "client@test.dev",
        "user_type": "CLIENT"
    },
    "tokens": {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
}
```

### Étape 2: Utiliser le Token

Pour toutes les requêtes suivantes, ajoutez ce header :

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json
```

## 📋 Tests des Endpoints Principaux

### 1. Inscription d'un Nouvel Utilisateur

**POST** `http://localhost:8000/api/auth/register/`

**Body (Client):**
```json
{
    "email": "nouveau.client@test.dev",
    "password": "TestPass123!",
    "user_type": "CLIENT",
    "profile_data": {
        "first_name": "Marie",
        "last_name": "Dupont",
        "phone": "+33123456789",
        "date_of_birth": "1985-05-15"
    }
}
```

**Body (Entreprise):**
```json
{
    "email": "nouvelle.entreprise@test.dev",
    "password": "TestPass123!",
    "user_type": "ENTREPRISE",
    "profile_data": {
        "company_name": "Nouvelle Entreprise SAS",
        "siret": "12345678901234",
        "legal_form": "SAS",
        "address": "456 Avenue Test",
        "postal_code": "69000",
        "city": "Lyon",
        "country": "France"
    }
}
```

### 2. Gestion des Organisations

**GET** `http://localhost:8000/api/organizations/`
- Lister les organisations de l'utilisateur connecté

**POST** `http://localhost:8000/api/organizations/`
```json
{
    "name": "Mon Organisation",
    "description": "Description de mon organisation",
    "organization_type": "COMPANY"
}
```

**GET** `http://localhost:8000/api/organizations/{id}/`
- Détails d'une organisation spécifique

### 3. Gestion des Membres

**POST** `http://localhost:8000/api/organizations/{org_id}/members/`
```json
{
    "user_id": 2,
    "role": "MEMBER"
}
```

**POST** `http://localhost:8000/api/organizations/{org_id}/invite/`
```json
{
    "email": "invite@example.com",
    "role": "MEMBER",
    "message": "Rejoignez notre organisation !"
}
```

### 4. Facturation et Abonnements

**GET** `http://localhost:8000/api/organizations/{org_id}/subscription/`
- Détails de l'abonnement

**POST** `http://localhost:8000/api/organizations/{org_id}/subscription/`
```json
{
    "plan_name": "Premium",
    "plan_price": "29.99",
    "billing_cycle": "MONTHLY"
}
```

### 5. Vérification d'Entreprise

**POST** `http://localhost:8000/api/verification/`
```json
{
    "request_type": "KYB_FULL"
}
```

**POST** `http://localhost:8000/api/verification/{verification_id}/documents/`
- Upload de document (multipart/form-data)
- Champs: `document_type`, `file`

## 🛠️ Résolution des Problèmes Courants

### Problème: CORS Error
**Solution:** Vérifiez que `DevCORSMiddleware` est activé dans `MIDDLEWARE`.

### Problème: CSRF Token Missing
**Solution:** Utilisez `DevCSRFExemptMiddleware` ou ajoutez `X-CSRFToken` header.

### Problème: 401 Unauthorized
**Solutions:**
1. Vérifiez que le token JWT est valide et non expiré
2. Utilisez le format: `Authorization: Bearer <token>`
3. En dernier recours, utilisez le token de test: `Bearer dev-test-token-123`

### Problème: 403 Forbidden
**Solution:** Vérifiez que l'utilisateur a les permissions nécessaires pour l'endpoint.

### Problème: 429 Too Many Requests
**Solution:** Le rate limiting est actif. Attendez ou augmentez les limites en développement.

## 🧪 Collection Postman

### Variables d'Environnement Postman

Créez un environnement "Foundation Dev" avec ces variables :

```
base_url: http://localhost:8000
access_token: (sera rempli automatiquement)
refresh_token: (sera rempli automatiquement)
user_id: (sera rempli automatiquement)
org_id: (sera rempli automatiquement)
```

### Script de Pré-requête Global

```javascript
// Ajouter automatiquement le token d'authentification
if (pm.environment.get("access_token")) {
    pm.request.headers.add({
        key: "Authorization",
        value: "Bearer " + pm.environment.get("access_token")
    });
}
```

### Script de Test pour Login

```javascript
// Sauvegarder les tokens après connexion
if (pm.response.code === 200) {
    const response = pm.response.json();
    if (response.tokens) {
        pm.environment.set("access_token", response.tokens.access);
        pm.environment.set("refresh_token", response.tokens.refresh);
        pm.environment.set("user_id", response.user.id);
    }
}
```

## 🔧 Commandes Utiles

```bash
# Créer un superutilisateur
python manage.py createsuperuser

# Réinitialiser les données de test
python manage.py setup_dev_environment --reset

# Vérifier les logs en temps réel
python manage.py runserver --verbosity=2

# Tester les endpoints avec curl
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "client@test.dev", "password": "TestPass123!"}'
```

## ⚠️ Sécurité en Production

**IMPORTANT:** Ces configurations sont uniquement pour le développement !

En production, vous devez :
- Activer HTTPS
- Configurer CORS strictement
- Activer CSRF protection
- Utiliser des tokens JWT avec expiration courte
- Activer le rate limiting strict
- Supprimer les middlewares de développement

## 📞 Support

Si vous rencontrez des problèmes :
1. Vérifiez les logs du serveur Django
2. Utilisez les outils de développement du navigateur
3. Testez d'abord avec curl avant Postman
4. Vérifiez que tous les middlewares de développement sont actifs
