"""
Service d'intégration avec Stripe pour les paiements.
Gère les clients, abonnements, paiements et webhooks Stripe.
"""
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
from django.conf import settings
from django.contrib.auth import get_user_model
from .base_service import BaseService, ServiceResult, BusinessLogicException
from .billing_service import BillingService
from .event_bus import EventBus, FoundationEvents
from ..models import MoyenDePaiement, Paiement, Abonnement, Organization

# Import Stripe (sera installé via requirements.txt)
try:
    import stripe
    stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    stripe = None


logger = logging.getLogger(__name__)
User = get_user_model()


class StripeService(BaseService):
    """
    Service d'intégration avec Stripe.
    Gère toutes les interactions avec l'API Stripe.
    """
    
    def __init__(self, user: User = None, organization: Organization = None):
        super().__init__(user, organization)
        
        if not STRIPE_AVAILABLE:
            logger.error("Stripe n'est pas disponible. Installez le package stripe.")
        
        # Configuration Stripe
        self.stripe_public_key = getattr(settings, 'STRIPE_PUBLIC_KEY', '')
        self.stripe_secret_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
        self.webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
        
        if not self.stripe_secret_key:
            logger.warning("Clé secrète Stripe non configurée")
    
    def _check_stripe_availability(self) -> bool:
        """Vérifie si Stripe est disponible et configuré."""
        if not STRIPE_AVAILABLE:
            return False
        if not self.stripe_secret_key:
            return False
        return True
    
    def create_customer(self, user_or_organization) -> ServiceResult:
        """
        Crée un client Stripe pour un utilisateur ou une organisation.
        """
        try:
            if not self._check_stripe_availability():
                return ServiceResult.error_result("Service Stripe non disponible")
            
            # Déterminer les informations client
            if isinstance(user_or_organization, Organization):
                customer_data = {
                    'email': user_or_organization.billing_email or user_or_organization.owner.email,
                    'name': user_or_organization.name,
                    'description': f"Organisation: {user_or_organization.name}",
                    'metadata': {
                        'organization_id': str(user_or_organization.id),
                        'organization_type': user_or_organization.type,
                        'owner_id': str(user_or_organization.owner.id),
                    }
                }
            else:  # User
                customer_data = {
                    'email': user_or_organization.email,
                    'name': user_or_organization.full_name,
                    'phone': user_or_organization.numero_telephone,
                    'description': f"Utilisateur: {user_or_organization.full_name}",
                    'metadata': {
                        'user_id': str(user_or_organization.id),
                        'user_type': user_or_organization.user_type,
                    }
                }
            
            # Créer le client dans Stripe
            customer = stripe.Customer.create(**customer_data)
            
            self.log_activity('stripe_customer_created', {
                'stripe_customer_id': customer.id,
                'entity_type': 'organization' if isinstance(user_or_organization, Organization) else 'user',
                'entity_id': user_or_organization.id,
            })
            
            return ServiceResult.success_result({
                'customer_id': customer.id,
                'email': customer.email,
                'name': customer.name,
                'created': customer.created,
            })
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe lors de la création du client: {e}", exc_info=True)
            return ServiceResult.error_result(f"Erreur Stripe: {str(e)}")
        except Exception as e:
            logger.error(f"Erreur lors de la création du client Stripe: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la création du client")
    
    def create_payment_method(self, customer_id: str, payment_method_data: Dict) -> ServiceResult:
        """
        Crée et attache un moyen de paiement à un client Stripe.
        """
        try:
            if not self._check_stripe_availability():
                return ServiceResult.error_result("Service Stripe non disponible")
            
            # Créer le moyen de paiement
            payment_method = stripe.PaymentMethod.create(
                type=payment_method_data.get('type', 'card'),
                card=payment_method_data.get('card', {}),
            )
            
            # L'attacher au client
            payment_method.attach(customer=customer_id)
            
            # Créer l'enregistrement local
            if self.user:
                local_payment_method = MoyenDePaiement.objects.create(
                    user=self.user,
                    type='CARTE_CREDIT',
                    provider_token=payment_method.id,
                    details={
                        'last4': payment_method.card.last4,
                        'brand': payment_method.card.brand,
                        'exp_month': payment_method.card.exp_month,
                        'exp_year': payment_method.card.exp_year,
                        'country': payment_method.card.country,
                    },
                    status='ACTIVE',
                )
                
                self.log_activity('payment_method_created', {
                    'stripe_payment_method_id': payment_method.id,
                    'local_payment_method_id': local_payment_method.id,
                    'last4': payment_method.card.last4,
                })
            
            return ServiceResult.success_result({
                'payment_method_id': payment_method.id,
                'type': payment_method.type,
                'card': {
                    'last4': payment_method.card.last4,
                    'brand': payment_method.card.brand,
                    'exp_month': payment_method.card.exp_month,
                    'exp_year': payment_method.card.exp_year,
                },
                'local_id': local_payment_method.id if self.user else None,
            })
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe lors de la création du moyen de paiement: {e}", exc_info=True)
            return ServiceResult.error_result(f"Erreur Stripe: {str(e)}")
        except Exception as e:
            logger.error(f"Erreur lors de la création du moyen de paiement: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la création du moyen de paiement")
    
    def create_subscription(self, customer_id: str, price_id: str, 
                          payment_method_id: str = None) -> ServiceResult:
        """
        Crée un abonnement Stripe.
        """
        try:
            if not self._check_stripe_availability():
                return ServiceResult.error_result("Service Stripe non disponible")
            
            subscription_data = {
                'customer': customer_id,
                'items': [{'price': price_id}],
                'expand': ['latest_invoice.payment_intent'],
            }
            
            # Ajouter le moyen de paiement par défaut si fourni
            if payment_method_id:
                subscription_data['default_payment_method'] = payment_method_id
            
            # Créer l'abonnement
            subscription = stripe.Subscription.create(**subscription_data)
            
            self.log_activity('stripe_subscription_created', {
                'stripe_subscription_id': subscription.id,
                'customer_id': customer_id,
                'price_id': price_id,
                'status': subscription.status,
            })
            
            # Préparer les données de réponse
            result_data = {
                'subscription_id': subscription.id,
                'status': subscription.status,
                'current_period_start': subscription.current_period_start,
                'current_period_end': subscription.current_period_end,
                'created': subscription.created,
            }
            
            # Ajouter les informations de paiement si nécessaire
            if subscription.latest_invoice:
                invoice = subscription.latest_invoice
                result_data['latest_invoice'] = {
                    'id': invoice.id,
                    'status': invoice.status,
                    'amount_paid': invoice.amount_paid,
                    'amount_due': invoice.amount_due,
                }
                
                if invoice.payment_intent:
                    result_data['payment_intent'] = {
                        'id': invoice.payment_intent.id,
                        'status': invoice.payment_intent.status,
                        'client_secret': invoice.payment_intent.client_secret,
                    }
            
            return ServiceResult.success_result(result_data)
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe lors de la création de l'abonnement: {e}", exc_info=True)
            return ServiceResult.error_result(f"Erreur Stripe: {str(e)}")
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'abonnement Stripe: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la création de l'abonnement")
    
    def create_payment_intent(self, amount: Decimal, currency: str = 'eur', 
                            customer_id: str = None, metadata: Dict = None) -> ServiceResult:
        """
        Crée un Payment Intent Stripe pour un paiement unique.
        """
        try:
            if not self._check_stripe_availability():
                return ServiceResult.error_result("Service Stripe non disponible")
            
            # Convertir le montant en centimes
            amount_cents = int(amount * 100)
            
            payment_intent_data = {
                'amount': amount_cents,
                'currency': currency,
                'automatic_payment_methods': {'enabled': True},
                'metadata': metadata or {},
            }
            
            if customer_id:
                payment_intent_data['customer'] = customer_id
            
            # Créer le Payment Intent
            payment_intent = stripe.PaymentIntent.create(**payment_intent_data)
            
            self.log_activity('stripe_payment_intent_created', {
                'payment_intent_id': payment_intent.id,
                'amount': float(amount),
                'currency': currency,
                'customer_id': customer_id,
            })
            
            return ServiceResult.success_result({
                'payment_intent_id': payment_intent.id,
                'client_secret': payment_intent.client_secret,
                'status': payment_intent.status,
                'amount': amount_cents,
                'currency': currency,
            })
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe lors de la création du Payment Intent: {e}", exc_info=True)
            return ServiceResult.error_result(f"Erreur Stripe: {str(e)}")
        except Exception as e:
            logger.error(f"Erreur lors de la création du Payment Intent: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la création du Payment Intent")
    
    def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> ServiceResult:
        """
        Annule un abonnement Stripe.
        """
        try:
            if not self._check_stripe_availability():
                return ServiceResult.error_result("Service Stripe non disponible")
            
            if at_period_end:
                # Annuler à la fin de la période
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                # Annuler immédiatement
                subscription = stripe.Subscription.delete(subscription_id)
            
            self.log_activity('stripe_subscription_cancelled', {
                'subscription_id': subscription_id,
                'at_period_end': at_period_end,
                'status': subscription.status,
            })
            
            return ServiceResult.success_result({
                'subscription_id': subscription.id,
                'status': subscription.status,
                'canceled_at': subscription.canceled_at,
                'cancel_at_period_end': subscription.cancel_at_period_end,
            })
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe lors de l'annulation: {e}", exc_info=True)
            return ServiceResult.error_result(f"Erreur Stripe: {str(e)}")
        except Exception as e:
            logger.error(f"Erreur lors de l'annulation Stripe: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de l'annulation")
    
    def handle_webhook(self, payload: bytes, signature: str) -> ServiceResult:
        """
        Traite un webhook Stripe.
        """
        try:
            if not self._check_stripe_availability():
                return ServiceResult.error_result("Service Stripe non disponible")
            
            # Vérifier la signature du webhook
            try:
                event = stripe.Webhook.construct_event(
                    payload, signature, self.webhook_secret
                )
            except ValueError:
                return ServiceResult.error_result("Payload invalide")
            except stripe.error.SignatureVerificationError:
                return ServiceResult.error_result("Signature invalide")
            
            # Traiter l'événement selon son type
            event_type = event['type']
            event_data = event['data']['object']
            
            self.log_activity('stripe_webhook_received', {
                'event_type': event_type,
                'event_id': event['id'],
            })
            
            # Dispatcher vers les handlers spécifiques
            handler_result = self._dispatch_webhook_event(event_type, event_data)
            
            return ServiceResult.success_result({
                'event_type': event_type,
                'event_id': event['id'],
                'processed': handler_result.success if handler_result else True,
            })
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du webhook: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors du traitement du webhook")
    
    def _dispatch_webhook_event(self, event_type: str, event_data: Dict) -> Optional[ServiceResult]:
        """
        Dispatche les événements webhook vers les handlers appropriés.
        """
        try:
            if event_type == 'invoice.payment_succeeded':
                return self._handle_invoice_payment_succeeded(event_data)
            elif event_type == 'invoice.payment_failed':
                return self._handle_invoice_payment_failed(event_data)
            elif event_type == 'customer.subscription.created':
                return self._handle_subscription_created(event_data)
            elif event_type == 'customer.subscription.updated':
                return self._handle_subscription_updated(event_data)
            elif event_type == 'customer.subscription.deleted':
                return self._handle_subscription_deleted(event_data)
            elif event_type == 'payment_intent.succeeded':
                return self._handle_payment_intent_succeeded(event_data)
            elif event_type == 'payment_intent.payment_failed':
                return self._handle_payment_intent_failed(event_data)
            else:
                logger.info(f"Événement webhook non géré: {event_type}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors du dispatch webhook {event_type}: {e}", exc_info=True)
            return ServiceResult.error_result(f"Erreur lors du traitement de {event_type}")
    
    def _handle_invoice_payment_succeeded(self, invoice_data: Dict) -> ServiceResult:
        """Gère les paiements de facture réussis."""
        try:
            subscription_id = invoice_data.get('subscription')
            if not subscription_id:
                return ServiceResult.success_result({'message': 'Pas d\'abonnement associé'})
            
            # Trouver l'abonnement local
            try:
                abonnement = Abonnement.objects.get(stripe_subscription_id=subscription_id)
            except Abonnement.DoesNotExist:
                logger.warning(f"Abonnement local introuvable pour Stripe ID: {subscription_id}")
                return ServiceResult.success_result({'message': 'Abonnement local introuvable'})
            
            # Trouver le paiement en attente
            paiement = Paiement.objects.filter(
                abonnement=abonnement,
                status='EN_ATTENTE'
            ).first()
            
            if paiement:
                # Utiliser le BillingService pour traiter le paiement
                billing_service = BillingService(user=abonnement.client, organization=abonnement.organization)
                result = billing_service.process_payment(
                    payment_id=paiement.id,
                    external_transaction_id=invoice_data.get('payment_intent'),
                    details=invoice_data
                )
                return result
            
            return ServiceResult.success_result({'message': 'Aucun paiement en attente trouvé'})
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du paiement réussi: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors du traitement du paiement réussi")
    
    def _handle_invoice_payment_failed(self, invoice_data: Dict) -> ServiceResult:
        """Gère les échecs de paiement de facture."""
        try:
            subscription_id = invoice_data.get('subscription')
            if not subscription_id:
                return ServiceResult.success_result({'message': 'Pas d\'abonnement associé'})
            
            # Trouver l'abonnement local
            try:
                abonnement = Abonnement.objects.get(stripe_subscription_id=subscription_id)
            except Abonnement.DoesNotExist:
                logger.warning(f"Abonnement local introuvable pour Stripe ID: {subscription_id}")
                return ServiceResult.success_result({'message': 'Abonnement local introuvable'})
            
            # Trouver le paiement en attente
            paiement = Paiement.objects.filter(
                abonnement=abonnement,
                status='EN_ATTENTE'
            ).first()
            
            if paiement:
                # Utiliser le BillingService pour gérer l'échec
                billing_service = BillingService(user=abonnement.client, organization=abonnement.organization)
                result = billing_service.handle_failed_payment(
                    payment_id=paiement.id,
                    error_message="Échec du paiement Stripe",
                    error_code="stripe_payment_failed"
                )
                return result
            
            return ServiceResult.success_result({'message': 'Aucun paiement en attente trouvé'})
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'échec de paiement: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors du traitement de l'échec de paiement")
    
    def _handle_subscription_created(self, subscription_data: Dict) -> ServiceResult:
        """Gère la création d'abonnement Stripe."""
        # Publier un événement pour informer les autres services
        EventBus.publish('stripe.subscription.created', {
            'stripe_subscription_id': subscription_data['id'],
            'customer_id': subscription_data['customer'],
            'status': subscription_data['status'],
        })
        return ServiceResult.success_result({'message': 'Abonnement Stripe créé'})
    
    def _handle_subscription_updated(self, subscription_data: Dict) -> ServiceResult:
        """Gère la mise à jour d'abonnement Stripe."""
        EventBus.publish('stripe.subscription.updated', {
            'stripe_subscription_id': subscription_data['id'],
            'status': subscription_data['status'],
            'cancel_at_period_end': subscription_data.get('cancel_at_period_end', False),
        })
        return ServiceResult.success_result({'message': 'Abonnement Stripe mis à jour'})
    
    def _handle_subscription_deleted(self, subscription_data: Dict) -> ServiceResult:
        """Gère la suppression d'abonnement Stripe."""
        try:
            # Trouver l'abonnement local et l'annuler
            try:
                abonnement = Abonnement.objects.get(stripe_subscription_id=subscription_data['id'])
                abonnement.cancel(reason="Abonnement annulé dans Stripe")
            except Abonnement.DoesNotExist:
                logger.warning(f"Abonnement local introuvable pour Stripe ID: {subscription_data['id']}")
            
            EventBus.publish('stripe.subscription.deleted', {
                'stripe_subscription_id': subscription_data['id'],
                'canceled_at': subscription_data.get('canceled_at'),
            })
            
            return ServiceResult.success_result({'message': 'Abonnement Stripe supprimé'})
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression d'abonnement: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la suppression d'abonnement")
    
    def _handle_payment_intent_succeeded(self, payment_intent_data: Dict) -> ServiceResult:
        """Gère les Payment Intent réussis."""
        EventBus.publish('stripe.payment_intent.succeeded', {
            'payment_intent_id': payment_intent_data['id'],
            'amount': payment_intent_data['amount'],
            'currency': payment_intent_data['currency'],
            'customer_id': payment_intent_data.get('customer'),
        })
        return ServiceResult.success_result({'message': 'Payment Intent réussi'})
    
    def _handle_payment_intent_failed(self, payment_intent_data: Dict) -> ServiceResult:
        """Gère les échecs de Payment Intent."""
        EventBus.publish('stripe.payment_intent.failed', {
            'payment_intent_id': payment_intent_data['id'],
            'amount': payment_intent_data['amount'],
            'currency': payment_intent_data['currency'],
            'customer_id': payment_intent_data.get('customer'),
            'last_payment_error': payment_intent_data.get('last_payment_error'),
        })
        return ServiceResult.success_result({'message': 'Payment Intent échoué'})
    
    def get_customer_payment_methods(self, customer_id: str) -> ServiceResult:
        """
        Récupère les moyens de paiement d'un client Stripe.
        """
        try:
            if not self._check_stripe_availability():
                return ServiceResult.error_result("Service Stripe non disponible")
            
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type='card',
            )
            
            methods_data = []
            for pm in payment_methods.data:
                methods_data.append({
                    'id': pm.id,
                    'type': pm.type,
                    'card': {
                        'last4': pm.card.last4,
                        'brand': pm.card.brand,
                        'exp_month': pm.card.exp_month,
                        'exp_year': pm.card.exp_year,
                    },
                    'created': pm.created,
                })
            
            return ServiceResult.success_result({
                'payment_methods': methods_data,
                'total_count': len(methods_data),
            })
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe lors de la récupération des moyens de paiement: {e}", exc_info=True)
            return ServiceResult.error_result(f"Erreur Stripe: {str(e)}")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des moyens de paiement: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la récupération des moyens de paiement")


class StripeWebhookHandler:
    """
    Handler spécialisé pour les webhooks Stripe.
    Utilisé dans les vues Django pour traiter les webhooks.
    """
    
    def __init__(self):
        self.stripe_service = StripeService()
    
    def handle_webhook(self, request) -> ServiceResult:
        """
        Traite une requête webhook Django.
        """
        try:
            payload = request.body
            signature = request.META.get('HTTP_STRIPE_SIGNATURE', '')
            
            if not signature:
                return ServiceResult.error_result("Signature manquante")
            
            return self.stripe_service.handle_webhook(payload, signature)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du webhook Django: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors du traitement du webhook")
