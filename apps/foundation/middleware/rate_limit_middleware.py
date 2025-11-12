
import logging
import time
from collections import defaultdict
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.conf import settings
from ..services.event_bus import EventBus


logger = logging.getLogger(__name__)


class RateLimitMiddleware(MiddlewareMixin):

    def __init__(self, get_response):
        self.get_response = get_response
        
        self.default_limits = getattr(settings, 'RATE_LIMIT_DEFAULTS', {
            'requests_per_minute': 60,
            'requests_per_hour': 1000,
            'requests_per_day': 10000,
        })
        
        self.endpoint_limits = getattr(settings, 'RATE_LIMIT_ENDPOINTS', {
            '/api/auth/login/': {
                'requests_per_minute': 5,
                'requests_per_hour': 20,
            },
            '/api/auth/register/': {
                'requests_per_minute': 3,
                'requests_per_hour': 10,
            },
            '/api/auth/password-reset/': {
                'requests_per_minute': 2,
                'requests_per_hour': 5,
            },
            '/api/billing/payment-intent/': {
                'requests_per_minute': 10,
                'requests_per_hour': 100,
            },
        })
        
        self.exempt_paths = getattr(settings, 'RATE_LIMIT_EXEMPT_PATHS', [
            '/api/health/',
            '/api/docs/',
            '/static/',
            '/media/',
        ])
        
        super().__init__(get_response)
    
    def process_request(self, request):

        if self._should_skip_rate_limit(request):
            return None
        
        if request.method == 'OPTIONS':
            return None
        
        try:
            identifier = self._get_request_identifier(request)
            
            if self._is_rate_limited(request, identifier):
                self._log_rate_limit_exceeded(request, identifier)
                
                return JsonResponse({
                    'error': 'Trop de requêtes. Veuillez réessayer plus tard.',
                    'retry_after': 60  # secondes
                }, status=429)
            
            self._record_request(request, identifier)
            
        except Exception as e:
            logger.error(f"Erreur dans le middleware de limitation de débit: {e}")

        return None
    
    def _should_skip_rate_limit(self, request):

        path = request.path
        
        # Vérifier les chemins exemptés
        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return True
        
        # Exempter les superutilisateurs en développement
        if settings.DEBUG and hasattr(request, 'user') and request.user.is_superuser:
            return True
        
        return False
    
    def _get_request_identifier(self, request):

        # Utiliser l'ID utilisateur si authentifié
        if hasattr(request, 'user') and request.user.is_authenticated:
            return f"user:{request.user.id}"
        
        # Sinon utiliser l'IP
        ip = self._get_client_ip(request)
        return f"ip:{ip}"
    
    def _is_rate_limited(self, request, identifier):

        path = request.path
        
        # Récupérer les limites pour cet endpoint
        limits = self._get_limits_for_path(path)
        
        # Vérifier chaque limite
        for period, max_requests in limits.items():
            if self._check_limit_exceeded(identifier, path, period, max_requests):
                return True
        
        return False
    
    def _get_limits_for_path(self, path):

        for endpoint_path, endpoint_limits in self.endpoint_limits.items():
            if path.startswith(endpoint_path):
                return endpoint_limits
        
        # Utiliser les limites par défaut
        return self.default_limits
    
    def _check_limit_exceeded(self, identifier, path, period, max_requests):

        cache_key = f"rate_limit:{identifier}:{path}:{period}"
        
        current_count = cache.get(cache_key, 0)
        
        return current_count >= max_requests
    
    def _record_request(self, request, identifier):

        path = request.path
        limits = self._get_limits_for_path(path)

        for period, max_requests in limits.items():
            cache_key = f"rate_limit:{identifier}:{path}:{period}"
            
            period_seconds = self._get_period_seconds(period)
            
            try:
                current_count = cache.get(cache_key, 0)
                cache.set(cache_key, current_count + 1, period_seconds)
            except Exception as e:
                logger.error(f"Erreur lors de l'enregistrement du débit: {e}")
    
    def _get_period_seconds(self, period):
        period_map = {
            'requests_per_minute': 60,
            'requests_per_hour': 3600,
            'requests_per_day': 86400,
        }
        return period_map.get(period, 3600)
    
    def _log_rate_limit_exceeded(self, request, identifier):

        log_data = {
            'identifier': identifier,
            'path': request.path,
            'method': request.method,
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'timestamp': time.time(),
        }
        
        logger.warning(f"Limite de débit dépassée: {identifier}", extra=log_data)
        EventBus.publish('rate_limit.exceeded', log_data)
    
    def _get_client_ip(self, request):

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AdaptiveRateLimitMiddleware(MiddlewareMixin):
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):

        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
        
        try:
            trust_score = self._get_user_trust_score(request.user)

            adjusted_limits = self._adjust_limits_by_trust(trust_score)
            
            request._adaptive_rate_limits = adjusted_limits
            
        except Exception as e:
            logger.error(f"Erreur dans la limitation adaptatif: {e}")
        
        return None
    
    def _get_user_trust_score(self, user):
        score = 50  # Score de base
        
        if user.is_verified:
            score += 20
        
        if hasattr(user, 'entreprise') and user.entreprise.is_verified:
            score += 15
        
        # Ancienneté du compte
        from django.utils import timezone
        account_age_days = (timezone.now() - user.date_joined).days
        if account_age_days > 30:
            score += 10
        if account_age_days > 365:
            score += 10

        return min(100, max(0, score))
    
    def _adjust_limits_by_trust(self, trust_score):

        # Plus le score est élevé, plus les limites sont généreuses
        multiplier = 1 + (trust_score / 100)
        
        base_limits = {
            'requests_per_minute': 60,
            'requests_per_hour': 1000,
        }
        
        adjusted_limits = {}
        for period, limit in base_limits.items():
            adjusted_limits[period] = int(limit * multiplier)
        
        return adjusted_limits


class BurstRateLimitMiddleware(MiddlewareMixin):
    
    def __init__(self, get_response):
        self.get_response = get_response

        self.bucket_size = getattr(settings, 'RATE_LIMIT_BUCKET_SIZE', 100)
        self.refill_rate = getattr(settings, 'RATE_LIMIT_REFILL_RATE', 10)  # tokens par seconde
        
        super().__init__(get_response)
    
    def process_request(self, request):
        if self._should_skip_burst_limit(request):
            return None
        
        try:
            identifier = self._get_request_identifier(request)
            
            if not self._consume_token(identifier):
                return JsonResponse({
                    'error': 'Limite de débit dépassée (burst)',
                    'retry_after': 1
                }, status=429)
                
        except Exception as e:
            logger.error(f"Erreur dans la limitation burst: {e}")
        
        return None
    
    def _should_skip_burst_limit(self, request):

        return request.method == 'OPTIONS' or request.path.startswith('/static/')
    
    def _consume_token(self, identifier):

        cache_key = f"burst_bucket:{identifier}"
        
        # Récupérer l'état actuel du bucket
        bucket_data = cache.get(cache_key, {
            'tokens': self.bucket_size,
            'last_refill': time.time()
        })
        
        current_time = time.time()
        time_passed = current_time - bucket_data['last_refill']
        
        # Remplir le bucket
        tokens_to_add = int(time_passed * self.refill_rate)
        bucket_data['tokens'] = min(
            self.bucket_size,
            bucket_data['tokens'] + tokens_to_add
        )
        bucket_data['last_refill'] = current_time
        
        # Consommer un token si disponible
        if bucket_data['tokens'] > 0:
            bucket_data['tokens'] -= 1
            cache.set(cache_key, bucket_data, 3600)  # 1 heure
            return True
        
        # Sauvegarder l'état même si pas de token consommé
        cache.set(cache_key, bucket_data, 3600)
        return False
    
    def _get_request_identifier(self, request):

        if hasattr(request, 'user') and request.user.is_authenticated:
            return f"user:{request.user.id}"
        
        ip = request.META.get('REMOTE_ADDR', 'unknown')
        return f"ip:{ip}"
