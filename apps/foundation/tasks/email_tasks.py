"""
Tâches Celery pour les emails du module Foundation.
"""
import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3)
def send_welcome_email(self, user_id: int):
    """
    Envoie un email de bienvenue à un nouvel utilisateur.
    
    Args:
        user_id: ID de l'utilisateur à qui envoyer l'email
    """
    try:
        user = User.objects.get(id=user_id)
        
        subject = "Bienvenue sur NoCode Platform!"
        message = f"""
Bonjour {user.get_full_name() or user.email},

Bienvenue sur NoCode Platform! Votre compte a été créé avec succès.

Vous pouvez maintenant:
- Créer des projets NoCode
- Concevoir des applications dynamiques
- Collaborer avec votre équipe

Pour commencer, connectez-vous à votre tableau de bord.

Cordialement,
L'équipe NoCode Platform
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False
        )
        
        logger.info(f"Email de bienvenue envoyé à {user.email}")
        
        return {
            'status': 'success',
            'message': f'Email de bienvenue envoyé à {user.email}',
            'user_id': user_id
        }
        
    except User.DoesNotExist:
        logger.error(f"Utilisateur {user_id} introuvable pour l'email de bienvenue")
        return {
            'status': 'error',
            'message': 'Utilisateur introuvable',
            'user_id': user_id
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email de bienvenue: {str(e)}")
        
        if self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)
            raise self.retry(exc=e, countdown=countdown)
        
        return {
            'status': 'error',
            'message': f'Échec après {self.max_retries} tentatives',
            'error': str(e)
        }


@shared_task(bind=True, max_retries=3)
def send_password_reset_email(self, user_id: int, reset_token: str):
    """
    Envoie un email de réinitialisation de mot de passe.
    
    Args:
        user_id: ID de l'utilisateur
        reset_token: Token de réinitialisation
    """
    try:
        user = User.objects.get(id=user_id)
        
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        subject = "Réinitialisation de votre mot de passe"
        message = f"""
Bonjour {user.get_full_name() or user.email},

Vous avez demandé la réinitialisation de votre mot de passe.

Cliquez sur le lien suivant pour réinitialiser votre mot de passe:
{reset_url}

Ce lien expirera dans 24 heures.

Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.

Cordialement,
L'équipe NoCode Platform
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False
        )
        
        logger.info(f"Email de réinitialisation envoyé à {user.email}")
        
        return {
            'status': 'success',
            'message': f'Email de réinitialisation envoyé à {user.email}',
            'user_id': user_id
        }
        
    except User.DoesNotExist:
        logger.error(f"Utilisateur {user_id} introuvable pour la réinitialisation")
        return {
            'status': 'error',
            'message': 'Utilisateur introuvable',
            'user_id': user_id
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email de réinitialisation: {str(e)}")
        
        if self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)
            raise self.retry(exc=e, countdown=countdown)
        
        return {
            'status': 'error',
            'message': f'Échec après {self.max_retries} tentatives',
            'error': str(e)
        }