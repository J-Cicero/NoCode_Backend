# 🔐 Foundation API - Authentification & Gestion des Utilisateurs

## 📋 Vue d'ensemble

Le module Foundation gère **toute l'identité et l'organisation** de la plateforme NoCode. Il fournit l'authentification JWT, la gestion des utilisateurs, les organisations multi-tenant, et les abonnements.

**Base URL :** `/api/v1/foundation/`

---

## 🔑 **Authentification JWT**

### POST `/auth/login/`
**Connexion utilisateur avec tokens JWT**

**Requête :**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Réponse (200) :**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyX3V1aWQiLCJpYXQiOjE2MDk0NTkyMDAsImV4cCI6MTYwOTQ2MjgwMCwiZW1haWwiOiJ1c2VyQGV4YW1wbGUuY29tIiwicm9sZSI6IkNMSUVOVCIsIm9yZ2FuaXphdGlvbiI6bnVsbH0.signature",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyX3V1aWQiLCJpYXQiOjE2MDk0NTkyMDAsImV4cCI6MTYxMjA1MTIwMH0.signature",
  "user": {
    "id": 1,
    "tracking_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "nom": "Doe",
    "prenom": "John",
    "full_name": "John Doe",
    "role": "CLIENT",
    "numero_telephone": "+33612345678",
    "pays": "France",
    "is_active": true,
    "email_verified": true,
    "phone_verified": false,
    "date_joined": "2024-01-01T10:00:00Z",
    "last_login": "2024-01-01T15:30:00Z"
  },
  "organizations": [
    {
      "id": 1,
      "tracking_id": "org-uuid-here",
      "name": "Tech Company",
      "role": "OWNER",
      "member_count": 5
    }
  ],
  "permissions": ["read", "write", "profile"]
}
```

**Erreurs :**
- `400` : Email ou mot de passe manquant
- `401` : Identifiants incorrects
- `403` : Compte désactivé

---

### POST `/auth/register/client/`
**Inscription d'un nouveau client**

**Requête :**
```json
{
  "email": "newuser@example.com",
  "password": "SecurePassword123!",
  "password_confirm": "SecurePassword123!",
  "nom": "Doe",
  "prenom": "John",
  "pays": "France",
  "numero_telephone": "+33612345678"
}
```

**Réponse (201) :**
```json
{
  "message": "Utilisateur créé avec succès",
  "user": {
    "id": 2,
    "tracking_id": "550e8400-e29b-41d4-a716-446655440001",
    "email": "newuser@example.com",
    "nom": "Doe",
    "prenom": "John",
    "full_name": "John Doe",
    "role": "CLIENT",
    "is_active": true,
    "email_verified": false,
    "date_joined": "2024-01-01T10:00:00Z"
  },
  "verification_email_sent": true
}
```

**Validation :**
- `password` : Minimum 8 caractères, 1 majuscule, 1 chiffre
- `email` : Format email valide et unique
- `password_confirm` : Doit correspondre au password

---

### POST `/auth/refresh/`
**Rafraîchissement du access token**

**Requête :**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyX3V1aWQiLCJpYXQiOjE2MDk0NTkyMDAsImV4cCI6MTYxMjA1MTIwMH0.signature"
}
```

**Réponse (200) :**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyX3V1aWQiLCJpYXQiOjE2MDk0NjAwMDAsImV4cCI6MTYwOTQ2MzYwMH0.signature"
}
```

**Durée de vie tokens :**
- **Access Token** : 15 minutes
- **Refresh Token** : 7 jours

---

### POST `/auth/logout/`
**Déconnexion et révocation du refresh token**

**Requête :**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyX3V1aWQiLCJpYXQiOjE2MDk0NTkyMDAsImV4cCI6MTYxMjA1MTIwMH0.signature"
}
```

**Réponse (200) :**
```json
{
  "message": "Déconnexion réussie",
  "token_revoked": true
}
```

---

### POST `/auth/change-password/`
**Changement de mot de passe (authentifié)**

**Requête :**
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewPassword456!",
  "new_password_confirm": "NewPassword456!"
}
```

**Réponse (200) :**
```json
{
  "message": "Mot de passe changé avec succès",
  "changed_at": "2024-01-01T15:30:00Z"
}
```

**Validation :**
- `current_password` : Doit correspondre au mot de passe actuel
- `new_password` : Minimum 8 caractères, 1 majuscule, 1 chiffre

---

### POST `/auth/password-reset/`
**Demande de réinitialisation de mot de passe**

**Requête :**
```json
{
  "email": "user@example.com"
}
```

**Réponse (200) :**
```json
{
  "message": "Si cet email existe, un lien de réinitialisation a été envoyé."
}
```

**Note :** Toujours retourne succès pour des raisons de sécurité.

---

### POST `/auth/password-reset/confirm/`
**Confirmation de réinitialisation avec token**

**Requête :**
```json
{
  "token": "reset-token-uuid-here",
  "new_password": "NewPassword123!",
  "new_password_confirm": "NewPassword123!"
}
```

**Réponse (200) :**
```json
{
  "message": "Mot de passe réinitialisé avec succès",
  "reset_at": "2024-01-01T15:30:00Z"
}
```

---

## 👤 **Gestion des Utilisateurs**

### GET `/users/profile/`
**Profil de l'utilisateur connecté**

**Headers :**
```http
Authorization: Bearer <access_token>
```

**Réponse (200) :**
```json
{
  "id": 1,
  "tracking_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "nom": "Doe",
  "prenom": "John",
  "full_name": "John Doe",
  "role": "CLIENT",
  "numero_telephone": "+33612345678",
  "pays": "France",
  "is_active": true,
  "is_staff": false,
  "is_superuser": false,
  "email_verified": true,
  "phone_verified": false,
  "date_joined": "2024-01-01T10:00:00Z",
  "last_login": "2024-01-01T15:30:00Z"
}
```

---

### GET `/users/profile/{user_id}/`
**Profil d'un utilisateur spécifique (admin seulement)**

**Réponse (200) :**
```json
{
  "id": 2,
  "tracking_id": "550e8400-e29b-41d4-a716-446655440001",
  "email": "other@example.com",
  "nom": "Smith",
  "prenom": "Jane",
  "full_name": "Jane Smith",
  "role": "MEMBER",
  "is_active": true,
  "date_joined": "2024-01-01T10:00:00Z",
  "last_login": "2024-01-01T14:20:00Z"
}
```

---

### PUT `/users/profile/`
**Mise à jour du profil utilisateur**

**Requête :**
```json
{
  "nom": "Doe-Updated",
  "prenom": "John-Updated",
  "pays": "Belgique",
  "numero_telephone": "+32212345678"
}
```

**Réponse (200) :**
```json
{
  "id": 1,
  "tracking_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "nom": "Doe-Updated",
  "prenom": "John-Updated",
  "full_name": "John-Updated Doe-Updated",
  "pays": "Belgique",
  "numero_telephone": "+32212345678",
  "updated_at": "2024-01-01T16:00:00Z"
}
```

---

### GET `/users/search/`
**Recherche d'utilisateurs**

**Paramètres :**
- `q` (required) : Terme de recherche
- `limit` (optional) : Nombre de résultats (défaut: 10)
- `role` (optional) : Filtrer par rôle (CLIENT/MEMBER/ADMIN/OWNER)

**Requête :**
```
GET /api/v1/foundation/users/search?q=john&limit=5&role=CLIENT
```

**Réponse (200) :**
```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "tracking_id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "john.doe@example.com",
      "full_name": "John Doe",
      "role": "CLIENT",
      "is_active": true,
      "date_joined": "2024-01-01T10:00:00Z"
    }
  ]
}
```

---

### GET `/users/stats/`
**Statistiques des utilisateurs (admin)**

**Réponse (200) :**
```json
{
  "total_users": 1250,
  "active_users": 1180,
  "clients_count": 800,
  "organizations_count": 150,
  "verified_organizations_count": 120,
  "new_users_this_month": 85,
  "users_by_country": {
    "France": 450,
    "Belgique": 280,
    "Suisse": 220,
    "Canada": 180,
    "Autres": 120
  },
  "users_by_language": {
    "fr": 850,
    "en": 320,
    "nl": 80
  }
}
```

---

### POST `/users/{user_id}/deactivate/`
**Désactiver un utilisateur (admin)**

**Réponse (200) :**
```json
{
  "message": "Utilisateur désactivé avec succès",
  "user_id": 2,
  "deactivated_at": "2024-01-01T16:00:00Z",
  "deactivated_by": 1
}
```

---

### GET `/users/{user_id}/organizations/`
**Organisations d'un utilisateur**

**Réponse (200) :**
```json
{
  "user_id": 1,
  "organizations": [
    {
      "id": 1,
      "tracking_id": "org-uuid-here",
      "name": "Tech Company",
      "role": "OWNER",
      "status": "ACTIVE",
      "joined_at": "2024-01-01T10:00:00Z"
    },
    {
      "id": 2,
      "tracking_id": "org-uuid-2",
      "name": "Startup XYZ",
      "role": "MEMBER",
      "status": "ACTIVE",
      "joined_at": "2024-01-15T14:00:00Z"
    }
  ]
}
```

---

## 🏢 **Gestion des Organisations**

### GET `/organizations/`
**Lister les organisations de l'utilisateur**

**Réponse (200) :**
```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "tracking_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Tech Company",
      "description": "Entreprise de développement web",
      "type": "COMPANY",
      "status": "ACTIVE",
      "city": "Paris",
      "member_count": 5,
      "is_owner": true,
      "user_role": "OWNER",
      "created_at": "2024-01-01T10:00:00Z"
    },
    {
      "id": 2,
      "tracking_id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "Startup XYZ",
      "type": "STARTUP",
      "status": "ACTIVE",
      "city": "Lyon",
      "member_count": 3,
      "is_owner": false,
      "user_role": "MEMBER",
      "created_at": "2024-01-10T15:00:00Z"
    }
  ]
}
```

---

### POST `/organizations/`
**Créer une nouvelle organisation**

**Requête :**
```json
{
  "name": "Ma Nouvelle Entreprise",
  "description": "Description de l'entreprise",
  "type": "COMPANY"
}
```

**Réponse (201) :**
```json
{
  "id": 3,
  "tracking_id": "770e8400-e29b-41d4-a716-446655440002",
  "name": "Ma Nouvelle Entreprise",
  "description": "Description de l'entreprise",
  "type": "COMPANY",
  "status": "ACTIVE",
  "owner": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe"
  },
  "member_count": 1,
  "max_members": 10,
  "created_at": "2024-01-01T17:00:00Z"
}
```

**Types d'organisation :**
- `COMPANY` : Entreprise classique
- `STARTUP` : Startup
- `AGENCY` : Agence digitale
- `FREELANCE` : Freelance
- `NON_PROFIT` : Organisation à but non lucratif

---

### GET `/organizations/{org_id}/`
**Détails d'une organisation**

**Réponse (200) :**
```json
{
  "id": 1,
  "tracking_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Tech Company",
  "description": "Entreprise de développement web",
  "type": "COMPANY",
  "status": "ACTIVE",
  "city": "Paris",
  "member_count": 5,
  "max_members": 10,
  "is_owner": true,
  "user_role": "OWNER",
  "owner": {
    "id": 1,
    "tracking_id": "user-uuid",
    "email": "user@example.com",
    "full_name": "John Doe"
  },
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T15:30:00Z"
}
```

---

### PUT `/organizations/{org_id}/`
**Mettre à jour une organisation (owner/admin)**

**Requête :**
```json
{
  "name": "Tech Company Updated",
  "description": "Nouvelle description de l'entreprise"
}
```

**Réponse (200) :**
```json
{
  "id": 1,
  "tracking_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Tech Company Updated",
  "description": "Nouvelle description de l'entreprise",
  "updated_at": "2024-01-01T17:30:00Z"
}
```

---

### DELETE `/organizations/{org_id}/`
**Supprimer une organisation (owner)**

**Réponse (204) :** Aucun contenu

---

## 👥 **Gestion des Membres d'Organisation**

### GET `/organizations/{org_id}/members/`
**Lister les membres d'une organisation**

**Réponse (200) :**
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "user": {
        "id": 1,
        "tracking_id": "user-uuid-1",
        "email": "owner@company.com",
        "full_name": "John Doe",
        "role": "CLIENT"
      },
      "organization": {
        "id": 1,
        "tracking_id": "org-uuid",
        "name": "Tech Company"
      },
      "role": "OWNER",
      "status": "ACTIVE",
      "is_current_user": true,
      "joined_at": "2024-01-01T10:00:00Z",
      "created_at": "2024-01-01T10:00:00Z"
    },
    {
      "id": 2,
      "user": {
        "id": 2,
        "tracking_id": "user-uuid-2",
        "email": "member@company.com",
        "full_name": "Jane Smith",
        "role": "MEMBER"
      },
      "role": "ADMIN",
      "status": "ACTIVE",
      "is_current_user": false,
      "joined_at": "2024-01-02T09:00:00Z"
    }
  ]
}
```

**Rôles de membre :**
- `OWNER` : Propriétaire (tous les droits)
- `ADMIN` : Administrateur (gestion sauf suppression)
- `MEMBER` : Membre (droits limités)
- `VIEWER` : Lecteur (lecture seule)

---

### POST `/organizations/{org_id}/members/`
**Ajouter un membre à une organisation**

**Requête :**
```json
{
  "user_email": "newmember@example.com",
  "role": "MEMBER"
}
```

**Réponse (201) :**
```json
{
  "id": 4,
  "user": {
    "id": 3,
    "tracking_id": "user-uuid-3",
    "email": "newmember@example.com",
    "full_name": "Bob Wilson"
  },
  "role": "MEMBER",
  "status": "PENDING",
  "invitation_sent": true,
  "created_at": "2024-01-01T18:00:00Z"
}
```

---

### PUT `/organizations/{org_id}/members/{member_id}/`
**Mettre à jour le rôle d'un membre**

**Requête :**
```json
{
  "role": "ADMIN"
}
```

**Réponse (200) :**
```json
{
  "id": 2,
  "role": "ADMIN",
  "updated_at": "2024-01-01T18:30:00Z",
  "updated_by": {
    "id": 1,
    "email": "owner@company.com"
  }
}
```

---

### DELETE `/organizations/{org_id}/members/{member_id}/`
**Retirer un membre de l'organisation**

**Réponse (204) :** Aucun contenu

---

### POST `/organizations/{org_id}/transfer-ownership/`
**Transférer la propriété de l'organisation**

**Requête :**
```json
{
  "new_owner_id": 2,
  "confirmation_text": "TRANSFER Tech Company"
}
```

**Réponse (200) :**
```json
{
  "message": "Propriété transférée avec succès",
  "previous_owner": {
    "id": 1,
    "email": "oldowner@company.com"
  },
  "new_owner": {
    "id": 2,
    "email": "newowner@company.com"
  },
  "transferred_at": "2024-01-01T19:00:00Z"
}
```

---

### POST `/organizations/{org_id}/leave/`
**Quitter une organisation**

**Réponse (200) :**
```json
{
  "message": "Vous avez quitté l'organisation",
  "organization": "Tech Company",
  "left_at": "2024-01-01T19:30:00Z"
}
```

---

### GET `/organizations/{org_id}/stats/`
**Statistiques d'une organisation**

**Réponse (200) :**
```json
{
  "organization_id": 1,
  "total_members": 5,
  "active_members": 4,
  "pending_invitations": 1,
  "members_by_role": {
    "OWNER": 1,
    "ADMIN": 1,
    "MEMBER": 2,
    "VIEWER": 1
  },
  "recent_activity_count": 25,
  "storage_used_mb": 125.5,
  "api_calls_this_month": 15420,
  "projects_count": 8,
  "active_projects": 6
}
```

---

## 💳 **Gestion des Abonnements**

### GET `/subscriptions/`
**Lister les abonnements de l'utilisateur**

**Réponse (200) :**
```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "tracking_id": "sub-uuid-here",
      "organization": {
        "id": 1,
        "name": "Tech Company"
      },
      "plan": {
        "id": 2,
        "name": "Professional",
        "price": 99.99,
        "currency": "EUR",
        "billing_interval": "monthly"
      },
      "status": "ACTIVE",
      "current_period_start": "2024-01-01T00:00:00Z",
      "current_period_end": "2024-02-01T00:00:00Z",
      "created_at": "2024-01-01T10:00:00Z"
    }
  ]
}
```

---

### POST `/subscriptions/`
**Créer un nouvel abonnement**

**Requête :**
```json
{
  "organization_id": "org-uuid-here",
  "plan_id": 2,
  "payment_method_id": "pm-uuid-here"
}
```

**Réponse (201) :**
```json
{
  "id": 2,
  "tracking_id": "sub-uuid-new",
  "status": "ACTIVE",
  "trial_period": {
    "enabled": true,
    "ends_at": "2024-01-15T00:00:00Z"
  },
  "created_at": "2024-01-01T20:00:00Z"
}
```

---

### GET `/subscription-plans/`
**Lister les plans d'abonnement disponibles**

**Réponse (200) :**
```json
{
  "count": 4,
  "results": [
    {
      "id": 1,
      "name": "Starter",
      "description": "Pour petites équipes",
      "price": 0.00,
      "currency": "EUR",
      "billing_interval": "monthly",
      "features": [
        "5 projets",
        "3 utilisateurs",
        "1GB stockage",
        "Support communautaire"
      ],
      "limits": {
        "max_projects": 5,
        "max_users": 3,
        "max_storage_gb": 1
      }
    },
    {
      "id": 2,
      "name": "Professional",
      "description": "Pour entreprises en croissance",
      "price": 99.99,
      "currency": "EUR",
      "billing_interval": "monthly",
      "features": [
        "Projets illimités",
        "50 utilisateurs",
        "50GB stockage",
        "Support prioritaire",
        "Analytics avancés"
      ],
      "limits": {
        "max_projects": -1,
        "max_users": 50,
        "max_storage_gb": 50
      }
    }
  ]
}
```

---

### GET `/payment-methods/`
**Lister les moyens de paiement**

**Réponse (200) :**
```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "tracking_id": "pm-uuid-here",
      "type": "credit_card",
      "brand": "visa",
      "last4": "4242",
      "expiry_month": 12,
      "expiry_year": 2025,
      "is_default": true,
      "created_at": "2024-01-01T10:00:00Z"
    },
    {
      "id": 2,
      "tracking_id": "pm-uuid-2",
      "type": "sepa_debit",
      "last4": "3000",
      "is_default": false,
      "created_at": "2024-01-10T15:00:00Z"
    }
  ]
}
```

---

## 📊 **Codes d'Erreur et Status**

### Codes HTTP Communs
| Code | Signification | Contexte |
|------|---------------|----------|
| `200` | OK | Opération réussie |
| `201` | Created | Ressource créée |
| `204` | No Content | Ressource supprimée |
| `400` | Bad Request | Données invalides |
| `401` | Unauthorized | Non authentifié |
| `403` | Forbidden | Permissions insuffisantes |
| `404` | Not Found | Ressource introuvable |
| `409` | Conflict | Conflit de données |
| `422` | Unprocessable Entity | Validation échouée |
| `429` | Too Many Requests | Rate limit dépassé |
| `500` | Internal Error | Erreur serveur |

### Codes d'Erreur Spécifiques
| Code | Message | Cause |
|------|---------|-------|
| `AUTH_001` | "Email ou mot de passe requis" | Login incomplet |
| `AUTH_002` | "Identifiants incorrects" | Login échoué |
| `AUTH_003` | "Compte désactivé" | Utilisateur banni |
| `AUTH_004` | "Token invalide ou expiré" | JWT expiré |
| `USER_001` | "Email déjà utilisé" | Inscription duplicate |
| `USER_002` | "Mot de passe trop faible" | Validation password |
| `ORG_001` | "Nom d'organisation requis" | Création org invalide |
| `ORG_002` | "Vous n'êtes pas propriétaire" | Permission refusée |
| `SUB_001` | "Plan d'abonnement inexistant" | Souscription invalide |

---

## 🔄 **Exemples d'Intégration**

### Python Client
```python
import requests
from typing import Dict, Any

class FoundationClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.access_token = None
        self.refresh_token = None
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Connexion utilisateur"""
        response = requests.post(
            f"{self.base_url}/api/v1/foundation/auth/login/",
            json={"email": email, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access']
            self.refresh_token = data['refresh']
            return data
        else:
            raise Exception(f"Login failed: {response.json()}")
    
    def get_profile(self) -> Dict[str, Any]:
        """Récupérer le profil utilisateur"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(
            f"{self.base_url}/api/v1/foundation/users/profile/",
            headers=headers
        )
        return response.json()
    
    def create_organization(self, name: str, description: str, org_type: str) -> Dict[str, Any]:
        """Créer une organisation"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        data = {
            "name": name,
            "description": description,
            "type": org_type
        }
        response = requests.post(
            f"{self.base_url}/api/v1/foundation/organizations/",
            json=data,
            headers=headers
        )
        return response.json()

# Utilisation
client = FoundationClient("https://api.nocode-platform.com")
user_data = client.login("user@example.com", "password")
profile = client.get_profile()
org = client.create_organization("Ma Company", "Description", "COMPANY")
```

### JavaScript Client
```javascript
class FoundationAPI {
    constructor(baseURL) {
        this.baseURL = baseURL;
        this.accessToken = null;
        this.refreshToken = null;
    }

    async login(email, password) {
        const response = await fetch(`${this.baseURL}/api/v1/foundation/auth/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        if (response.ok) {
            const data = await response.json();
            this.accessToken = data.access;
            this.refreshToken = data.refresh;
            return data;
        } else {
            throw new Error('Login failed');
        }
    }

    async getProfile() {
        const response = await fetch(`${this.baseURL}/api/v1/foundation/users/profile/`, {
            headers: { 'Authorization': `Bearer ${this.accessToken}` }
        });
        return response.json();
    }

    async createOrganization(name, description, type) {
        const response = await fetch(`${this.baseURL}/api/v1/foundation/organizations/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.accessToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, description, type })
        });
        return response.json();
    }
}

// Utilisation
const api = new FoundationAPI('https://api.nocode-platform.com');
await api.login('user@example.com', 'password');
const profile = await api.getProfile();
const org = await api.createOrganization('Ma Company', 'Description', 'COMPANY');
```

---

## 🧪 **Tests et Débogage**

### Tests Endpoints Clés
```bash
# Login
curl -X POST http://localhost:8000/api/v1/foundation/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}'

# Register
curl -X POST http://localhost:8000/api/v1/foundation/auth/register/client/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Password123!","password_confirm":"Password123!","nom":"Test","prenom":"User"}'

# Get Profile (remplacer token)
curl -X GET http://localhost:8000/api/v1/foundation/users/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Create Organization
curl -X POST http://localhost:8000/api/v1/foundation/organizations/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Org","description":"Test description","type":"COMPANY"}'
```

### Monitoring et Logs
```python
# Logs d'authentification
logger.info(f"User login successful", extra={
    'user_id': user.id,
    'email': user.email,
    'ip_address': request.META.get('REMOTE_ADDR'),
    'timestamp': timezone.now()
})

# Logs d'organisation
logger.info(f"Organization created", extra={
    'org_id': org.id,
    'owner_id': request.user.id,
    'org_type': org.type,
    'timestamp': timezone.now()
})
```

---

*Documentation Foundation API - Version 1.0*
