"""
Vues pour la gestion de la facturation et des abonnements.
Expose les APIs pour les plans, abonnements, paiements, factures, etc.
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from ..services.billing_service import BillingService
from ..services.stripe_service import StripeService, StripeWebhookHandler
from ..serializers import (
    TypeAbonnementSerializer, AbonnementCreateSerializer,
    PaymentIntentSerializer, BillingInfoSerializer
)
from ..models import Organization, TypeAbonnement


User = get_user_model()


class SubscriptionPlansView(APIView):
    """Vue pour les plans d'abonnement."""
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Liste les plans d'abonnement disponibles."""
        user_type = request.query_params.get('user_type')
        
        billing_service = BillingService(user=request.user if request.user.is_authenticated else None)
        result = billing_service.get_available_plans(user_type)
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_400_BAD_REQUEST)


class OrganizationSubscriptionView(APIView):
    """Vue pour les abonnements d'organisation."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, org_id):
        """Souscrit une organisation à un plan."""
        serializer = AbonnementCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            try:
                organization = Organization.objects.get(id=org_id)
            except Organization.DoesNotExist:
                return Response({
                    'error': 'Organisation introuvable'
                }, status=status.HTTP_404_NOT_FOUND)
            
            billing_service = BillingService(user=request.user, organization=organization)
            result = billing_service.subscribe_organization(
                organization_id=org_id,
                plan_id=serializer.validated_data['type_abonnement_id'],
                payment_method_id=serializer.validated_data.get('payment_method_id')
            )
            
            if result.success:
                return Response(result.data, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': result.error_message
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, org_id):
        """Annule l'abonnement d'une organisation."""
        reason = request.data.get('reason', '')
        
        try:
            organization = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return Response({
                'error': 'Organisation introuvable'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Récupérer l'abonnement actif
        from ..models import Abonnement
        subscription = Abonnement.objects.filter(
            organization=organization,
            status='ACTIF'
        ).first()
        
        if not subscription:
            return Response({
                'error': 'Aucun abonnement actif trouvé'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        billing_service = BillingService(user=request.user, organization=organization)
        result = billing_service.cancel_subscription(subscription.id, reason)
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_400_BAD_REQUEST)


class OrganizationBillingInfoView(APIView):
    """Vue pour les informations de facturation d'une organisation."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id):
        """Récupère les informations de facturation."""
        try:
            organization = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return Response({
                'error': 'Organisation introuvable'
            }, status=status.HTTP_404_NOT_FOUND)
        
        billing_service = BillingService(user=request.user, organization=organization)
        result = billing_service.get_organization_billing_info(org_id)
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_400_BAD_REQUEST)


class CreatePaymentIntentView(APIView):
    """Vue pour créer un Payment Intent Stripe."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Crée un Payment Intent pour un paiement."""
        serializer = PaymentIntentSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                organization = Organization.objects.get(
                    id=serializer.validated_data['organization_id']
                )
            except Organization.DoesNotExist:
                return Response({
                    'error': 'Organisation introuvable'
                }, status=status.HTTP_404_NOT_FOUND)
            
            stripe_service = StripeService(user=request.user, organization=organization)
            result = stripe_service.create_payment_intent(
                amount=serializer.validated_data['amount'],
                currency=serializer.validated_data.get('currency', 'eur'),
                metadata={
                    'organization_id': organization.id,
                    'user_id': request.user.id,
                    'description': serializer.validated_data.get('description', '')
                }
            )
            
            if result.success:
                return Response(result.data, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': result.error_message
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StripeWebhookView(APIView):
    """Vue pour les webhooks Stripe."""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Traite les webhooks Stripe."""
        webhook_handler = StripeWebhookHandler()
        result = webhook_handler.handle_webhook(request)
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_400_BAD_REQUEST)


class SubscriptionLimitsView(APIView):
    """Vue pour vérifier les limites d'abonnement."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, org_id):
        """Vérifie si une limite d'abonnement est atteinte."""
        limit_type = request.data.get('limit_type')
        current_usage = request.data.get('current_usage', 0)
        
        if not limit_type:
            return Response({
                'error': 'Type de limite requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            organization = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return Response({
                'error': 'Organisation introuvable'
            }, status=status.HTTP_404_NOT_FOUND)
        
        billing_service = BillingService(user=request.user, organization=organization)
        result = billing_service.check_subscription_limits(org_id, limit_type, current_usage)
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_400_BAD_REQUEST)


class InvoiceGenerateView(APIView):
    """Vue pour générer des factures."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, org_id):
        """Génère une facture pour une organisation."""
        from django.utils import timezone
        from datetime import datetime
        
        period_start_str = request.data.get('period_start')
        period_end_str = request.data.get('period_end')
        
        if not period_start_str or not period_end_str:
            return Response({
                'error': 'Période de facturation requise (period_start, period_end)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            period_start = datetime.fromisoformat(period_start_str.replace('Z', '+00:00'))
            period_end = datetime.fromisoformat(period_end_str.replace('Z', '+00:00'))
        except ValueError:
            return Response({
                'error': 'Format de date invalide (ISO 8601 requis)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            organization = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return Response({
                'error': 'Organisation introuvable'
            }, status=status.HTTP_404_NOT_FOUND)
        
        billing_service = BillingService(user=request.user, organization=organization)
        result = billing_service.generate_invoice(org_id, period_start, period_end)
        
        if result.success:
            return Response(result.data, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def billing_stats(request):
    """Récupère les statistiques de facturation (admin seulement)."""
    if not request.user.is_staff:
        return Response({
            'error': 'Permissions insuffisantes'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Calculer les statistiques de facturation
    from ..models import Abonnement, Paiement, Facture
    from django.db.models import Sum, Count
    from django.utils import timezone
    from datetime import timedelta
    
    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    stats_data = {
        'total_revenue': float(Paiement.objects.filter(
            status='REUSSI'
        ).aggregate(total=Sum('montant'))['total'] or 0),
        
        'monthly_revenue': float(Paiement.objects.filter(
            status='REUSSI',
            date_paiement__gte=current_month
        ).aggregate(total=Sum('montant'))['total'] or 0),
        
        'active_subscriptions': Abonnement.objects.filter(status='ACTIF').count(),
        
        'pending_payments': Paiement.objects.filter(status='EN_ATTENTE').count(),
        
        'overdue_invoices': Facture.objects.filter(
            status='EMISE',
            date_echeance__lt=timezone.now()
        ).count(),
        
        'churn_rate': 0.0,  # À calculer selon la logique métier
        
        'revenue_by_plan': {},  # À implémenter
        
        'subscription_trends': {}  # À implémenter
    }
    
    return Response(stats_data, status=status.HTTP_200_OK)
