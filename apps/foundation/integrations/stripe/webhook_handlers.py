
import logging
import stripe
from django.conf import settings
from ...models import Abonnement, Paiement, Facture, Organization, TypeAbonnement
from ...services.event_bus import EventBus
from ...services.stripe_service import StripeService

logger = logging.getLogger(__name__)


class StripeWebhookHandler:
    
    def __init__(self):
        self.stripe_service = StripeService()
        self.event_handlers = {
            'payment_intent.succeeded': self.handle_payment_succeeded,
            'payment_intent.payment_failed': self.handle_payment_failed,
            'customer.subscription.created': self.handle_subscription_created,
            'customer.subscription.updated': self.handle_subscription_updated,
            'customer.subscription.deleted': self.handle_subscription_deleted,
            'invoice.payment_succeeded': self.handle_invoice_paid,
            'invoice.payment_failed': self.handle_invoice_payment_failed,
        }
    
    def handle_webhook(self, payload, sig_header):
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            
            logger.info(f"Webhook Stripe reçu: {event['type']}")
            
            handler = self.event_handlers.get(event['type'])
            if handler:
                result = handler(event)
                EventBus.publish('stripe.webhook.processed', {
                    'event_type': event['type'],
                    'event_id': event['id'],
                    'result': result,
                })
                return result
            else:
                logger.warning(f"Handler non trouvé: {event['type']}")
                return {'status': 'ignored'}
                
        except Exception as e:
            logger.error(f"Erreur webhook Stripe: {e}")
            EventBus.publish('stripe.webhook.error', {
                'event_type': event.get('type', 'unknown'),
                'error': str(e),
            })
            raise
    
    def handle_payment_succeeded(self, event):

        payment_intent = event['data']['object']
        try:
            paiement = Paiement.objects.get(stripe_payment_intent_id=payment_intent['id'])
            paiement.status = 'COMPLETED'
            paiement.save()
            
            EventBus.publish('payment.succeeded', {
                'payment_id': paiement.id,
                'organization_id': paiement.organization.id,
            })
            return {'status': 'success'}
        except Paiement.DoesNotExist:
            return {'status': 'ignored'}
    
    def handle_payment_failed(self, event):
        payment_intent = event['data']['object']
        try:
            paiement = Paiement.objects.get(stripe_payment_intent_id=payment_intent['id'])
            paiement.status = 'FAILED'
            paiement.save()
            
            EventBus.publish('payment.failed', {
                'payment_id': paiement.id,
                'organization_id': paiement.organization.id,
            })
            return {'status': 'success'}
        except Paiement.DoesNotExist:
            return {'status': 'ignored'}
    
    def handle_subscription_created(self, event):
        subscription = event['data']['object']
        try:
            customer = stripe.Customer.retrieve(subscription['customer'])
            organization = Organization.objects.get(stripe_customer_id=customer['id'])
            
            price_id = subscription['items']['data'][0]['price']['id']
            type_abonnement = TypeAbonnement.objects.get(stripe_price_id=price_id)
            
            abonnement = Abonnement.objects.create(
                organization=organization,
                type_abonnement=type_abonnement,
                stripe_subscription_id=subscription['id'],
                status='ACTIF',
                date_debut=self.stripe_service._timestamp_to_datetime(subscription['current_period_start']),
                date_fin=self.stripe_service._timestamp_to_datetime(subscription['current_period_end']),
            )
            
            EventBus.publish('subscription.created', {
                'subscription_id': abonnement.id,
                'organization_id': organization.id,
            })
            return {'status': 'success'}
        except Exception as e:
            logger.error(f"Erreur création abonnement: {e}")
            return {'status': 'error'}
    
    def handle_subscription_updated(self, event):
        subscription = event['data']['object']
        try:
            abonnement = Abonnement.objects.get(stripe_subscription_id=subscription['id'])
            abonnement.status = self._map_stripe_status(subscription['status'])
            abonnement.save()
            
            EventBus.publish('subscription.updated', {
                'subscription_id': abonnement.id,
            })
            return {'status': 'success'}
        except Abonnement.DoesNotExist:
            return {'status': 'ignored'}
    
    def handle_subscription_deleted(self, event):
        subscription = event['data']['object']
        try:
            abonnement = Abonnement.objects.get(stripe_subscription_id=subscription['id'])
            abonnement.status = 'ANNULE'
            abonnement.save()
            
            EventBus.publish('subscription.canceled', {
                'subscription_id': abonnement.id,
            })
            return {'status': 'success'}
        except Abonnement.DoesNotExist:
            return {'status': 'ignored'}
    
    def handle_invoice_paid(self, event):
        invoice = event['data']['object']
        try:
            facture = Facture.objects.get(stripe_invoice_id=invoice['id'])
            facture.status = 'PAID'
            facture.save()
            
            EventBus.publish('invoice.paid', {
                'invoice_id': facture.id,
            })
            return {'status': 'success'}
        except Facture.DoesNotExist:
            return {'status': 'ignored'}
    
    def handle_invoice_payment_failed(self, event):
        invoice = event['data']['object']
        try:
            facture = Facture.objects.get(stripe_invoice_id=invoice['id'])
            facture.status = 'OVERDUE'
            facture.save()
            
            EventBus.publish('invoice.payment_failed', {
                'invoice_id': facture.id,
            })
            return {'status': 'success'}
        except Facture.DoesNotExist:
            return {'status': 'ignored'}
    
    def _map_stripe_status(self, stripe_status):
        mapping = {
            'active': 'ACTIF',
            'canceled': 'ANNULE',
            'incomplete': 'PENDING',
            'past_due': 'OVERDUE',
        }
        return mapping.get(stripe_status, 'PENDING')
