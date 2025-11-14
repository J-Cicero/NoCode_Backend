"""
Tâches Celery pour la gestion   des abonnements.
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from ..models import Abonnement, Organization
from ..services.billing_service import BillingService
from ..services.event_bus import EventBus
from .email_tasks import send_billing_notification

logger = logging.getLogger(__name__)


# Tâche sync_stripe_subscription supprimée - Intégration Stripe retirée


@shared_task(bind=True, max_retries=3)
def process_failed_payment(self, payment_id):

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


# Tâche update_subscription_usage supprimée - Intégration Stripe retirée


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
