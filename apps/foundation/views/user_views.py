
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from ..services.user_service import UserService
from ..serializers import (
    UserProfileSerializer, UserUpdateSerializer, UserStatsSerializer
)
from ..permissions.role_permissions import (
    CanAccessOwnDataOrAdmin, IsAdminApp
)


User = get_user_model()


class UserProfileView(APIView):
    """Vue pour le profil utilisateur avec tracking_id."""
    
    permission_classes = [IsAuthenticated, CanAccessOwnDataOrAdmin]
    
    def get(self, request, tracking_id=None):
        if tracking_id:
            user = get_object_or_404(User, tracking_id=tracking_id)
            self.check_object_permissions(request, user)
        else:
            user = request.user
            
        user_service = UserService(user=request.user)
        result = user_service.get_user_profile(user.id)
        
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
    def get(self, request):
        user_service = UserService(user=request.user)
        result = user_service.get_user_stats()
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_400_BAD_REQUEST)


class UserDeactivateView(APIView):    
    
    def post(self, request, user_id):
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
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id=None):
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
    user_service = UserService(user=request.user)
    result = user_service.get_user_organizations()
    
    if result.success:
        return Response(result.data, status=status.HTTP_200_OK)
    else:
        return Response({
            'error': result.error_message
        }, status=status.HTTP_400_BAD_REQUEST)
