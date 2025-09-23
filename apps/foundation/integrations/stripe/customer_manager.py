"""
Gestionnaire de clients Stripe.
Gère les clients Stripe et leur synchronisation avec les organisations.
"""
import logging
import stripe
from django.conf import settings
from ...models import Organization, User
from ...services.event_bus import EventBus

logger = logging.getLogger(__name__)


class StripeCustomerManager:
    """
    Gestionnaire de clients Stripe.
    """
    
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
    
    def create_customer(self, organization, user=None):
        """
        Crée un client Stripe pour une organisation.
        """
        try:
            customer_params = {
                'name': organization.name,
                'metadata': {
                    'organization_id': str(organization.id),
                    'organization_type': organization.type,
                }
            }
            
            if user:
                customer_params['email'] = user.email
                customer_params['metadata']['user_id'] = str(user.id)
            
            customer = stripe.Customer.create(**customer_params)
            
            organization.stripe_customer_id = customer['id']
            organization.save()
            
            EventBus.publish('stripe.customer.created', {
                'customer_id': customer['id'],
                'organization_id': organization.id,
            })
            
            return {
                'success': True,
                'customer': customer,
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe lors de la création du client: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def update_customer(self, organization, **update_fields):
        """
        Met à jour un client Stripe.
        """
        try:
            if not organization.stripe_customer_id:
                return {
                    'success': False,
                    'error': 'Aucun client Stripe associé',
                }
            
            customer = stripe.Customer.modify(
                organization.stripe_customer_id,
                **update_fields
            )
            
            return {
                'success': True,
                'customer': customer,
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def get_customer(self, organization):
        """
        Récupère un client Stripe.
        """
        try:
            if not organization.stripe_customer_id:
                return {
                    'success': False,
                    'error': 'Aucun client Stripe associé',
                }
            
            customer = stripe.Customer.retrieve(organization.stripe_customer_id)
            
            return {
                'success': True,
                'customer': customer,
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def get_customer_payment_methods(self, organization, type='card'):
        """
        Récupère les moyens de paiement d'un client.
        """
        try:
            if not organization.stripe_customer_id:
                return {
                    'success': False,
                    'error': 'Aucun client Stripe associé',
                }
            
            payment_methods = stripe.PaymentMethod.list(
                customer=organization.stripe_customer_id,
                type=type,
            )
            
            return {
                'success': True,
                'payment_methods': payment_methods['data'],
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def get_customer_invoices(self, organization, limit=10):
        """
        Récupère les factures d'un client.
        """
        try:
            if not organization.stripe_customer_id:
                return {
                    'success': False,
                    'error': 'Aucun client Stripe associé',
                }
            
            invoices = stripe.Invoice.list(
                customer=organization.stripe_customer_id,
                limit=limit,
            )
            
            return {
                'success': True,
                'invoices': invoices['data'],
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe: {e}")
            return {
                'success': False,
                'error': str(e),
            }
