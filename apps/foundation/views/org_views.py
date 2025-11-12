"""
Vues pour la gestion des organisations.
Expose les APIs pour les organisations, membres, invitations, etc.
"""
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from ..services.organization_service import OrganizationService
from ..serializers import (
    OrganizationCreateSerializer, OrganizationUpdateSerializer,
    OrganizationDetailSerializer, OrganizationListSerializer,
    OrganizationMemberSerializer,
    OrganizationTransferOwnershipSerializer, OrganizationStatsSerializer
)
from ..models import Organization, OrganizationMember


User = get_user_model()


class OrganizationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Liste les organisations de l'utilisateur."""
        org_service = OrganizationService(user=request.user)
        result = org_service.get_user_organizations()

        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        """Crée une nouvelle organisation."""
        serializer = OrganizationCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            org_service = OrganizationService(user=request.user)
            result = org_service.create_organization(serializer.validated_data)

            if result.success:
                return Response(result.data, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': result.error_message
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganizationDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id):
        """Récupère les détails d'une organisation."""
        org_service = OrganizationService(user=request.user)
        result = org_service.get_organization_details(org_id)
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, org_id):
        """Met à jour une organisation."""
        serializer = OrganizationUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            org_service = OrganizationService(user=request.user)
            result = org_service.update_organization(org_id, serializer.validated_data)
            
            if result.success:
                return Response(result.data, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': result.error_message
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, org_id):
        """Supprime une organisation."""
        org_service = OrganizationService(user=request.user)
        result = org_service.delete_organization(org_id)
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_400_BAD_REQUEST)


class OrganizationMembersView(APIView):
    """Vue pour les membres d'une organisation."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id):
        """Liste les membres d'une organisation."""
        org_service = OrganizationService(user=request.user)
        result = org_service.get_organization_members(org_id)
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_400_BAD_REQUEST)


class OrganizationMemberDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request, org_id, member_id):
        """Met à jour un membre d'organisation."""
        new_role = request.data.get('role')
        permissions = request.data.get('permissions', [])
        
        org_service = OrganizationService(user=request.user)
        result = org_service.update_member_role(org_id, member_id, new_role, permissions)
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, org_id, member_id):
        """Supprime un membre d'une organisation."""
        org_service = OrganizationService(user=request.user)
        result = org_service.remove_member(org_id, member_id)
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_400_BAD_REQUEST)


# OrganizationInvitationsView - SUPPRIMÉ (modèle OrganizationInvitation supprimé)
# OrganizationInvitationAcceptView - SUPPRIMÉ (modèle OrganizationInvitation supprimé)


class OrganizationTransferOwnershipView(APIView):
    """Vue pour le transfert de propriété d'organisation."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, org_id):
        """Transfère la propriété d'une organisation."""
        try:
            organization = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return Response({
                'error': 'Organisation introuvable'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = OrganizationTransferOwnershipSerializer(
            data=request.data,
            context={'organization': organization}
        )
        
        if serializer.is_valid():
            new_owner_id = serializer.validated_data['new_owner_id']
            
            org_service = OrganizationService(user=request.user, organization=organization)
            result = org_service.transfer_ownership(new_owner_id)
            
            if result.success:
                return Response(result.data, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': result.error_message
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganizationStatsView(APIView):
    """Vue pour les statistiques d'organisation."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id):
        """Récupère les statistiques d'une organisation."""
        try:
            organization = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return Response({
                'error': 'Organisation introuvable'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Vérifier les permissions
        try:
            member = OrganizationMember.objects.get(
                organization=organization,
                user=request.user,
                status='ACTIVE'
            )
            if member.role not in ['OWNER', 'MEMBER']:
                return Response({
                    'error': 'Permissions insuffisantes'
                }, status=status.HTTP_403_FORBIDDEN)
        except OrganizationMember.DoesNotExist:
            return Response({
                'error': 'Vous n\'êtes pas membre de cette organisation'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Calculer les statistiques
        stats_data = {
            'total_members': organization.members.filter(status='ACTIVE').count(),
            'active_members': organization.members.filter(status='ACTIVE').count(),
            'pending_invitations': organization.invitations.filter(status='PENDING').count(),
            'members_by_role': {},
            'recent_activity_count': 0,  # À implémenter avec le système d'audit
            'storage_used_mb': 0.0,  # À implémenter avec les projets
            'api_calls_this_month': 0,  # À implémenter avec les métriques
        }
        
        # Répartition par rôle
        from django.db.models import Count
        roles_count = organization.members.filter(status='ACTIVE').values('role').annotate(
            count=Count('id')
        )
        
        for role_data in roles_count:
            stats_data['members_by_role'][role_data['role']] = role_data['count']
        
        return Response(stats_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def leave_organization(request, org_id):
    """Quitte une organisation."""
    org_service = OrganizationService(user=request.user)
    result = org_service.leave_organization(org_id)
    
    if result.success:
        return Response(result.data, status=status.HTTP_200_OK)
    else:
        return Response({
            'error': result.error_message
        }, status=status.HTTP_400_BAD_REQUEST)


# resend_invitation - SUPPRIMÉ (modèle OrganizationInvitation supprimé)