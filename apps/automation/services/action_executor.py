"""
Exécuteur d'actions pour les workflows
"""
import logging
import json
import requests
from typing import Dict, Any, Optional
from django.db import connection
from django.core.mail import send_mail
from django.conf import settings
from ..models import Integration
from .integration_service import IntegrationService

logger = logging.getLogger(__name__)


class ActionExecutor:
    """
    Exécute les différentes actions définies dans les workflows.
    """
    
    def __init__(self):
        self.integration_service = IntegrationService()
    
    def execute_action(
        self,
        action_type: str,
        params: Dict[str, Any],
        integration: Optional[Integration] = None,
        context: Dict[str, Any] = None
    ) -> Any:
        """
        Exécute une action selon son type.
        
        Args:
            action_type: Type d'action à exécuter
            params: Paramètres de l'action
            integration: Intégration à utiliser (si applicable)
            context: Contexte d'exécution
            
        Returns:
            Le résultat de l'action
        """
        context = context or {}
        
        # Mapper les types d'actions aux méthodes
        action_map = {
            'validate_data': self._validate_data,
            'database_save': self._database_save,
            'database_query': self._database_query,
            'integration_call': self._integration_call,
            'send_email': self._send_email,
            'send_webhook': self._send_webhook,
            'transform_data': self._transform_data,
            'conditional': self._conditional,
            'loop': self._loop,
            'wait': self._wait,
            'custom_code': self._custom_code,
        }
        
        action_func = action_map.get(action_type)
        
        if not action_func:
            raise ValueError(f"Type d'action inconnu: {action_type}")
        
        logger.info(f"Exécution de l'action: {action_type}")
        
        # Exécuter l'action
        result = action_func(params, integration, context)
        
        return result
    
    def _validate_data(
        self,
        params: Dict[str, Any],
        integration: Optional[Integration],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Valide des données selon un schéma.
        """
        from jsonschema import validate, ValidationError
        
        data = params.get('data', {})
        schema = params.get('schema', {})
        
        try:
            if isinstance(schema, str):
                # Si c'est un nom de schéma, le récupérer
                from apps.studio.models import DataSchema
                schema_obj = DataSchema.objects.get(id=schema)
                schema = schema_obj.fields_config
            
            validate(instance=data, schema=schema)
            
            return {
                'valid': True,
                'data': data,
            }
        except ValidationError as e:
            logger.warning(f"Validation échouée: {e.message}")
            return {
                'valid': False,
                'errors': [e.message],
                'data': data,
            }
    
    def _database_save(
        self,
        params: Dict[str, Any],
        integration: Optional[Integration],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Sauvegarde des données dans une table.
        """
        table_name = params.get('table')
        data = params.get('data', {})
        
        if not table_name:
            raise ValueError("Le paramètre 'table' est requis")
        
        try:
            # Construire la requête d'insertion
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['%s'] * len(data))
            values = list(data.values())
            
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) RETURNING id"
            
            with connection.cursor() as cursor:
                cursor.execute(query, values)
                row_id = cursor.fetchone()[0]
            
            logger.info(f"Données sauvegardées dans {table_name}, ID: {row_id}")
            
            return {
                'success': True,
                'table': table_name,
                'id': row_id,
                'data': data,
            }
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}", exc_info=True)
            raise
    
    def _database_query(
        self,
        params: Dict[str, Any],
        integration: Optional[Integration],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Exécute une requête sur la base de données.
        """
        query = params.get('query')
        query_params = params.get('params', [])
        
        if not query:
            raise ValueError("Le paramètre 'query' est requis")
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, query_params)
                
                if query.strip().upper().startswith('SELECT'):
                    columns = [col[0] for col in cursor.description]
                    results = [
                        dict(zip(columns, row))
                        for row in cursor.fetchall()
                    ]
                    
                    return {
                        'success': True,
                        'results': results,
                        'count': len(results),
                    }
                else:
                    return {
                        'success': True,
                        'affected_rows': cursor.rowcount,
                    }
        except Exception as e:
            logger.error(f"Erreur lors de la requête: {e}", exc_info=True)
            raise
    
    def _integration_call(
        self,
        params: Dict[str, Any],
        integration: Optional[Integration],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Appelle une intégration externe.
        """
        if not integration:
            raise ValueError("Une intégration est requise pour cette action")
        
        return self.integration_service.execute(integration, params, context)
    
    def _send_email(
        self,
        params: Dict[str, Any],
        integration: Optional[Integration],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Envoie un email.
        """
        to = params.get('to')
        subject = params.get('subject', 'Notification')
        message = params.get('message', '')
        from_email = params.get('from_email', settings.DEFAULT_FROM_EMAIL)
        html_message = params.get('html_message')
        
        if not to:
            raise ValueError("Le paramètre 'to' est requis")
        
        try:
            # Si on a une intégration email, l'utiliser
            if integration and integration.integration_type == 'email':
                return self.integration_service.send_email_via_integration(
                    integration, to, subject, message, html_message
                )
            
            # Sinon, utiliser le système Django par défaut
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[to] if isinstance(to, str) else to,
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Email envoyé à {to}")
            
            return {
                'success': True,
                'to': to,
                'subject': subject,
            }
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi d'email: {e}", exc_info=True)
            raise
    
    def _send_webhook(
        self,
        params: Dict[str, Any],
        integration: Optional[Integration],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Envoie un webhook HTTP.
        """
        url = params.get('url')
        method = params.get('method', 'POST').upper()
        headers = params.get('headers', {})
        data = params.get('data', {})
        timeout = params.get('timeout', 30)
        
        if not url:
            raise ValueError("Le paramètre 'url' est requis")
        
        try:
            # Ajouter les headers par défaut
            if 'Content-Type' not in headers:
                headers['Content-Type'] = 'application/json'
            
            # Faire la requête
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Méthode HTTP non supportée: {method}")
            
            response.raise_for_status()
            
            logger.info(f"Webhook envoyé à {url}, statut: {response.status_code}")
            
            return {
                'success': True,
                'status_code': response.status_code,
                'response': response.json() if response.content else None,
            }
        except requests.RequestException as e:
            logger.error(f"Erreur lors de l'envoi du webhook: {e}", exc_info=True)
            raise
    
    def _transform_data(
        self,
        params: Dict[str, Any],
        integration: Optional[Integration],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transforme des données selon des règles.
        """
        data = params.get('data', {})
        transformations = params.get('transformations', [])
        
        result = data.copy() if isinstance(data, dict) else data
        
        for transformation in transformations:
            transform_type = transformation.get('type')
            
            if transform_type == 'map':
                # Mapper des clés
                mapping = transformation.get('mapping', {})
                if isinstance(result, dict):
                    result = {mapping.get(k, k): v for k, v in result.items()}
            
            elif transform_type == 'filter':
                # Filtrer des données
                filter_func = transformation.get('filter')
                if isinstance(result, list):
                    result = [item for item in result if self._eval_filter(item, filter_func)]
            
            elif transform_type == 'format':
                # Formatter une valeur
                field = transformation.get('field')
                format_string = transformation.get('format')
                if isinstance(result, dict) and field in result:
                    result[field] = format_string.format(result[field])
        
        return {
            'success': True,
            'transformed_data': result,
        }
    
    def _conditional(
        self,
        params: Dict[str, Any],
        integration: Optional[Integration],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Exécute une logique conditionnelle.
        """
        condition = params.get('condition', {})
        if_true = params.get('if_true', {})
        if_false = params.get('if_false', {})
        
        # Évaluer la condition (simplifié)
        condition_result = self._eval_condition(condition, context)
        
        return {
            'condition_result': condition_result,
            'action': if_true if condition_result else if_false,
        }
    
    def _loop(
        self,
        params: Dict[str, Any],
        integration: Optional[Integration],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Exécute une boucle sur un ensemble de données.
        """
        items = params.get('items', [])
        action = params.get('action', {})
        
        results = []
        for item in items:
            # Créer un contexte temporaire avec l'item
            temp_context = context.copy()
            temp_context['loop_item'] = item
            
            # Exécuter l'action (simplifié - dans une vraie impl, appeler récursivement)
            results.append({'item': item, 'processed': True})
        
        return {
            'success': True,
            'results': results,
            'count': len(results),
        }
    
    def _wait(
        self,
        params: Dict[str, Any],
        integration: Optional[Integration],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Attend un certain temps.
        """
        import time
        
        seconds = params.get('seconds', 0)
        
        if seconds > 0:
            logger.info(f"Attente de {seconds} secondes")
            time.sleep(seconds)
        
        return {
            'success': True,
            'waited_seconds': seconds,
        }
    
    def _custom_code(
        self,
        params: Dict[str, Any],
        integration: Optional[Integration],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Exécute du code personnalisé (ATTENTION: Risque de sécurité).
        """
        code = params.get('code', '')
        
        if not code:
            raise ValueError("Le paramètre 'code' est requis")
        
        # ATTENTION: exec() est dangereux en production
        # Dans une vraie application, utiliser un sandbox sécurisé
        
        local_vars = {
            'context': context,
            'params': params,
            'result': None,
        }
        
        try:
            exec(code, {'__builtins__': {}}, local_vars)
            
            return {
                'success': True,
                'result': local_vars.get('result'),
            }
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du code personnalisé: {e}", exc_info=True)
            raise
    
    def _eval_filter(self, item: Any, filter_expr: Dict[str, Any]) -> bool:
        """Évalue un filtre sur un item."""
        # Implémentation simplifiée
        return True
    
    def _eval_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Évalue une condition."""
        # Implémentation simplifiée
        return True
