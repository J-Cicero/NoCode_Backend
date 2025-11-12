"""
Vues pour la gestion des abonnements et de la facturation.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

import logging

from ..models import Abonnement, TypeAbonnement
from ..serializers.billing_serializers import (
    AbonnementSerializer,
    TypeAbonnementSerializer,
)
from ..services.billing_service import BillingService


logger = logging.getLogger(__name__)


class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API pour consulter et gérer les abonnements.
    """
    serializer_class = AbonnementSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Retourne les abonnements de l'utilisateur."""
        user = self.request.user
        return Abonnement.objects.filter(
            user=user
        ).select_related('type_abonnement', 'organization')
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """
        Retourne l'abonnement actif de l'utilisateur.
        """
        try:
            abonnement = Abonnement.objects.filter(
                user=request.user,
                status='ACTIF'
            ).select_related('type_abonnement').first()
            
            if not abonnement:
                return Response({
                    'message': 'Aucun abonnement actif',
                    'has_subscription': False,
                }, status=status.HTTP_200_OK)
            
            serializer = self.get_serializer(abonnement)
            return Response({
                'subscription': serializer.data,
                'has_subscription': True,
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'abonnement: {e}", exc_info=True)
            return Response(
                {'error': 'Erreur lors de la récupération de l\'abonnement'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def create_subscription(self, request):
        """
        Crée un nouvel abonnement pour l'utilisateur.
        """
        try:
            type_abonnement_id = request.data.get('type_abonnement_id')
            payment_method_id = request.data.get('payment_method_id')
            
            if not type_abonnement_id:
                return Response(
                    {'error': 'type_abonnement_id requis'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Vérifier que l'utilisateur n'a pas déjà un abonnement actif
            existing = Abonnement.objects.filter(
                user=request.user,
                status='ACTIF'
            ).exists()
            
            if existing:
                return Response(
                    {'error': 'Vous avez déjà un abonnement actif'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Récupérer le type d'abonnement
            type_abonnement = get_object_or_404(TypeAbonnement, id=type_abonnement_id)
            
            # Utiliser le BillingService pour créer l'abonnement
            billing_service = BillingService(user=request.user)
            result = billing_service.create_subscription(
                type_abonnement=type_abonnement,
                payment_method_id=payment_method_id
            )
            
            if result.success:
                return Response({
                    'message': 'Abonnement créé avec succès',
                    'subscription': result.data,
                }, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': result.error_message},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'abonnement: {e}", exc_info=True)
            return Response(
                {'error': 'Erreur lors de la création de l\'abonnement'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Annule un abonnement.
        """
        try:
            abonnement = self.get_object()
            
            # Vérifier que l'utilisateur est le propriétaire
            if abonnement.user != request.user:
                return Response(
                    {'error': 'Non autorisé'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            reason = request.data.get('reason', 'Annulation par l\'utilisateur')
            at_period_end = request.data.get('at_period_end', True)
            
            # Utiliser le BillingService pour annuler
            billing_service = BillingService(user=request.user)
            result = billing_service.cancel_subscription(
                subscription_id=abonnement.id,
                reason=reason,
                at_period_end=at_period_end
            )
            
            if result.success:
                return Response({
                    'message': 'Abonnement annulé avec succès',
                    'subscription': result.data,
                })
            else:
                return Response(
                    {'error': result.error_message},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Erreur lors de l'annulation: {e}", exc_info=True)
            return Response(
                {'error': 'Erreur lors de l\'annulation'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def upgrade(self, request, pk=None):
        """
        Met à niveau un abonnement vers un plan supérieur.
        """
        try:
            abonnement = self.get_object()
            
            if abonnement.client != request.user:
                return Response(
                    {'error': 'Non autorisé'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            new_type_id = request.data.get('new_type_abonnement_id')
            if not new_type_id:
                return Response(
                    {'error': 'new_type_abonnement_id requis'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            new_type = get_object_or_404(TypeAbonnement, id=new_type_id)
            
            # Utiliser le BillingService
            billing_service = BillingService(user=request.user)
            result = billing_service.upgrade_subscription(
                subscription_id=abonnement.id,
                new_type_abonnement=new_type
            )
            
            if result.success:
                return Response({
                    'message': 'Abonnement mis à niveau avec succès',
                    'subscription': result.data,
                })
            else:
                return Response(
                    {'error': result.error_message},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à niveau: {e}", exc_info=True)
            return Response(
                {'error': 'Erreur lors de la mise à niveau'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def usage(self, request, pk=None):
        """
        Retourne l'utilisation actuelle de l'abonnement.
        """
        try:
            abonnement = self.get_object()
            
            if abonnement.client != request.user:
                return Response(
                    {'error': 'Non autorisé'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Calculer l'utilisation
            usage_data = {
                'projects_count': abonnement.organization.projects.count() if abonnement.organization else 0,
                'projects_limit': abonnement.type_abonnement.quotas.get('max_projects', 0),
                'storage_used': 0,  # À implémenter
                'storage_limit': abonnement.type_abonnement.quotas.get('max_storage_gb', 0),
                'api_calls_this_month': 0,  # À implémenter
                'api_calls_limit': abonnement.type_abonnement.quotas.get('max_api_calls', 0),
            }
            
            return Response(usage_data)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'utilisation: {e}", exc_info=True)
            return Response(
                {'error': 'Erreur lors de la récupération de l\'utilisation'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API pour consulter les plans d'abonnement disponibles.
    """
    queryset = TypeAbonnement.objects.filter(is_active=True)
    serializer_class = TypeAbonnementSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def compare(self, request):
        """
        Compare tous les plans disponibles.
        """
        plans = self.get_queryset().order_by('tarif_mensuel')
        serializer = self.get_serializer(plans, many=True)
        
        return Response({
            'plans': serializer.data,
            'comparison': {
                'features': [
                    'Nombre de projets',
                    'Stockage',
                    'Appels API',
                    'Support',
                    'Collaboration',
                    'Déploiement',
                ]
            }
        })




class PaymentMethodViewSet(viewsets.ViewSet):
    """
    API pour gérer les moyens de paiement.
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Liste les moyens de paiement de l'utilisateur."""
        try:
            # TODO: Implémenter l'intégration avec la banque digitale
            return Response({
                'message': 'Intégration banque digitale à implémenter',
                'payment_methods': []
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des moyens de paiement: {e}", exc_info=True)
            return Response(
                {'error': 'Erreur lors de la récupération'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request):
        """Ajoute un nouveau moyen de paiement."""
        try:
            # TODO: Implémenter l'intégration avec la banque digitale
            return Response({
                'message': 'Intégration banque digitale à implémenter'
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
                
        except Exception as e:
            logger.error(f"Erreur lors de la création du moyen de paiement: {e}", exc_info=True)
            return Response(
                {'error': 'Erreur lors de la création'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
