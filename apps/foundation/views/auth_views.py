
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from drf_spectacular.utils import extend_schema
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


class RegisterClientView(APIView):

    permission_classes = [AllowAny]
    
    # @extend_schema(request=UserCreateSerializer, responses={201: dict})
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




class LogoutView(APIView):

    permission_classes = [IsAuthenticated]
    
    @extend_schema(request=dict, responses={200: dict})
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
