# Foundation Module

Module Foundation - Cœur de l'architecture NoCode avec gestion multi-tenant, authentification par rôles, et abonnements.

## 🏗️ Architecture

### Structure du Module

```
foundation/
├── models/                 # Modèles de données
│   ├── base.py            # BaseModel avec champs communs
│   ├── user.py            # User avec rôles (CLIENT/ADMIN)
│   ├── organization.py    # Organization et OrganizationMember
│   └── subscription.py    # TypeAbonnement et Abonnement
├── services/              # Services métier
│   ├── auth_service.py    # Service d'authentification
│   ├── user_service.py    # Service utilisateur
│   ├── organization_service.py  # Service organisations
│   └── event_bus.py       # Bus d'événements
│   ├── organization_service.py # Service d'organisation
│   ├── billing_service.py # Service de facturation
│   └── verification_service.py # Service de vérification
├── serializers/           # Serializers DRF
├── views/                 # Vues et API endpoints
├── permissions/           # Système de permissions
├── middlewares/           # Middlewares personnalisés
├── integrations/          # Intégrations externes
│   └── stripe/           # Intégration Stripe
├── tasks/                # Tâches Celery asynchrones
├── utils/                # Utilitaires et validators
└── tests/                # Tests unitaires
```

## 🚀 Fonctionnalités Principales

### 1. Gestion Multi-Tenant
- **Organisations** : Gestion complète des organisations avec rôles et permissions
- **Membres** : Système d'invitation et de gestion des membres
- **Isolation** : Isolation complète des données par tenant

### 2. Authentification et Autorisation
- **JWT** : Authentification basée sur JWT avec refresh tokens
- **Permissions** : Système de permissions granulaire et extensible
- **Middlewares** : Protection automatique des endpoints

### 3. Facturation et Abonnements
- **Stripe** : Intégration complète avec Stripe
- **Abonnements** : Gestion des plans et cycles de facturation
- **Webhooks** : Traitement automatique des événements Stripe

### 4. Vérification des Entreprises
- **KYB** : Processus de vérification Know Your Business
- **Documents** : Upload et validation de documents
- **Workflow** : Processus de validation automatisé

### 5. Architecture Événementielle
- **EventBus** : Communication découplée entre composants
- **Audit** : Traçabilité complète des actions
- **Notifications** : Système de notifications asynchrones

## 📋 Modèles de Données

### Utilisateurs
- **User** : Modèle utilisateur personnalisé avec types CLIENT/ENTREPRISE
- **Client** : Profil client avec informations personnelles
- **Entreprise** : Profil entreprise avec SIRET et vérification

### Organisations
- **Organization** : Organisation multi-tenant
- **OrganizationMember** : Membres avec rôles (OWNER, ADMIN, MEMBER)
- **OrganizationInvitation** : Invitations avec expiration

### Facturation
- **Subscription** : Abonnements avec plans et cycles
- **Invoice** : Factures avec calculs de TVA
- **PaymentMethod** : Moyens de paiement Stripe

### Vérification
- **VerificationRequest** : Demandes de vérification KYB
- **VerificationDocument** : Documents uploadés avec validation

## 🔧 Services

### AuthService
```python
from apps.foundation.services import AuthService

auth_service = AuthService()

# Inscription
result = auth_service.register_user(user_data, profile_data)

# Authentification
result = auth_service.authenticate_user(email, password)

# Rafraîchissement de token
result = auth_service.refresh_token(refresh_token)
```

### OrganizationService
```python
from apps.foundation.services import OrganizationService

org_service = OrganizationService()

# Création d'organisation
result = org_service.create_organization(owner, org_data)

# Ajout de membre
result = org_service.add_member(org_id, user_id, role)

# Invitation
result = org_service.invite_member(org_id, email, role)
```

### BillingService
```python
from apps.foundation.services import BillingService

billing_service = BillingService()

# Création d'abonnement
result = billing_service.create_subscription(org_id, subscription_data)

# Annulation
result = billing_service.cancel_subscription(subscription_id)
```

## 🔒 Permissions

### Permissions de Base
- **IsOwner** : Propriétaire de la ressource
- **IsOrganizationMember** : Membre de l'organisation
- **IsOrganizationAdmin** : Administrateur de l'organisation
- **HasActiveBilling** : Facturation active
- **IsVerifiedEnterprise** : Entreprise vérifiée

### Utilisation
```python
from apps.foundation.permissions import IsOrganizationMember

class MyView(APIView):
    permission_classes = [IsAuthenticated, IsOrganizationMember]
```

## 🛡️ Middlewares

### Middlewares Disponibles
- **JWTAuthenticationMiddleware** : Authentification JWT
- **TenantMiddleware** : Contexte multi-tenant
- **AuditMiddleware** : Audit des actions
- **CORSMiddleware** : Gestion CORS
- **RateLimitMiddleware** : Limitation de débit

### Configuration
```python
# settings.py
MIDDLEWARE = [
    'apps.foundation.middleware.JWTAuthenticationMiddleware',
    'apps.foundation.middleware.TenantMiddleware',
    'apps.foundation.middleware.AuditMiddleware',
    # ...
]
```

## 💳 Intégration Stripe

### Configuration
```python
# settings.py
STRIPE_PUBLISHABLE_KEY = 'pk_...'
STRIPE_SECRET_KEY = 'sk_...'
STRIPE_WEBHOOK_SECRET = 'whsec_...'
```

### Webhooks
Les webhooks Stripe sont automatiquement traités :
- Paiements réussis/échoués
- Changements d'abonnement
- Factures créées/payées
- Clients créés/mis à jour

## 🔧 Utilitaires

### Validators
```python
from apps.foundation.utils.validators import SIRETValidator, PhoneNumberValidator

# Validation SIRET
validator = SIRETValidator()
validator('73282932000074')  # OK

# Validation téléphone
validator = PhoneNumberValidator()
validator('+33123456789')  # OK
```

### Helpers
```python
from apps.foundation.utils.helpers import format_currency, generate_unique_token

# Formatage devise
amount = format_currency(1234.56)  # "1 234,56 €"

# Génération token
token = generate_unique_token()
```

### Sécurité
```python
from apps.foundation.utils.security import encrypt_data, hash_sensitive_data

# Chiffrement
encrypted = encrypt_data("sensitive_data")
decrypted = decrypt_data(encrypted)

# Hachage
hashed = hash_sensitive_data("password")
is_valid = verify_hashed_data("password", hashed)
```

## 📊 Tâches Asynchrones

### Tâches Email
- Emails de bienvenue
- Vérification d'email
- Réinitialisation de mot de passe
- Notifications de facturation

### Tâches Facturation
- Synchronisation Stripe
- Traitement des paiements échoués
- Génération de factures
- Rappels de paiement

### Tâches Vérification
- Traitement de documents
- Notifications de statut
- Nettoyage automatique

### Utilisation
```python
from apps.foundation.tasks import send_welcome_email

# Tâche asynchrone
send_welcome_email.delay(user_id)

# Tâche différée
send_welcome_email.apply_async(args=[user_id], countdown=60)
```

## 🧪 Tests

### Exécution des Tests
```bash
# Tous les tests du module
python manage.py test apps.foundation

# Tests spécifiques
python manage.py test apps.foundation.tests.test_models
python manage.py test apps.foundation.tests.test_services
python manage.py test apps.foundation.tests.test_views
python manage.py test apps.foundation.tests.test_utils
```

### Coverage
```bash
# Installation
pip install coverage

# Exécution avec coverage
coverage run --source='apps.foundation' manage.py test apps.foundation
coverage report
coverage html
```

## 📈 Monitoring et Logging

### EventBus
```python
from apps.foundation.services.event_bus import EventBus

# Publication d'événement
EventBus.publish('user.registered', {
    'user_id': user.id,
    'email': user.email
})

# Abonnement
def handle_user_registered(event_type, data):
    print(f"Nouvel utilisateur: {data['email']}")

EventBus.subscribe('user.registered', handle_user_registered)
```

### Logs
Les logs sont automatiquement générés pour :
- Actions utilisateur
- Erreurs système
- Événements de sécurité
- Performance

## 🔧 Configuration

### Variables d'Environnement
```bash
# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_LIFETIME=15  # minutes
JWT_REFRESH_TOKEN_LIFETIME=7  # jours

# Stripe
STRIPE_PUBLISHABLE_KEY=pk_...
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
DEFAULT_FROM_EMAIL=noreply@example.com

# Frontend
FRONTEND_URL=https://app.example.com

# Chiffrement
ENCRYPTION_KEY=your-encryption-key
```

### Settings Django
```python
# apps/foundation/apps.py
INSTALLED_APPS = [
    # ...
    'apps.foundation',
    'rest_framework',
    'rest_framework_simplejwt',
    # ...
]

# Configuration JWT
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

# Configuration DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

## 🚀 Déploiement

### Migrations
```bash
# Créer les migrations
python manage.py makemigrations foundation

# Appliquer les migrations
python manage.py migrate foundation
```

### Collecte des Fichiers Statiques
```bash
python manage.py collectstatic
```

### Celery
```bash
# Worker Celery
celery -A your_project worker -l info

# Beat Celery (tâches périodiques)
celery -A your_project beat -l info

# Monitoring
celery -A your_project flower
```

## 📚 API Documentation

### Endpoints Principaux

#### Authentification
- `POST /api/auth/register/` - Inscription
- `POST /api/auth/login/` - Connexion
- `POST /api/auth/refresh/` - Rafraîchissement token
- `POST /api/auth/logout/` - Déconnexion

#### Organisations
- `GET /api/organizations/` - Liste des organisations
- `POST /api/organizations/` - Création d'organisation
- `GET /api/organizations/{id}/` - Détails d'organisation
- `POST /api/organizations/{id}/members/` - Ajout de membre
- `POST /api/organizations/{id}/invite/` - Invitation

#### Facturation
- `GET /api/organizations/{id}/subscription/` - Abonnement
- `POST /api/organizations/{id}/subscription/` - Création d'abonnement
- `POST /api/organizations/{id}/subscription/cancel/` - Annulation
- `GET /api/organizations/{id}/invoices/` - Factures

#### Vérification
- `POST /api/verification/` - Démarrage vérification
- `POST /api/verification/{id}/documents/` - Upload document
- `GET /api/verification/{id}/status/` - Statut vérification

### Format des Réponses
```json
{
    "success": true,
    "data": { ... },
    "message": "Opération réussie",
    "errors": null
}
```

## 🤝 Contribution

### Standards de Code
- PEP 8 pour Python
- Docstrings pour toutes les fonctions publiques
- Tests unitaires obligatoires
- Coverage minimum 80%

### Workflow
1. Fork du repository
2. Création d'une branche feature
3. Développement avec tests
4. Pull request avec description détaillée

## 📄 Licence

Ce module est sous licence propriétaire. Tous droits réservés.

## 📞 Support

Pour toute question ou problème :
- Documentation : [docs.example.com](https://docs.example.com)
- Issues : [github.com/project/issues](https://github.com/project/issues)
- Email : support@example.com
