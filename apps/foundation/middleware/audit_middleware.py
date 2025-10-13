
import logging
import json
import time
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from ..services.event_bus import EventBus


logger = logging.getLogger(__name__)
User = get_user_model()


class AuditMiddleware(MiddlewareMixin):
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        request._audit_start_time = time.time()
        
        if self._should_skip_audit(request):
            return None
        
        request._audit_data = {
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET),
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'timestamp': time.time(),
        }
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            request._audit_data.update({
                'user_id': request.user.id,
                'user_email': request.user.email,
                'user_type': request.user.user_type,
            })
        
        if hasattr(request, 'current_organization'):
            request._audit_data.update({
                'organization_id': request.current_organization.id,
                'organization_name': request.current_organization.name,
            })
        
        if self._is_sensitive_action(request):
            self._audit_sensitive_data(request)
        
        return None
    
    def process_response(self, request, response):

        if not hasattr(request, '_audit_data'):
            return response
        
        try:
            duration = time.time() - request._audit_start_time
            
            request._audit_data.update({
                'status_code': response.status_code,
                'duration_ms': round(duration * 1000, 2),
                'response_size': len(response.content) if hasattr(response, 'content') else 0,
            })
            
            if response.status_code >= 500:
                log_level = 'error'
            elif response.status_code >= 400:
                log_level = 'warning'
            else:
                log_level = 'info'
            
            self._log_audit(request._audit_data, log_level)

            EventBus.publish('audit.request', request._audit_data)
            
            self._audit_specific_actions(request, response)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'audit: {e}", exc_info=True)
        
        return response
    
    def _should_skip_audit(self, request):

        # Chemins à ignorer
        skip_paths = [
            '/api/health/',
            '/api/docs/',
            '/static/',
            '/media/',
            '/favicon.ico',
        ]
        
        path = request.path
        

        for skip_path in skip_paths:
            if path.startswith(skip_path):
                return True
        
        if request.method == 'OPTIONS':
            return True
        
        if request.method == 'GET' and any(path.startswith(p) for p in ['/api/users/me/', '/api/organizations/']):
            return True
        
        return False
    
    def _is_sensitive_action(self, request):

        sensitive_patterns = [
            '/api/auth/login/',
            '/api/auth/register/',
            '/api/auth/password-change/',
            '/api/auth/password-reset/',
            '/api/billing/',
            '/api/organizations/',
            '/api/verification/',
            '/api/users/',
        ]
        
        path = request.path

        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            for pattern in sensitive_patterns:
                if path.startswith(pattern):
                    return True
        
        return False
    
    def _audit_sensitive_data(self, request):
        try:
            if request.content_type == 'application/json':
                try:
                    body = json.loads(request.body)
                    sensitive_fields = ['password', 'password_confirmation', 'token', 'secret']
                    for field in sensitive_fields:
                        if field in body:
                            body[field] = '***MASKED***'
                    
                    request._audit_data['request_body'] = body
                except json.JSONDecodeError:
                    pass
            
        except Exception as e:
            logger.error(f"Erreur lors de l'audit des données sensibles: {e}")
    
    def _audit_specific_actions(self, request, response):

        try:
            path = request.path
            method = request.method
            
            if path == '/api/auth/login/' and method == 'POST':
                if response.status_code == 200:
                    EventBus.publish('audit.login_success', {
                        'user_id': request._audit_data.get('user_id'),
                        'ip_address': request._audit_data.get('ip_address'),
                        'user_agent': request._audit_data.get('user_agent'),
                    })
                else:
                    EventBus.publish('audit.login_failed', {
                        'ip_address': request._audit_data.get('ip_address'),
                        'user_agent': request._audit_data.get('user_agent'),
                        'status_code': response.status_code,
                    })
            
            elif '/api/organizations/' in path and method == 'POST':
                if response.status_code == 201:
                    EventBus.publish('audit.organization_created', request._audit_data)
            
            elif '/api/billing/' in path and method in ['POST', 'PUT', 'PATCH']:
                EventBus.publish('audit.billing_modified', request._audit_data)
            
            elif '/api/verification/' in path and method in ['POST', 'PUT', 'PATCH']:
                EventBus.publish('audit.verification_action', request._audit_data)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'audit des actions spécifiques: {e}")
    
    def _log_audit(self, audit_data, level='info'):

        message = f"API Request: {audit_data.get('method')} {audit_data.get('path')} - {audit_data.get('status_code')} ({audit_data.get('duration_ms')}ms)"
        
        if level == 'error':
            logger.error(message, extra={'audit_data': audit_data})
        elif level == 'warning':
            logger.warning(message, extra={'audit_data': audit_data})
        else:
            logger.info(message, extra={'audit_data': audit_data})
    
    def _get_client_ip(self, request):

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityAuditMiddleware(MiddlewareMixin):
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.suspicious_patterns = [
            'script',
            'javascript:',
            '<script',
            'eval(',
            'union select',
            'drop table',
            '../',
            '..\\',
        ]
        super().__init__(get_response)
    
    def process_request(self, request):

        try:
            # Vérifier les tentatives d'injection
            if self._detect_injection_attempt(request):
                self._log_security_incident(request, 'injection_attempt')
                return JsonResponse({
                    'error': 'Requête suspecte détectée'
                }, status=400)
            
            # Vérifier les tentatives de brute force
            if self._detect_brute_force(request):
                self._log_security_incident(request, 'brute_force_attempt')
                # Ne pas bloquer immédiatement, juste enregistrer
            
            # Vérifier les tentatives d'accès non autorisé
            if self._detect_unauthorized_access(request):
                self._log_security_incident(request, 'unauthorized_access_attempt')
            
        except Exception as e:
            logger.error(f"Erreur dans l'audit de sécurité: {e}")
        
        return None
    
    def _detect_injection_attempt(self, request):

        # Vérifier les paramètres GET
        for key, value in request.GET.items():
            if any(pattern in value.lower() for pattern in self.suspicious_patterns):
                return True
        
        # Vérifier le body pour les requêtes POST/PUT
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = request.body.decode('utf-8').lower()
                if any(pattern in body for pattern in self.suspicious_patterns):
                    return True
            except:
                pass
        
        return False
    
    def _detect_brute_force(self, request):

        if request.path == '/api/auth/login/' and request.method == 'POST':
            # Ici, on pourrait implémenter une logique de détection basée sur l'IP
            # et le nombre de tentatives récentes
            return False  # Placeholder
        
        return False
    
    def _detect_unauthorized_access(self, request):

        if not hasattr(request, 'user') or not request.user.is_authenticated:
            protected_paths = ['/api/users/', '/api/organizations/', '/api/billing/']
            if any(request.path.startswith(path) for path in protected_paths):
                return True
        
        return False
    
    def _log_security_incident(self, request, incident_type):

        incident_data = {
            'incident_type': incident_type,
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'path': request.path,
            'method': request.method,
            'timestamp': time.time(),
        }
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            incident_data['user_id'] = request.user.id
        
        logger.warning(f"Incident de sécurité détecté: {incident_type}", extra=incident_data)
        EventBus.publish('security.incident', incident_data)
    
    def _get_client_ip(self, request):

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class PerformanceAuditMiddleware(MiddlewareMixin):

    def __init__(self, get_response):
        self.get_response = get_response
        self.slow_request_threshold = 2.0  # 2 secondes
        super().__init__(get_response)
    
    def process_request(self, request):

        request._perf_start = time.time()
        return None
    
    def process_response(self, request, response):

        if not hasattr(request, '_perf_start'):
            return response
        
        try:
            duration = time.time() - request._perf_start

            if duration > self.slow_request_threshold:
                self._log_slow_request(request, response, duration)
            
            self._record_performance_metrics(request, response, duration)
            
        except Exception as e:
            logger.error(f"Erreur dans l'audit de performance: {e}")
        
        return response
    
    def _log_slow_request(self, request, response, duration):

        perf_data = {
            'path': request.path,
            'method': request.method,
            'duration': duration,
            'status_code': response.status_code,
            'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
        }
        
        logger.warning(f"Requête lente détectée: {duration:.2f}s", extra=perf_data)
        EventBus.publish('performance.slow_request', perf_data)
    
    def _record_performance_metrics(self, request, response, duration):

        metrics = {
            'path': request.path,
            'method': request.method,
            'duration': duration,
            'status_code': response.status_code,
            'response_size': len(response.content) if hasattr(response, 'content') else 0,
            'timestamp': time.time(),
        }
        
        # Publier les métriques pour collecte
        EventBus.publish('performance.metrics', metrics)
