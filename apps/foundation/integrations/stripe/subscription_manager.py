
import logging
import stripe
from django.conf import settings
from ...models import Abonnement, TypeAbonnement
from ...services.event_bus import EventBus

logger = logging.getLogger(__name__)


class StripeSubscriptionManager:
    """
    Gestionnaire d'abonnements Stripe.
    """
    
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
    
    def create_subscription(self, organization, plan_id, payment_method_id=None, trial_days=None):
        """
        Crée un abonnement Stripe.
        """
        try:
            # Récupérer le type d'abonnement
            type_abonnement = TypeAbonnement.objects.get(id=plan_id)
            
            subscription_params = {
                'customer': organization.stripe_customer_id,
                'items': [{'price': type_abonnement.stripe_price_id}],
                'expand': ['latest_invoice.payment_intent'],
            }
            
            if payment_method_id:
                subscription_params['default_payment_method'] = payment_method_id
            
            if trial_days:
                subscription_params['trial_period_days'] = trial_days
            
            subscription = stripe.Subscription.create(**subscription_params)
            
            # Créer l'abonnement local
            abonnement = Abonnement.objects.create(
                organization=organization,
                type_abonnement=type_abonnement,
                stripe_subscription_id=subscription['id'],
                status=self._map_subscription_status(subscription['status']),
                date_debut=self._timestamp_to_datetime(subscription['current_period_start']),
                date_fin=self._timestamp_to_datetime(subscription['current_period_end']),
                trial_end=self._timestamp_to_datetime(subscription.get('trial_end')) if subscription.get('trial_end') else None,
            )
            
            EventBus.publish('subscription.created', {
                'subscription_id': abonnement.id,
                'organization_id': organization.id,
                'plan': type_abonnement.nom,
            })
            
            return {
                'success': True,
                'subscription': subscription,
                'local_subscription_id': abonnement.id,
            }
            
        except TypeAbonnement.DoesNotExist:
            return {
                'success': False,
                'error': 'Plan d\'abonnement non trouvé',
            }
        
        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe lors de la création d'abonnement: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def update_subscription(self, subscription_id, new_plan_id=None, prorate=True):
        """
        Met à jour un abonnement.
        """
        try:
            abonnement = Abonnement.objects.get(id=subscription_id)
            
            update_params = {}
            
            if new_plan_id:
                new_type = TypeAbonnement.objects.get(id=new_plan_id)
                
                # Récupérer l'abonnement Stripe actuel
                subscription = stripe.Subscription.retrieve(abonnement.stripe_subscription_id)
                
                update_params['items'] = [{
                    'id': subscription['items']['data'][0]['id'],
                    'price': new_type.stripe_price_id,
                }]
                update_params['proration_behavior'] = 'create_prorations' if prorate else 'none'
            
            if update_params:
                updated_subscription = stripe.Subscription.modify(
                    abonnement.stripe_subscription_id,
                    **update_params
                )
                
                # Mettre à jour l'abonnement local
                if new_plan_id:
                    abonnement.type_abonnement = new_type
                
                abonnement.status = self._map_subscription_status(updated_subscription['status'])
                abonnement.save()
                
                EventBus.publish('subscription.updated', {
                    'subscription_id': abonnement.id,
                    'organization_id': abonnement.organization.id,
                })
                
                return {
                    'success': True,
                    'subscription': updated_subscription,
                }
            
            return {
                'success': True,
                'message': 'Aucune modification nécessaire',
            }
            
        except (Abonnement.DoesNotExist, TypeAbonnement.DoesNotExist) as e:
            return {
                'success': False,
                'error': str(e),
            }
        
        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe lors de la mise à jour d'abonnement: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def cancel_subscription(self, subscription_id, at_period_end=True):
        """
        Annule un abonnement.
        """
        try:
            abonnement = Abonnement.objects.get(id=subscription_id)
            
            if at_period_end:
                # Annuler à la fin de la période
                subscription = stripe.Subscription.modify(
                    abonnement.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                abonnement.status = 'PENDING_CANCEL'
            else:
                # Annuler immédiatement
                subscription = stripe.Subscription.delete(abonnement.stripe_subscription_id)
                abonnement.status = 'ANNULE'
                abonnement.date_annulation = self._timestamp_to_datetime(subscription.get('canceled_at'))
            
            abonnement.save()
            
            EventBus.publish('subscription.canceled', {
                'subscription_id': abonnement.id,
                'organization_id': abonnement.organization.id,
                'immediate': not at_period_end,
            })
            
            return {
                'success': True,
                'subscription': subscription,
            }
            
        except Abonnement.DoesNotExist:
            return {
                'success': False,
                'error': 'Abonnement non trouvé',
            }
        
        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe lors de l'annulation d'abonnement: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def reactivate_subscription(self, subscription_id):
        """
        Réactive un abonnement annulé.
        """
        try:
            abonnement = Abonnement.objects.get(id=subscription_id)
            
            # Annuler la programmation d'annulation
            subscription = stripe.Subscription.modify(
                abonnement.stripe_subscription_id,
                cancel_at_period_end=False
            )
            
            abonnement.status = self._map_subscription_status(subscription['status'])
            abonnement.save()
            
            EventBus.publish('subscription.reactivated', {
                'subscription_id': abonnement.id,
                'organization_id': abonnement.organization.id,
            })
            
            return {
                'success': True,
                'subscription': subscription,
            }
            
        except Abonnement.DoesNotExist:
            return {
                'success': False,
                'error': 'Abonnement non trouvé',
            }
        
        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe lors de la réactivation: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def get_subscription_usage(self, subscription_id):
        """
        Récupère l'usage d'un abonnement (pour les plans à l'usage).
        """
        try:
            abonnement = Abonnement.objects.get(id=subscription_id)
            
            # Récupérer les éléments d'usage
            usage_records = stripe.SubscriptionItem.list_usage_record_summaries(
                abonnement.stripe_subscription_id
            )
            
            return {
                'success': True,
                'usage_records': usage_records['data'],
            }
            
        except Abonnement.DoesNotExist:
            return {
                'success': False,
                'error': 'Abonnement non trouvé',
            }
        
        except stripe.error.StripeError as e:
            logger.error(f"Erreur lors de la récupération de l'usage: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def report_usage(self, subscription_id, quantity, timestamp=None):
        """
        Rapporte l'usage pour un abonnement à l'usage.
        """
        try:
            abonnement = Abonnement.objects.get(id=subscription_id)
            
            # Récupérer l'abonnement Stripe
            subscription = stripe.Subscription.retrieve(abonnement.stripe_subscription_id)
            
            # Trouver l'item d'usage (supposé être le premier)
            subscription_item_id = subscription['items']['data'][0]['id']
            
            usage_params = {
                'quantity': quantity,
                'action': 'increment',
            }
            
            if timestamp:
                usage_params['timestamp'] = timestamp
            
            usage_record = stripe.UsageRecord.create(
                subscription_item_id,
                **usage_params
            )
            
            EventBus.publish('subscription.usage_reported', {
                'subscription_id': abonnement.id,
                'organization_id': abonnement.organization.id,
                'quantity': quantity,
            })
            
            return {
                'success': True,
                'usage_record': usage_record,
            }
            
        except Abonnement.DoesNotExist:
            return {
                'success': False,
                'error': 'Abonnement non trouvé',
            }
        
        except stripe.error.StripeError as e:
            logger.error(f"Erreur lors du rapport d'usage: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def _map_subscription_status(self, stripe_status):
        """
        Mappe les statuts Stripe vers les statuts locaux.
        """
        mapping = {
            'active': 'ACTIF',
            'canceled': 'ANNULE',
            'incomplete': 'PENDING',
            'incomplete_expired': 'EXPIRED',
            'past_due': 'OVERDUE',
            'trialing': 'TRIAL',
            'unpaid': 'UNPAID',
        }
        return mapping.get(stripe_status, 'PENDING')
    
    def _timestamp_to_datetime(self, timestamp):
        """
        Convertit un timestamp Unix en datetime.
        """
        if timestamp:
            from django.utils import timezone
            import datetime
            return timezone.make_aware(datetime.datetime.fromtimestamp(timestamp))
        return None
