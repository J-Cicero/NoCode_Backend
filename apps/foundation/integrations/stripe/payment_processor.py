"""
Processeur de paiements Stripe.
Gère les paiements uniques et les transactions.
"""
import logging
import stripe
from django.conf import settings
from decimal import Decimal
from ...models import Paiement, Organization, MoyenDePaiement
from ...services.event_bus import EventBus

logger = logging.getLogger(__name__)


class StripePaymentProcessor:
    """
    Processeur de paiements Stripe pour les transactions uniques.
    """
    
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
    
    def create_payment_intent(self, organization, amount, currency='eur', description=None, metadata=None):
        """
        Crée un Payment Intent Stripe.
        """
        try:
            # Convertir le montant en centimes
            amount_cents = int(amount * 100)
            
            # Créer le Payment Intent
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                customer=organization.stripe_customer_id,
                description=description or f"Paiement pour {organization.name}",
                metadata=metadata or {},
                automatic_payment_methods={'enabled': True},
            )
            
            # Créer l'enregistrement local
            paiement = Paiement.objects.create(
                organization=organization,
                montant=amount,
                devise=currency.upper(),
                status='PENDING',
                stripe_payment_intent_id=payment_intent['id'],
                description=description,
            )
            
            # Publier un événement
            EventBus.publish('payment.intent_created', {
                'payment_id': paiement.id,
                'organization_id': organization.id,
                'amount': amount,
            })
            
            logger.info(f"Payment Intent créé: {payment_intent['id']}")
            
            return {
                'success': True,
                'payment_intent': payment_intent,
                'payment_id': paiement.id,
                'client_secret': payment_intent['client_secret'],
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe lors de la création du Payment Intent: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'stripe_error',
            }
        
        except Exception as e:
            logger.error(f"Erreur lors de la création du Payment Intent: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'internal_error',
            }
    
    def confirm_payment_intent(self, payment_intent_id, payment_method_id=None):
        """
        Confirme un Payment Intent.
        """
        try:
            confirm_params = {}
            if payment_method_id:
                confirm_params['payment_method'] = payment_method_id
            
            payment_intent = stripe.PaymentIntent.confirm(
                payment_intent_id,
                **confirm_params
            )
            
            # Mettre à jour le paiement local
            try:
                paiement = Paiement.objects.get(stripe_payment_intent_id=payment_intent_id)
                paiement.status = self._map_payment_intent_status(payment_intent['status'])
                paiement.save()
            except Paiement.DoesNotExist:
                logger.warning(f"Paiement local non trouvé pour PI: {payment_intent_id}")
            
            return {
                'success': True,
                'payment_intent': payment_intent,
                'status': payment_intent['status'],
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur lors de la confirmation du Payment Intent: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'stripe_error',
            }
    
    def cancel_payment_intent(self, payment_intent_id):
        """
        Annule un Payment Intent.
        """
        try:
            payment_intent = stripe.PaymentIntent.cancel(payment_intent_id)
            
            # Mettre à jour le paiement local
            try:
                paiement = Paiement.objects.get(stripe_payment_intent_id=payment_intent_id)
                paiement.status = 'CANCELED'
                paiement.save()
                
                EventBus.publish('payment.canceled', {
                    'payment_id': paiement.id,
                    'organization_id': paiement.organization.id,
                })
            except Paiement.DoesNotExist:
                pass
            
            return {
                'success': True,
                'payment_intent': payment_intent,
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur lors de l'annulation du Payment Intent: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def create_refund(self, payment_intent_id, amount=None, reason=None):
        """
        Crée un remboursement.
        """
        try:
            # Récupérer le Payment Intent pour obtenir le charge
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if not payment_intent.get('latest_charge'):
                return {
                    'success': False,
                    'error': 'Aucun charge trouvé pour ce Payment Intent',
                }
            
            refund_params = {
                'charge': payment_intent['latest_charge'],
            }
            
            if amount:
                refund_params['amount'] = int(amount * 100)  # Convertir en centimes
            
            if reason:
                refund_params['reason'] = reason
            
            refund = stripe.Refund.create(**refund_params)
            
            # Mettre à jour le paiement local
            try:
                paiement = Paiement.objects.get(stripe_payment_intent_id=payment_intent_id)
                if refund['amount'] == payment_intent['amount']:
                    paiement.status = 'REFUNDED'
                else:
                    paiement.status = 'PARTIALLY_REFUNDED'
                paiement.save()
                
                EventBus.publish('payment.refunded', {
                    'payment_id': paiement.id,
                    'organization_id': paiement.organization.id,
                    'refund_amount': refund['amount'] / 100,
                })
            except Paiement.DoesNotExist:
                pass
            
            return {
                'success': True,
                'refund': refund,
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur lors du remboursement: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def get_payment_methods(self, customer_id):
        """
        Récupère les moyens de paiement d'un client.
        """
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type='card',
            )
            
            return {
                'success': True,
                'payment_methods': payment_methods['data'],
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur lors de la récupération des moyens de paiement: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def attach_payment_method(self, payment_method_id, customer_id):
        """
        Attache un moyen de paiement à un client.
        """
        try:
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id,
            )
            
            return {
                'success': True,
                'payment_method': payment_method,
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur lors de l'attachement du moyen de paiement: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def detach_payment_method(self, payment_method_id):
        """
        Détache un moyen de paiement.
        """
        try:
            payment_method = stripe.PaymentMethod.detach(payment_method_id)
            
            return {
                'success': True,
                'payment_method': payment_method,
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur lors du détachement du moyen de paiement: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def _map_payment_intent_status(self, stripe_status):
        """
        Mappe les statuts Stripe vers les statuts locaux.
        """
        mapping = {
            'requires_payment_method': 'PENDING',
            'requires_confirmation': 'PENDING',
            'requires_action': 'PENDING',
            'processing': 'PROCESSING',
            'succeeded': 'COMPLETED',
            'canceled': 'CANCELED',
        }
        return mapping.get(stripe_status, 'PENDING')
