"""
Tâches Celery pour l'envoi d'emails asynchrones.
"""
import logging
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
from ..models import Organization, OrganizationInvitation, Abonnement
from ..services.event_bus import EventBus

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3)
def send_welcome_email(self, user_id):
    """
    Envoie un email de bienvenue à un nouvel utilisateur.
    """
    try:
        user = User.objects.get(id=user_id)
        
        subject = f"Bienvenue sur {settings.SITE_NAME} !"
        
        context = {
            'user': user,
            'site_name': settings.SITE_NAME,
            'site_url': settings.FRONTEND_URL,
        }
        
        html_message = render_to_string('emails/welcome.html', context)
        plain_message = render_to_string('emails/welcome.txt', context)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        EventBus.publish('email.sent', {
            'type': 'welcome',
            'user_id': user_id,
            'email': user.email,
        })
        
        logger.info(f"Email de bienvenue envoyé à {user.email}")
        return {'success': True, 'email': user.email}
        
    except User.DoesNotExist:
        logger.error(f"Utilisateur {user_id} non trouvé pour l'email de bienvenue")
        return {'success': False, 'error': 'User not found'}
    
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email de bienvenue: {e}")
        
        # Retry avec backoff exponentiel
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def send_verification_email(self, user_id, verification_token):
    """
    Envoie un email de vérification d'adresse email.
    """
    try:
        user = User.objects.get(id=user_id)
        
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        
        subject = "Vérifiez votre adresse email"
        
        context = {
            'user': user,
            'verification_url': verification_url,
            'site_name': settings.SITE_NAME,
        }
        
        html_message = render_to_string('emails/email_verification.html', context)
        plain_message = render_to_string('emails/email_verification.txt', context)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        EventBus.publish('email.sent', {
            'type': 'verification',
            'user_id': user_id,
            'email': user.email,
        })
        
        logger.info(f"Email de vérification envoyé à {user.email}")
        return {'success': True, 'email': user.email}
        
    except User.DoesNotExist:
        logger.error(f"Utilisateur {user_id} non trouvé pour l'email de vérification")
        return {'success': False, 'error': 'User not found'}
    
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email de vérification: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def send_password_reset_email(self, user_id, reset_token):
    """
    Envoie un email de réinitialisation de mot de passe.
    """
    try:
        user = User.objects.get(id=user_id)
        
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        subject = "Réinitialisation de votre mot de passe"
        
        context = {
            'user': user,
            'reset_url': reset_url,
            'site_name': settings.SITE_NAME,
        }
        
        html_message = render_to_string('emails/password_reset.html', context)
        plain_message = render_to_string('emails/password_reset.txt', context)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        EventBus.publish('email.sent', {
            'type': 'password_reset',
            'user_id': user_id,
            'email': user.email,
        })
        
        logger.info(f"Email de réinitialisation envoyé à {user.email}")
        return {'success': True, 'email': user.email}
        
    except User.DoesNotExist:
        logger.error(f"Utilisateur {user_id} non trouvé pour l'email de réinitialisation")
        return {'success': False, 'error': 'User not found'}
    
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email de réinitialisation: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def send_invitation_email(self, invitation_id):
    """
    Envoie un email d'invitation à rejoindre une organisation.
    """
    try:
        invitation = OrganizationInvitation.objects.get(id=invitation_id)
        
        invitation_url = f"{settings.FRONTEND_URL}/accept-invitation?token={invitation.token}"
        
        subject = f"Invitation à rejoindre {invitation.organization.name}"
        
        context = {
            'invitation': invitation,
            'organization': invitation.organization,
            'inviter': invitation.invited_by,
            'invitation_url': invitation_url,
            'site_name': settings.SITE_NAME,
        }
        
        html_message = render_to_string('emails/organization_invitation.html', context)
        plain_message = render_to_string('emails/organization_invitation.txt', context)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.email],
            fail_silently=False,
        )
        
        # Marquer l'invitation comme envoyée
        invitation.status = 'SENT'
        invitation.save()
        
        EventBus.publish('email.sent', {
            'type': 'invitation',
            'invitation_id': invitation_id,
            'email': invitation.email,
            'organization_id': invitation.organization.id,
        })
        
        logger.info(f"Email d'invitation envoyé à {invitation.email}")
        return {'success': True, 'email': invitation.email}
        
    except OrganizationInvitation.DoesNotExist:
        logger.error(f"Invitation {invitation_id} non trouvée")
        return {'success': False, 'error': 'Invitation not found'}
    
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email d'invitation: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def send_billing_notification(self, notification_type, organization_id, **kwargs):
    """
    Envoie des notifications de facturation.
    """
    try:
        organization = Organization.objects.get(id=organization_id)
        
        # Récupérer les emails des administrateurs
        admin_emails = list(
            organization.members.filter(
                organizationmember__role__in=['OWNER', 'ADMIN'],
                organizationmember__status='ACTIVE'
            ).values_list('email', flat=True)
        )
        
        if not admin_emails:
            logger.warning(f"Aucun admin trouvé pour l'organisation {organization_id}")
            return {'success': False, 'error': 'No admin emails found'}
        
        # Préparer le contexte selon le type de notification
        context = {
            'organization': organization,
            'site_name': settings.SITE_NAME,
            **kwargs
        }
        
        # Déterminer le template et le sujet
        templates = {
            'payment_failed': {
                'subject': 'Échec de paiement',
                'template': 'emails/billing/payment_failed',
            },
            'subscription_canceled': {
                'subject': 'Abonnement annulé',
                'template': 'emails/billing/subscription_canceled',
            },
            'trial_ending': {
                'subject': 'Fin de période d\'essai',
                'template': 'emails/billing/trial_ending',
            },
            'invoice_ready': {
                'subject': 'Nouvelle facture disponible',
                'template': 'emails/billing/invoice_ready',
            },
        }
        
        if notification_type not in templates:
            logger.error(f"Type de notification inconnu: {notification_type}")
            return {'success': False, 'error': 'Unknown notification type'}
        
        template_info = templates[notification_type]
        
        html_message = render_to_string(f"{template_info['template']}.html", context)
        plain_message = render_to_string(f"{template_info['template']}.txt", context)
        
        send_mail(
            subject=template_info['subject'],
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=False,
        )
        
        EventBus.publish('email.sent', {
            'type': f'billing_{notification_type}',
            'organization_id': organization_id,
            'recipients': admin_emails,
        })
        
        logger.info(f"Notification de facturation {notification_type} envoyée à {len(admin_emails)} destinataires")
        return {'success': True, 'recipients': len(admin_emails)}
        
    except Organization.DoesNotExist:
        logger.error(f"Organisation {organization_id} non trouvée")
        return {'success': False, 'error': 'Organization not found'}
    
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de la notification de facturation: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}
