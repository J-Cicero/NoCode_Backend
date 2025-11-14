"""
Service Email Professionnel pour Foundation.
Envoie d'emails avec templates HTML/CSS et couleurs africaines.
"""

import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service simple pour l'envoi d'emails professionnels."""
    
    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
        self.site_name = getattr(settings, 'SITE_NAME', 'Notre Plateforme')
        self.frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    
    def send(self, template_name, to_email, context=None, **kwargs):
        """
        Envoie un email avec template HTML/CSS.
        
        Args:
            template_name: Nom du template (ex: 'welcome', 'welcome_owner')
            to_email: Email du destinataire
            context: Données pour le template
            **kwargs: Options supplémentaires pour send_mail
        
        Returns:
            dict: {'success': True/False, 'email': to_email, 'error': None}
        """
        try:
            context = context or {}
            
            # Ajouter le contexte global
            context.update({
                'site_name': self.site_name,
                'frontend_url': self.frontend_url,
                'current_year': 2024,
                'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@exemple.com'),
            })
            
            # Rendre les templates HTML et texte
            html_message = render_to_string(f'emails/{template_name}.html', context)
            plain_message = render_to_string(f'emails/{template_name}.txt', context)
            
            # Sujet de l'email
            subject = context.get('subject', f'Notification de {self.site_name}')
            
            # Envoyer l'email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=self.from_email,
                recipient_list=[to_email],
                html_message=html_message,
                fail_silently=False,
                **kwargs
            )
            
            logger.info(f"Email '{template_name}' envoyé avec succès à {to_email}")
            return {
                'success': True, 
                'email': to_email, 
                'template': template_name
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email '{template_name}' à {to_email}: {e}")
            return {
                'success': False, 
                'error': str(e), 
                'email': to_email,
                'template': template_name
            }


# Instance globale du service
email_service = EmailService()
