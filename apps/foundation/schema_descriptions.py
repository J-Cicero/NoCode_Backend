"""
Descriptions détaillées pour la documentation Swagger/OpenAPI
Module: Foundation (Authentification, Organisations, Utilisateurs)
"""

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes


# ============================================================================
# 🔐 AUTHENTIFICATION - Descriptions
# ============================================================================

AUTH_REGISTER_OWNER = {
    "summary": "🏢 Inscription Propriétaire (Owner)",
    "description": """
    **Crée un nouveau propriétaire avec son organisation.**
    
    ## 🎯 Cas d'usage :
    - Première inscription sur la plateforme
    - Crée automatiquement une organisation
    - L'utilisateur devient OWNER de cette organisation
    
    ## 📥 Données requises :
    - **email** : Adresse email unique
    - **password** : Minimum 8 caractères
    - **first_name** : Prénom
    - **last_name** : Nom de famille
    - **organization_name** : Nom de l'organisation
    
    ## 📤 Réponse :
    - Utilisateur créé avec son profil
    - Organisation créée et liée
    - Email de bienvenue envoyé
    - Tokens JWT (access + refresh)
    
    ## 🔒 Sécurité :
    - Pas d'authentification requise (endpoint public)
    - Email de vérification envoyé
    - Password hashé avec bcrypt
    
    ## 💡 Exemple frontend :
    ```javascript
    const response = await fetch('/api/v1/auth/register/owner/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            email: 'boss@entreprise.com',
            password: 'MonMotDePasse123!',
            first_name: 'Jean',
            last_name: 'Dupont',
            organization_name: 'Mon Entreprise'
        })
    });
    const data = await response.json();
    localStorage.setItem('access_token', data.tokens.access);
    localStorage.setItem('refresh_token', data.tokens.refresh);
    ```
    """,
    "tags": ["🔐 Authentification"],
    "examples": [
        OpenApiExample(
            name="Inscription Owner valide",
            value={
                "email": "boss@entreprise.com",
                "password": "MonMotDePasse123!",
                "first_name": "Jean",
                "last_name": "Dupont",
                "organization_name": "Mon Entreprise"
            },
            request_only=True
        ),
        OpenApiExample(
            name="Réponse succès",
            value={
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "boss@entreprise.com",
                    "first_name": "Jean",
                    "last_name": "Dupont",
                    "role": "OWNER",
                    "tracking_id": "trk_abc123xyz"
                },
                "organization": {
                    "id": "org_987654321",
                    "name": "Mon Entreprise",
                    "tracking_id": "org_abc123"
                },
                "tokens": {
                    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                }
            },
            response_only=True,
            status_codes=['201']
        )
    ]
}

AUTH_REGISTER_CLIENT = {
    "summary": "👤 Inscription Client/Membre",
    "description": """
    **Crée un nouveau client rattaché à une organisation existante.**
    
    ## 🎯 Cas d'usage :
    - Invitation par un OWNER
    - Rejoindre une organisation existante
    - Rôle CLIENT par défaut
    
    ## 📥 Données requises :
    - **email** : Adresse email unique
    - **password** : Minimum 8 caractères
    - **first_name** : Prénom
    - **last_name** : Nom de famille
    - **organization_id** : UUID de l'organisation (optionnel si invitation)
    
    ## 📤 Réponse :
    - Utilisateur créé avec rôle CLIENT
    - Lié à l'organisation
    - Email de bienvenue envoyé
    - Tokens JWT générés
    
    ## 🔒 Permissions :
    - Endpoint public
    - Nécessite une invitation valide OU organization_id
    
    ## 💡 Workflow typique :
    1. Owner envoie une invitation
    2. Client reçoit un email avec lien
    3. Client s'inscrit via ce endpoint
    4. Accès immédiat aux projets de l'organisation
    """,
    "tags": ["🔐 Authentification"]
}

AUTH_LOGIN = {
    "summary": "🔑 Connexion",
    "description": """
    **Authentifie un utilisateur et retourne des tokens JWT.**
    
    ## 🎯 Fonctionnement :
    1. Vérification email + password
    2. Génération de tokens JWT
    3. Retour des informations utilisateur
    
    ## 📥 Données requises :
    - **email** : Adresse email de l'utilisateur
    - **password** : Mot de passe
    
    ## 📤 Réponse :
    - **access_token** : JWT valide 15 minutes (à mettre dans Authorization: Bearer)
    - **refresh_token** : JWT valide 7 jours (pour renouveler l'access_token)
    - **user** : Profil utilisateur complet
    - **organization** : Organisation rattachée
    
    ## 🔐 Tokens JWT :
    - **Access Token** : Court terme (15 min) pour les requêtes API
    - **Refresh Token** : Long terme (7 jours) pour obtenir de nouveaux access tokens
    
    ## 💡 Exemple frontend :
    ```javascript
    const login = async (email, password) => {
        const response = await fetch('/api/v1/auth/login/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await response.json();
        
        // Stocker les tokens
        localStorage.setItem('access_token', data.tokens.access);
        localStorage.setItem('refresh_token', data.tokens.refresh);
        
        // Utiliser dans les requêtes
        fetch('/api/v1/projects/', {
            headers: {
                'Authorization': `Bearer ${data.tokens.access}`
            }
        });
    };
    ```
    
    ## ⚠️ Erreurs possibles :
    - **400** : Email ou password invalide
    - **401** : Compte non vérifié
    - **403** : Compte désactivé
    """,
    "tags": ["🔐 Authentification"]
}

AUTH_LOGOUT = {
    "summary": "🚪 Déconnexion",
    "description": """
    **Déconnecte un utilisateur en invalidant son refresh token.**
    
    ## 🎯 Fonctionnement :
    1. Envoyer le refresh_token
    2. Le système l'ajoute à la blacklist
    3. L'utilisateur ne peut plus générer de nouveaux access tokens
    
    ## 📥 Données requises :
    - **refresh_token** : Le token JWT obtenu à la connexion
    
    ## 🔐 Sécurité :
    - Authentification requise (Bearer token dans headers)
    - Le refresh_token est blacklisté définitivement
    - Empêche la réutilisation des tokens
    
    ## 💡 Bonnes pratiques frontend :
    ```javascript
    const logout = async () => {
        const refreshToken = localStorage.getItem('refresh_token');
        const accessToken = localStorage.getItem('access_token');
        
        await fetch('/api/v1/auth/logout/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ refresh_token: refreshToken })
        });
        
        // Nettoyer le stockage local
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        // Rediriger vers login
        window.location.href = '/login';
    };
    ```
    """,
    "tags": ["🔐 Authentification"]
}

AUTH_REFRESH_TOKEN = {
    "summary": "🔄 Renouveler l'Access Token",
    "description": """
    **Génère un nouveau access token avec le refresh token.**
    
    ## 🎯 Pourquoi ?
    Les access tokens expirent après 15 minutes pour la sécurité.
    Au lieu de reconnecter l'utilisateur, on génère un nouveau access token.
    
    ## 📥 Données requises :
    - **refresh** : Le refresh token obtenu à la connexion
    
    ## 📤 Réponse :
    - **access** : Nouveau access token valide 15 minutes
    
    ## 💡 Implémentation automatique :
    ```javascript
    // Intercepteur Axios pour renouveler automatiquement
    axios.interceptors.response.use(
        response => response,
        async error => {
            if (error.response?.status === 401) {
                const refreshToken = localStorage.getItem('refresh_token');
                
                const response = await axios.post('/api/v1/auth/token/refresh/', {
                    refresh: refreshToken
                });
                
                localStorage.setItem('access_token', response.data.access);
                
                // Rejouer la requête originale
                error.config.headers['Authorization'] = `Bearer ${response.data.access}`;
                return axios(error.config);
            }
            return Promise.reject(error);
        }
    );
    ```
    
    ## ⏰ Quand appeler ?
    - Quand une requête retourne 401 Unauthorized
    - Avant que l'access token expire (proactif)
    - Toutes les 10-12 minutes (recommandé)
    """,
    "tags": ["🔐 Authentification"]
}

AUTH_PASSWORD_CHANGE = {
    "summary": "🔒 Changer le mot de passe",
    "description": """
    **Permet à un utilisateur connecté de changer son mot de passe.**
    
    ## 🎯 Cas d'usage :
    - Utilisateur connecté veut changer son mot de passe
    - Depuis les paramètres du profil
    
    ## 📥 Données requises :
    - **old_password** : Mot de passe actuel (pour sécurité)
    - **new_password** : Nouveau mot de passe (min 8 caractères)
    
    ## 🔐 Sécurité :
    - Authentification requise (Bearer token)
    - Vérifie l'ancien mot de passe
    - Hash avec bcrypt
    - Invalidation de tous les anciens tokens (optionnel)
    
    ## 💡 Exemple frontend :
    ```javascript
    const changePassword = async (oldPassword, newPassword) => {
        const response = await fetch('/api/v1/auth/password/change/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                old_password: oldPassword,
                new_password: newPassword
            })
        });
        
        if (response.ok) {
            alert('Mot de passe changé avec succès');
        }
    };
    ```
    """,
    "tags": ["🔐 Authentification"]
}

AUTH_PASSWORD_RESET_REQUEST = {
    "summary": "📧 Demander réinitialisation mot de passe",
    "description": """
    **Envoie un email avec un lien de réinitialisation.**
    
    ## 🎯 Cas d'usage :
    - Utilisateur a oublié son mot de passe
    - Page "Mot de passe oublié ?"
    
    ## 📥 Données requises :
    - **email** : Adresse email du compte
    
    ## 📤 Processus :
    1. Vérification que l'email existe
    2. Génération d'un token unique
    3. Envoi d'un email avec lien de réinitialisation
    4. Lien valide 1 heure
    
    ## 🔒 Sécurité :
    - Endpoint public (pas d'authentification)
    - Ne révèle pas si l'email existe (pour éviter l'énumération)
    - Token à usage unique
    - Expiration après 1 heure
    
    ## 💡 Workflow complet :
    ```javascript
    // 1. Demande de réinitialisation
    await fetch('/api/v1/auth/password/reset/request/', {
        method: 'POST',
        body: JSON.stringify({ email: 'user@example.com' })
    });
    
    // 2. Utilisateur clique sur lien dans email
    // Lien: /reset-password?token=abc123xyz
    
    // 3. Confirmer nouveau mot de passe
    await fetch('/api/v1/auth/password/reset/confirm/', {
        method: 'POST',
        body: JSON.stringify({
            token: 'abc123xyz',
            new_password: 'NouveauMotDePasse123!'
        })
    });
    ```
    """,
    "tags": ["🔐 Authentification"]
}

AUTH_PASSWORD_RESET_CONFIRM = {
    "summary": "✅ Confirmer réinitialisation mot de passe",
    "description": """
    **Réinitialise le mot de passe avec le token reçu par email.**
    
    ## 🎯 Cas d'usage :
    - Utilisateur a cliqué sur le lien dans l'email
    - Saisie d'un nouveau mot de passe
    
    ## 📥 Données requises :
    - **token** : Token reçu par email (dans l'URL)
    - **new_password** : Nouveau mot de passe
    
    ## 🔐 Sécurité :
    - Token à usage unique (supprimé après utilisation)
    - Token expire après 1 heure
    - Nouveau password hashé avec bcrypt
    - Invalidation de tous les anciens tokens JWT
    
    ## ⚠️ Erreurs :
    - **400** : Token invalide ou expiré
    - **400** : Mot de passe trop faible
    """,
    "tags": ["🔐 Authentification"]
}

AUTH_EMAIL_VERIFICATION = {
    "summary": "✉️ Vérifier l'email",
    "description": """
    **Valide l'adresse email avec le token reçu.**
    
    ## 🎯 Cas d'usage :
    - Après inscription
    - Utilisateur clique sur lien dans email de bienvenue
    
    ## 📥 Données requises :
    - **token** : Token de vérification (dans l'URL)
    
    ## 📤 Réponse :
    - Compte activé
    - Email marqué comme vérifié
    - Utilisateur peut se connecter
    
    ## 💡 Workflow :
    ```javascript
    // 1. Récupérer token depuis URL
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    
    // 2. Vérifier l'email
    const response = await fetch('/api/v1/auth/email/verify/', {
        method: 'POST',
        body: JSON.stringify({ token })
    });
    
    // 3. Rediriger vers login
    if (response.ok) {
        window.location.href = '/login?verified=true';
    }
    ```
    """,
    "tags": ["🔐 Authentification"]
}


# ============================================================================
# 🏢 ORGANISATIONS - Descriptions
# ============================================================================

ORG_LIST_CREATE = {
    "summary": "🏢 Liste et création d'organisations",
    "description": """
    **Liste les organisations accessibles ou crée une nouvelle organisation.**
    
    ## 📋 GET - Lister les organisations
    
    ### Retourne :
    - Toutes les organisations où l'utilisateur est membre
    - Filtrage par rôle possible
    - Pagination automatique
    
    ### Filtres disponibles :
    - `?role=OWNER` : Seulement les orgs où je suis OWNER
    - `?role=ADMIN` : Seulement les orgs où je suis ADMIN
    - `?search=nom` : Recherche par nom
    
    ## ➕ POST - Créer une organisation
    
    ### Cas d'usage :
    - Utilisateur existant crée une nouvelle organisation
    - Devient automatiquement OWNER
    
    ### Données requises :
    - **name** : Nom de l'organisation
    - **description** : Description (optionnel)
    
    ### Résultat :
    - Organisation créée
    - Utilisateur devient OWNER
    - Plan gratuit attribué par défaut
    
    ## 💡 Exemple frontend :
    ```javascript
    // Lister mes organisations
    const orgs = await fetch('/api/v1/organizations/', {
        headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json());
    
    // Créer une nouvelle organisation
    const newOrg = await fetch('/api/v1/organizations/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: 'Ma Nouvelle Entreprise',
            description: 'Description de mon entreprise'
        })
    }).then(r => r.json());
    ```
    """,
    "tags": ["🏢 Organisations"]
}


# Vous pouvez ajouter plus de descriptions ici...
