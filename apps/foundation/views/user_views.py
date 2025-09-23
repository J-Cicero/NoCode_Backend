"""
Vues pour la gestion des utilisateurs.
Expose les APIs pour les profils utilisateur, recherche, statistiques, etc.
"""
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from ..services.user_service import UserService
from ..serializers import (
    UserProfileSerializer, UserUpdateSerializer, UserStatsSerializer,
    ClientUpdateSerializer, EntrepriseUpdateSerializer
)


User = get_user_model()


class UserProfileView(APIView):
    """Vue pour le profil utilisateur."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id=None):
        """Récupère le profil d'un utilisateur."""
        user_service = UserService(user=request.user)
        result = user_service.get_user_profile(user_id)
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, user_id=None):
        """Met à jour le profil d'un utilisateur."""
        target_user_id = user_id or request.user.id
        
        user_service = UserService(user=request.user)
        result = user_service.update_user_profile(target_user_id, request.data)
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_400_BAD_REQUEST)


class UserSearchView(APIView):
    """Vue pour la recherche d'utilisateurs."""
    
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Recherche des utilisateurs."""
        query = request.query_params.get('q', '')
        user_type = request.query_params.get('type')
        limit = int(request.query_params.get('limit', 20))
        
        user_service = UserService(user=request.user)
        result = user_service.search_users(query, user_type, limit)
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_400_BAD_REQUEST)


class UserStatsView(APIView):
    """Vue pour les statistiques des utilisateurs."""
    
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Récupère les statistiques des utilisateurs."""
        user_service = UserService(user=request.user)
        result = user_service.get_user_stats()
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_400_BAD_REQUEST)


class UserDeactivateView(APIView):
    """Vue pour la désactivation d'utilisateurs."""
    
    permission_classes = [IsAdminUser]
    
    def post(self, request, user_id):
        """Désactive un utilisateur."""
        reason = request.data.get('reason', '')
        
        user_service = UserService(user=request.user)
        result = user_service.deactivate_user(user_id, reason)
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_400_BAD_REQUEST)


class UserOrganizationsView(APIView):
    """Vue pour les organisations d'un utilisateur."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id=None):
        """Récupère les organisations d'un utilisateur."""
        user_service = UserService(user=request.user)
        result = user_service.get_user_organizations(user_id)
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_profile(request):
    """Récupère le profil de l'utilisateur connecté."""
    user_service = UserService(user=request.user)
    result = user_service.get_user_profile()
    
    if result.success:
        return Response(result.data, status=status.HTTP_200_OK)
    else:
        return Response({
            'error': result.error_message
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_current_user_profile(request):
    """Met à jour le profil de l'utilisateur connecté."""
    user_service = UserService(user=request.user)
    result = user_service.update_user_profile(request.user.id, request.data)
    
    if result.success:
        return Response(result.data, status=status.HTTP_200_OK)
    else:
        return Response({
            'error': result.error_message
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_organizations(request):
    """Récupère les organisations de l'utilisateur connecté."""
    user_service = UserService(user=request.user)
    result = user_service.get_user_organizations()
    
    if result.success:
        return Response(result.data, status=status.HTTP_200_OK)
    else:
        return Response({
            'error': result.error_message
        }, status=status.HTTP_400_BAD_REQUEST)
