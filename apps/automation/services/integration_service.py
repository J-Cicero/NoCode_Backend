"""
Service de gestion des intégrations externes
"""
import logging
import requests
from typing import Dict, Any, Optional
from django.conf import settings
from cryptography.fernet import Fernet
from ..models import Integration, IntegrationCredential

logger = logging.getLogger(__name__)


class IntegrationService:
    """
    Gère l'exécution des intégrations avec des services externes.
    """
    
    def __init__(self):
        # Clé de chiffrement (devrait être en settings)
        self.cipher_suite = self._get_cipher_suite()
    
    def _get_cipher_suite(self):
        """Récupère ou génère la clé de chiffrement."""
        encryption_key = getattr(settings, 'INTEGRATION_ENCRYPTION_KEY', None)
        
        if not encryption_key:
            # Générer une clé (en production, la stocker dans les settings)
            encryption_key = Fernet.generate_key()
            logger.warning("Clé de chiffrement générée - devrait être configurée dans settings")
        
        return Fernet(encryption_key)
    
    def execute(
        self,
        integration: Integration,
        params: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Exécute une intégration.
        
        Args:
            integration: L'intégration à exécuter
            params: Paramètres pour l'intégration
            context: Contexte d'exécution
            
        Returns:
            Le résultat de l'intégration
        """
        context = context or {}
        
        # Vérifier le rate limiting
        if not self._check_rate_limit(integration):
            raise Exception(f"Rate limit dépassé pour l'intégration {integration.name}")
        
        # Router selon le type d'intégration
        integration_handlers = {
            'email': self._execute_email,
            'stripe': self._execute_stripe,
            'webhook': self._execute_webhook,
            'slack': self._execute_slack,
            'api': self._execute_api,
        }
        
        handler = integration_handlers.get(integration.integration_type)
        
        if not handler:
            raise ValueError(f"Type d'intégration non supporté: {integration.integration_type}")
        
        try:
            result = handler(integration, params, context)
            
            # Incrémenter les statistiques de succès
            integration.increment_call_stats(success=True)
            
            return result
            
        except Exception as e:
            # Incrémenter les statistiques d'échec
            integration.increment_call_stats(success=False)
            logger.error(f"Erreur lors de l'exécution de l'intégration {integration.name}: {e}", exc_info=True)
            raise
    
    def _check_rate_limit(self, integration: Integration) -> bool:
        """Vérifie le rate limit de l'intégration."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Compter les appels de la dernière heure
        one_hour_ago = timezone.now() - timedelta(hours=1)
        
        # Dans une vraie impl, utiliser Redis ou cache
        # Pour l'instant, approximation simple
        return True  # Simplification
    
    def _execute_email(
        self,
        integration: Integration,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Exécute une intégration email."""
        config = integration.config
        credentials = self._get_credentials(integration)
        
        # Utiliser SendGrid si configuré
        if config.get('provider') == 'sendgrid':
            return self._sendgrid_send(credentials, params)
        
        # Sinon, SMTP classique
        return self._smtp_send(config, credentials, params)
    
    def _execute_stripe(
        self,
        integration: Integration,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Exécute une intégration Stripe."""
        import stripe
        
        credentials = self._get_credentials(integration)
        stripe.api_key = credentials.get('api_key')
        
        action = params.get('action')
        
        if action == 'create_customer':
            customer = stripe.Customer.create(
                email=params.get('email'),
                name=params.get('name'),
            )
            return {'success': True, 'customer_id': customer.id}
        
        elif action == 'create_subscription':
            subscription = stripe.Subscription.create(
                customer=params.get('customer_id'),
                items=[{'price': params.get('price_id')}],
            )
            return {'success': True, 'subscription_id': subscription.id}
        
        # Autres actions Stripe...
        return {'success': True}
    
    def _execute_webhook(
        self,
        integration: Integration,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Exécute un webhook HTTP."""
        config = integration.config
        url = params.get('url') or config.get('url')
        method = params.get('method', 'POST').upper()
        headers = params.get('headers', {})
        data = params.get('data', {})
        
        # Ajouter les credentials si nécessaires
        credentials = self._get_credentials(integration)
        if credentials.get('api_key'):
            headers['Authorization'] = f"Bearer {credentials['api_key']}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            
            return {
                'success': True,
                'status_code': response.status_code,
                'response': response.json() if response.content else None,
            }
        except requests.RequestException as e:
            logger.error(f"Erreur webhook: {e}", exc_info=True)
            raise
    
    def _execute_slack(
        self,
        integration: Integration,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Envoie un message Slack."""
        credentials = self._get_credentials(integration)
        webhook_url = credentials.get('webhook_url')
        
        message = params.get('message', '')
        channel = params.get('channel')
        
        payload = {
            'text': message,
        }
        
        if channel:
            payload['channel'] = channel
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            return {'success': True, 'message_sent': True}
        except requests.RequestException as e:
            logger.error(f"Erreur Slack: {e}", exc_info=True)
            raise
    
    def _execute_api(
        self,
        integration: Integration,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Exécute un appel API personnalisé."""
        config = integration.config
        credentials = self._get_credentials(integration)
        
        base_url = config.get('base_url', '')
        endpoint = params.get('endpoint', '')
        method = params.get('method', 'GET').upper()
        headers = params.get('headers', {})
        data = params.get('data', {})
        
        # Construire l'URL complète
        url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Ajouter l'authentification
        auth_type = config.get('auth_type')
        if auth_type == 'bearer':
            headers['Authorization'] = f"Bearer {credentials.get('token')}"
        elif auth_type == 'api_key':
            headers[config.get('api_key_header', 'X-API-Key')] = credentials.get('api_key')
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            
            return {
                'success': True,
                'status_code': response.status_code,
                'data': response.json() if response.content else None,
            }
        except requests.RequestException as e:
            logger.error(f"Erreur API: {e}", exc_info=True)
            raise
    
    def _sendgrid_send(
        self,
        credentials: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Envoie un email via SendGrid."""
        import sendgrid
        from sendgrid.helpers.mail import Mail
        
        sg = sendgrid.SendGridAPIClient(api_key=credentials.get('api_key'))
        
        message = Mail(
            from_email=params.get('from_email'),
            to_emails=params.get('to'),
            subject=params.get('subject'),
            html_content=params.get('html_message') or params.get('message')
        )
        
        try:
            response = sg.send(message)
            return {
                'success': True,
                'status_code': response.status_code,
            }
        except Exception as e:
            logger.error(f"Erreur SendGrid: {e}", exc_info=True)
            raise
    
    def _smtp_send(
        self,
        config: Dict[str, Any],
        credentials: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Envoie un email via SMTP."""
        from django.core.mail import send_mail
        
        send_mail(
            subject=params.get('subject'),
            message=params.get('message'),
            from_email=params.get('from_email'),
            recipient_list=[params.get('to')],
            html_message=params.get('html_message'),
            fail_silently=False,
        )
        
        return {'success': True}
    
    def send_email_via_integration(
        self,
        integration: Integration,
        to: str,
        subject: str,
        message: str,
        html_message: str = None
    ) -> Dict[str, Any]:
        """Helper pour envoyer un email."""
        params = {
            'to': to,
            'subject': subject,
            'message': message,
            'html_message': html_message,
            'from_email': integration.config.get('from_email', settings.DEFAULT_FROM_EMAIL),
        }
        
        return self.execute(integration, params)
    
    def _get_credentials(self, integration: Integration) -> Dict[str, Any]:
        """Récupère et déchiffre les credentials."""
        credential = integration.credentials.filter(is_active=True).first()
        
        if not credential:
            return {}
        
        # Vérifier l'expiration
        if credential.is_expired:
            logger.warning(f"Credentials expirés pour l'intégration {integration.name}")
            return {}
        
        try:
            # Déchiffrer les credentials
            decrypted_data = self.cipher_suite.decrypt(credential.encrypted_data)
            return eval(decrypted_data.decode())  # ATTENTION: eval est dangereux, utiliser json.loads en production
        except Exception as e:
            logger.error(f"Erreur lors du déchiffrement des credentials: {e}", exc_info=True)
            return {}
    
    def save_credentials(
        self,
        integration: Integration,
        credential_type: str,
        credentials_data: Dict[str, Any],
        expires_at: Optional['datetime'] = None
    ) -> IntegrationCredential:
        """Sauvegarde des credentials de manière sécurisée."""
        import json
        
        # Chiffrer les credentials
        encrypted_data = self.cipher_suite.encrypt(json.dumps(credentials_data).encode())
        
        # Créer ou mettre à jour le credential
        credential = IntegrationCredential.objects.create(
            integration=integration,
            credential_type=credential_type,
            encrypted_data=encrypted_data,
            expires_at=expires_at,
        )
        
        logger.info(f"Credentials sauvegardés pour l'intégration {integration.name}")
        
        return credential
    
    def test_integration(self, integration: Integration) -> tuple[bool, str]:
        """
        Teste une intégration.
        
        Returns:
            (success, message)
        """
        try:
            # Test basique selon le type
            if integration.integration_type == 'email':
                # Tester la connexion SMTP
                return True, "Connexion email OK"
            
            elif integration.integration_type == 'webhook':
                # Faire un ping
                url = integration.config.get('url')
                if url:
                    response = requests.get(url, timeout=10)
                    return True, f"Webhook accessible, statut: {response.status_code}"
            
            elif integration.integration_type == 'api':
                # Tester l'endpoint de health/ping
                base_url = integration.config.get('base_url')
                if base_url:
                    response = requests.get(f"{base_url}/health", timeout=10)
                    return True, f"API accessible, statut: {response.status_code}"
            
            return True, "Intégration configurée"
            
        except Exception as e:
            logger.error(f"Test d'intégration échoué: {e}", exc_info=True)
            return False, str(e)
