"""
Tâches Celery pour la gestion de la facturation et des abonnements.
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from ..models import Abonnement, Paiement, Facture, Organization
from ..services.stripe_service import StripeService
from ..services.billing_service import BillingService
from ..services.event_bus import EventBus
from .email_tasks import send_billing_notification

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def sync_stripe_subscription(self, subscription_id):
    """
    Synchronise un abonnement avec Stripe.
    """
    try:
        abonnement = Abonnement.objects.get(id=subscription_id)
        stripe_service = StripeService()
        
        # Récupérer les données Stripe
        result = stripe_service.get_subscription(abonnement.stripe_subscription_id)
        
        if not result['success']:
            logger.error(f"Erreur lors de la récupération de l'abonnement Stripe: {result['error']}")
            return {'success': False, 'error': result['error']}
        
        stripe_subscription = result['subscription']
        
        # Mettre à jour l'abonnement local
        abonnement.status = stripe_service._map_subscription_status(stripe_subscription['status'])
        abonnement.date_fin = stripe_service._timestamp_to_datetime(stripe_subscription['current_period_end'])
        
        if stripe_subscription.get('trial_end'):
            abonnement.trial_end = stripe_service._timestamp_to_datetime(stripe_subscription['trial_end'])
        
        abonnement.save()
        
        EventBus.publish('subscription.synced', {
            'subscription_id': subscription_id,
            'organization_id': abonnement.organization.id,
            'status': abonnement.status,
        })
        
        logger.info(f"Abonnement {subscription_id} synchronisé avec Stripe")
        return {'success': True, 'status': abonnement.status}
        
    except Abonnement.DoesNotExist:
        logger.error(f"Abonnement {subscription_id} non trouvé")
        return {'success': False, 'error': 'Subscription not found'}
    
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation de l'abonnement: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def process_failed_payment(self, payment_id):
    """
    Traite un paiement échoué.
    """
    try:
        paiement = Paiement.objects.get(id=payment_id)
        
        # Envoyer une notification
        send_billing_notification.delay(
            'payment_failed',
            paiement.organization.id,
            payment_amount=paiement.montant,
            payment_date=paiement.date_creation,
        )
        
        # Marquer l'organisation comme ayant des problèmes de paiement
        organization = paiement.organization
        organization.payment_issues = True
        organization.save()
        
        EventBus.publish('payment.failed_processed', {
            'payment_id': payment_id,
            'organization_id': organization.id,
        })
        
        logger.info(f"Paiement échoué {payment_id} traité")
        return {'success': True}
        
    except Paiement.DoesNotExist:
        logger.error(f"Paiement {payment_id} non trouvé")
        return {'success': False, 'error': 'Payment not found'}
    
    except Exception as e:
        logger.error(f"Erreur lors du traitement du paiement échoué: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def generate_invoice(self, organization_id, period_start, period_end):
    """
    Génère une facture pour une organisation.
    """
    try:
        organization = Organization.objects.get(id=organization_id)
        billing_service = BillingService()
        
        # Générer la facture
        result = billing_service.generate_invoice(
            organization_id,
            period_start,
            period_end
        )
        
        if not result.success:
            logger.error(f"Erreur lors de la génération de facture: {result.error}")
            return {'success': False, 'error': result.error}
        
        facture = result.data['facture']
        
        # Envoyer une notification
        send_billing_notification.delay(
            'invoice_ready',
            organization_id,
            invoice_number=facture.numero,
            invoice_amount=facture.montant_ttc,
        )
        
        EventBus.publish('invoice.generated', {
            'invoice_id': facture.id,
            'organization_id': organization_id,
            'amount': facture.montant_ttc,
        })
        
        logger.info(f"Facture générée pour l'organisation {organization_id}")
        return {'success': True, 'invoice_id': facture.id}
        
    except Organization.DoesNotExist:
        logger.error(f"Organisation {organization_id} non trouvée")
        return {'success': False, 'error': 'Organization not found'}
    
    except Exception as e:
        logger.error(f"Erreur lors de la génération de facture: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def send_payment_reminder(self, invoice_id):
    """
    Envoie un rappel de paiement pour une facture.
    """
    try:
        facture = Facture.objects.get(id=invoice_id)
        
        # Vérifier que la facture est en retard
        if facture.status != 'OVERDUE':
            logger.info(f"Facture {invoice_id} n'est pas en retard, rappel ignoré")
            return {'success': True, 'skipped': True}
        
        # Envoyer le rappel
        send_billing_notification.delay(
            'payment_reminder',
            facture.organization.id,
            invoice_number=facture.numero,
            invoice_amount=facture.montant_ttc,
            due_date=facture.date_echeance,
        )
        
        # Marquer le rappel comme envoyé
        facture.reminder_sent = True
        facture.save()
        
        EventBus.publish('payment.reminder_sent', {
            'invoice_id': invoice_id,
            'organization_id': facture.organization.id,
        })
        
        logger.info(f"Rappel de paiement envoyé pour la facture {invoice_id}")
        return {'success': True}
        
    except Facture.DoesNotExist:
        logger.error(f"Facture {invoice_id} non trouvée")
        return {'success': False, 'error': 'Invoice not found'}
    
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du rappel: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def update_subscription_usage(self, subscription_id, usage_data):
    """
    Met à jour l'usage d'un abonnement.
    """
    try:
        abonnement = Abonnement.objects.get(id=subscription_id)
        stripe_service = StripeService()
        
        # Rapporter l'usage à Stripe
        result = stripe_service.report_usage(
            abonnement.stripe_subscription_id,
            usage_data['quantity'],
            usage_data.get('timestamp')
        )
        
        if not result['success']:
            logger.error(f"Erreur lors du rapport d'usage: {result['error']}")
            return {'success': False, 'error': result['error']}
        
        EventBus.publish('subscription.usage_updated', {
            'subscription_id': subscription_id,
            'organization_id': abonnement.organization.id,
            'usage': usage_data,
        })
        
        logger.info(f"Usage mis à jour pour l'abonnement {subscription_id}")
        return {'success': True}
        
    except Abonnement.DoesNotExist:
        logger.error(f"Abonnement {subscription_id} non trouvé")
        return {'success': False, 'error': 'Subscription not found'}
    
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de l'usage: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task
def check_trial_endings():
    """
    Vérifie les abonnements dont la période d'essai se termine bientôt.
    """
    try:
        # Chercher les abonnements dont l'essai se termine dans 3 jours
        trial_ending_date = timezone.now() + timedelta(days=3)
        
        abonnements = Abonnement.objects.filter(
            status='TRIAL',
            trial_end__lte=trial_ending_date,
            trial_end__gte=timezone.now(),
        )
        
        for abonnement in abonnements:
            send_billing_notification.delay(
                'trial_ending',
                abonnement.organization.id,
                trial_end_date=abonnement.trial_end,
                plan_name=abonnement.type_abonnement.nom,
            )
        
        logger.info(f"Vérification des fins d'essai: {abonnements.count()} notifications envoyées")
        return {'success': True, 'notifications_sent': abonnements.count()}
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des fins d'essai: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def check_overdue_invoices():
    """
    Vérifie les factures en retard et envoie des rappels.
    """
    try:
        # Chercher les factures en retard sans rappel envoyé
        overdue_invoices = Facture.objects.filter(
            status='OVERDUE',
            reminder_sent=False,
            date_echeance__lt=timezone.now() - timedelta(days=1),
        )
        
        for facture in overdue_invoices:
            send_payment_reminder.delay(facture.id)
        
        logger.info(f"Vérification des factures en retard: {overdue_invoices.count()} rappels programmés")
        return {'success': True, 'reminders_sent': overdue_invoices.count()}
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des factures en retard: {e}")
        return {'success': False, 'error': str(e)}
