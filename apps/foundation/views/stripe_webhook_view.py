"""
Vue dédiée pour les webhooks Stripe.
Traite les événements Stripe de manière sécurisée.
"""
import logging
import json
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views import View
from ..integrations.stripe.webhook_handlers import StripeWebhookHandler

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(require_POST, name='dispatch')
class StripeWebhookView(View):
    """
    Vue pour traiter les webhooks Stripe.
    """
    
    def __init__(self):
        super().__init__()
        self.webhook_handler = StripeWebhookHandler()
    
    def post(self, request):
        """
        Traite les webhooks Stripe.
        """
        try:
            # Récupérer le payload et la signature
            payload = request.body
            sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
            
            if not sig_header:
                logger.warning("Webhook Stripe sans signature")
                return HttpResponseBadRequest("Signature manquante")
            
            # Traiter le webhook
            result = self.webhook_handler.handle_webhook(payload, sig_header)
            
            logger.info(f"Webhook Stripe traité avec succès: {result}")
            
            return HttpResponse(
                json.dumps(result),
                content_type='application/json',
                status=200
            )
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du webhook Stripe: {e}")
            return HttpResponse(
                json.dumps({'error': 'Erreur interne'}),
                content_type='application/json',
                status=500
            )
