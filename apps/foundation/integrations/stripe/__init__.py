"""
Intégration Stripe pour le module Foundation.
Gère les paiements, abonnements et webhooks Stripe.
"""

from .webhook_handlers import StripeWebhookHandler
from .payment_processor import StripePaymentProcessor
from .subscription_manager import StripeSubscriptionManager
from .customer_manager import StripeCustomerManager
