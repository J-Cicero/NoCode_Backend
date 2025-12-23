
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model
from ..services.auth_service import AuthService
from ..services.user_service import UserService
from ..serializers import (
     UserCreateSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    PasswordChangeSerializer, EmailVerificationSerializer
)

User = get_user_model()

@extend_schema(
    summary="🔑 Connexion utilisateur",
    description="""
    **Authentifie un utilisateur et génère des tokens JWT.**
    
    ## 🎯 Fonctionnement :
    1. Envoyer email + mot de passe
    2. Le système vérifie les identifiants
    3. Si valide : retourne un access_token et refresh_token
    
    ## 📊 Tokens retournés :
    - **access_token** : Token d'accès (courte durée, ~1h)
      - À utiliser dans l'en-tête : `Authorization: Bearer <access_token>`
      - Permet d'accéder aux endpoints protégés
    
    - **refresh_token** : Token de rafraîchissement (longue durée, ~7j)
      - Permet d'obtenir un nouveau access_token sans re-login
      - À conserver en sécurité côté client
    
    ## 🔐 Informations retournées :
    - Tokens JWT
    - Informations utilisateur (email, nom, prénom)
    - Liste des organisations de l'utilisateur
    - Type d'utilisateur
    
    ## 💡 Exemple de requête :
    ```json
    POST /api/v1/foundation/auth/login/
    {
        "email": "client@example.com",
        "password": "MonMotDePasse123!"
    }
    ```
    
    ## 📊 Exemple de réponse :
    ```json
    {
        "tokens": {
            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        },
        "user": {
            "email": "client@example.com",
            "nom": "Dupont",
            "prenom": "Jean",
            "organizations": [...]
        }
    }
    ```
    
    ## ⚠️ Erreurs possibles :
    - 400 : Email ou mot de passe manquant
    - 401 : Identifiants incorrects
    """,
    tags=["🔐 Authentification"],
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "format": "email", "example": "client@example.com"},
                "password": {"type": "string", "format": "password", "example": "MonMotDePasse123!"}
            },
            "required": ["email", "password"]
        }
    },
    examples=[
        OpenApiExample(
            "Connexion Client",
            value={
                "email": "client@example.com",
                "password": "MonMotDePasse123!"
            },
            request_only=True
        )
    ]
)
class LoginView(TokenObtainPairView):

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({
                'error': 'Email et mot de passe requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        auth_service = AuthService()
        result = auth_service.login(email, password)
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.errors[0] if result.errors else 'Erreur inconnue'
            }, status=status.HTTP_401_UNAUTHORIZED)


@extend_schema(
    summary="📝 Inscription d'un nouveau client",
    description="""
    **Crée un nouveau compte client individuel sur la plateforme NoCode.**
    
    ## 🎯 Qu'est-ce qu'un Client ?
    Un **Client** est un utilisateur individuel qui :
    - ✅ Peut créer ses propres projets NoCode
    - ✅ A une organisation personnelle automatiquement créée
    - ✅ Peut rejoindre des organisations d'entreprise plus tard
    - ✅ Travaille de manière indépendante (freelance/solo)
    
    ## 📝 Informations requises :
    ```json
    {
        "email": "nouveau@example.com",
        "password": "MotDePasse123!",
        "password_confirm": "MotDePasse123!",
        "nom": "Dupont",
        "prenom": "Jean",
        "pays": "France",
        "numero_telephone": "+33612345678"
    }
    ```
    
    ## ⚙️ Ce qui est créé automatiquement :
    - ✅ Compte utilisateur
    - ✅ Organisation personnelle (type PERSONAL)
    - ✅ Tokens JWT (access + refresh)
    - ✅ Email de vérification envoyé (si activé)
    
    ## 🔐 Sécurité :
    - Mot de passe hashé avec bcrypt
    - Email unique requis
    - Validation des données
    
    ## 📊 Réponse :
    - Détails de l'utilisateur créé
    - Tokens JWT pour connexion immédiate
    - Informations de l'organisation personnelle
    
    ## ⚠️ Validation du mot de passe :
    - Minimum 8 caractères
    - Au moins 1 majuscule
    - Au moins 1 chiffre
    - Au moins 1 caractère spécial
    
    ## 💡 Après l'inscription :
    1. Utilisez les tokens pour accéder aux endpoints
    2. Créez votre premier projet NoCode
    3. Commencez à construire vos applications
    
    ## ⚠️ Erreurs possibles :
    - 400 : Email déjà utilisé
    - 400 : Mot de passe trop faible
    - 400 : Champs manquants ou invalides
    """,
    tags=["🔐 Authentification"],
    request=UserCreateSerializer,
    examples=[
        OpenApiExample(
            "Inscription Complète",
            value={
                "email": "nouveau.client@example.com",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
                "nom": "Martin",
                "prenom": "Sophie",
                "pays": "France",
                "numero_telephone": "+33698765432"
            },
            request_only=True
        )
    ]
)
class RegisterClientView(APIView):

    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            auth_service = AuthService()
            result = auth_service.register_client(serializer.validated_data)
            
            if result.success:
                return Response(result.data, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': result.errors[0] if result.errors else 'Erreur inconnue'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@extend_schema(
    summary="🚪 Déconnexion utilisateur",
    description="""
    **Déconnecte un utilisateur en invalidant son refresh token.**
    
    ## 🎯 Fonctionnement :
    1. Envoyer le refresh_token
    2. Le système l'invalide (blacklist)
    3. L'utilisateur ne peut plus générer de nouveaux access tokens
    
    ## 📝 Requête :
    ```json
    {
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
    
    ## 🔐 Sécurité :
    - Authentification requise (Bearer token)
    - Le refresh_token est ajouté à une blacklist
    - Empêche la réutilisation des tokens
    
    ## 💡 Bonnes pratiques :
    - Supprimer les tokens stockés côté client
    - Rediriger vers la page de connexion
    """,
    tags=["🔐 Authentification"],
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "refresh_token": {"type": "string", "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
            },
            "required": ["refresh_token"]
        }
    }
)
class LogoutView(APIView):

    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        
        if not refresh_token:
            return Response({
                'error': 'Refresh token requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        auth_service = AuthService(user=request.user)
        result = auth_service.logout(refresh_token)
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.errors[0] if result.errors else 'Erreur inconnue'
            }, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    summary="🔄 Rafraîchir le token d'accès",
    description="""
    **Génère un nouveau access token à partir d'un refresh token valide.**
    
    ## 🎯 Pourquoi rafraîchir ?
    Les access tokens ont une durée de vie courte (~1h). Plutôt que de redemander à l'utilisateur
    de se reconnecter, utilisez le refresh token pour obtenir un nouveau access token.
    
    ## 📝 Requête :
    ```json
    {
        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
    
    ## 📊 Réponse :
    ```json
    {
        "access": "nouveau_access_token..."
    }
    ```
    
    ## 💡 Utilisation :
    1. Détecter l'expiration du access token (erreur 401)
    2. Appeler cet endpoint avec le refresh token
    3. Obtenir un nouveau access token
    4. Continuer à utiliser l'API
    
    ## ⚠️ Erreurs possibles :
    - 400 : Refresh token manquant
    - 401 : Refresh token invalide ou expiré
    """,
    tags=["🔐 Authentification"],
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "refresh": {"type": "string", "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
            },
            "required": ["refresh"]
        }
    }
)
class RefreshTokenView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response({
                'error': 'Refresh token requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        auth_service = AuthService()
        result = auth_service.refresh_token(refresh_token)
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.errors[0] if result.errors else 'Erreur inconnue'
            }, status=status.HTTP_401_UNAUTHORIZED)


class PasswordChangeView(APIView):
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            auth_service = AuthService(user=request.user)
            result = auth_service.change_password(
                current_password=serializer.validated_data['current_password'],
                new_password=serializer.validated_data['new_password']
            )
            
            if result.success:
                return Response(result.data, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': result.errors[0] if result.errors else 'Erreur inconnue'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            # Utiliser AuthService pour la demande de réinitialisation
            auth_service = AuthService()
            result = auth_service.request_password_reset(
                email=serializer.validated_data['email']
            )
            
            # Toujours retourner succès pour des raisons de sécurité
            return Response({
                'message': 'Si cet email existe, un lien de réinitialisation a été envoyé.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):

    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        
        if serializer.is_valid():
            # Utiliser AuthService pour la réinitialisation
            auth_service = AuthService()
            result = auth_service.reset_password(
                token=serializer.validated_data['token'],
                new_password=serializer.validated_data['new_password']
            )
            
            if result.success:
                return Response(result.data, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': result.errors[0] if result.errors else 'Erreur inconnue'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailVerificationView(APIView):
    """Vue pour la vérification d'email."""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        
        if serializer.is_valid():
            token = serializer.validated_data['token']
            
            # Utiliser AuthService pour vérifier l'email avec le token
            try:
                auth_service = AuthService()
                result = auth_service.verify_email(token)
                
                if result.success:
                    return Response(result.data, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'error': result.errors[0] if result.errors else 'Erreur inconnue'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Exception:
                return Response({
                    'error': 'Token invalide'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="👤 Récupérer mon profil",
    description="""
    **Récupère les informations complètes de l'utilisateur actuellement connecté.**
    
    ## 📊 Informations retournées :
    - Données personnelles (email, nom, prénom, etc.)
    - Liste des organisations
    - Rôles dans chaque organisation
    - Date d'inscription
    - Statut de vérification email
    
    ## 🔐 Authentification :
    ```
    GET /api/v1/foundation/auth/me/
    Authorization: Bearer <access_token>
    ```
    
    ## 💡 Cas d'utilisation :
    - Afficher le profil utilisateur
    - Vérifier les permissions
    - Récupérer les organisations disponibles
    - Initialiser l'interface utilisateur
    """,
    tags=["🔐 Authentification"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """Récupère les informations de l'utilisateur connecté."""

    user_service = UserService(user=request.user)
    result = user_service.get_user_profile()
    
    if result.success:
        return Response(result.data, status=status.HTTP_200_OK)
    else:
        return Response({
            'error': result.errors[0] if result.errors else 'Erreur inconnue'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resend_verification_email(request):
    """Renvoie l'email de vérification."""
    auth_service = AuthService(user=request.user)
    result = auth_service.send_verification_email(request.user.email)
    
    return Response({
        'message': 'Email de vérification envoyé'
    }, status=status.HTTP_200_OK)
