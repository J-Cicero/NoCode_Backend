"""
Vues pour l'authentification et la gestion des comptes.
Expose les APIs pour login, register, password reset, etc.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model
from ..services.auth_service import AuthService
from ..serializers import (
    UserCreateSerializer, ClientCreateSerializer, EntrepriseCreateSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    PasswordChangeSerializer, EmailVerificationSerializer
)


User = get_user_model()


class LoginView(TokenObtainPairView):
    """Vue pour la connexion avec JWT."""
    
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({
                'error': 'Email et mot de passe requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Utiliser AuthService pour la connexion
        auth_service = AuthService()
        result = auth_service.login(email, password)
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_401_UNAUTHORIZED)


class RegisterClientView(APIView):
    """Vue pour l'inscription des clients (personnes physiques)."""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ClientCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            # Utiliser AuthService pour l'inscription
            auth_service = AuthService()
            result = auth_service.register_client(serializer.validated_data)
            
            if result.success:
                return Response(result.data, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': result.error_message
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterEntrepriseView(APIView):
    """Vue pour l'inscription des entreprises."""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = EntrepriseCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            # Utiliser AuthService pour l'inscription
            auth_service = AuthService()
            result = auth_service.register_entreprise(serializer.validated_data)
            
            if result.success:
                return Response(result.data, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': result.error_message
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Vue pour la déconnexion."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        
        if not refresh_token:
            return Response({
                'error': 'Refresh token requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Utiliser AuthService pour la déconnexion
        auth_service = AuthService(user=request.user)
        result = auth_service.logout(refresh_token)
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_400_BAD_REQUEST)


class RefreshTokenView(TokenRefreshView):
    """Vue pour le renouvellement des tokens JWT."""
    
    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response({
                'error': 'Refresh token requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Utiliser AuthService pour le renouvellement
        auth_service = AuthService()
        result = auth_service.refresh_token(refresh_token)
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_401_UNAUTHORIZED)


class PasswordChangeView(APIView):
    """Vue pour le changement de mot de passe."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Utiliser AuthService pour le changement de mot de passe
            auth_service = AuthService(user=request.user)
            result = auth_service.change_password(
                current_password=serializer.validated_data['current_password'],
                new_password=serializer.validated_data['new_password']
            )
            
            if result.success:
                return Response(result.data, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': result.error_message
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """Vue pour la demande de réinitialisation de mot de passe."""
    
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
    """Vue pour la confirmation de réinitialisation de mot de passe."""
    
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
                    'error': result.error_message
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailVerificationView(APIView):
    """Vue pour la vérification d'email."""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        
        if serializer.is_valid():
            token = serializer.validated_data['token']
            
            # Extraire l'ID utilisateur du token (implémentation simplifiée)
            # Dans une vraie implémentation, on décoderait le JWT
            try:
                # Ici on devrait décoder le token pour récupérer l'user_id
                # Pour l'exemple, on suppose que le token contient l'ID
                user_id = 1  # À remplacer par la vraie logique de décodage
                
                from ..services.user_service import UserService
                user_service = UserService()
                result = user_service.verify_email(user_id, token)
                
                if result.success:
                    return Response(result.data, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'error': result.error_message
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Exception:
                return Response({
                    'error': 'Token invalide'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """Récupère les informations de l'utilisateur connecté."""
    from ..services.user_service import UserService
    from ..serializers import UserProfileSerializer
    
    user_service = UserService(user=request.user)
    result = user_service.get_user_profile()
    
    if result.success:
        return Response(result.data, status=status.HTTP_200_OK)
    else:
        return Response({
            'error': result.error_message
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
