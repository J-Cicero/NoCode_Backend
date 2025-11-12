
import logging
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from ..services.event_bus import EventBus


logger = logging.getLogger(__name__)
User = get_user_model()


class JWTAuthenticationMiddleware(MiddlewareMixin):

    
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()
        super().__init__(get_response)
    
    def process_request(self, request):

        if self._should_skip_auth(request):
            return None
        
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None
        
        try:
            auth_result = self.jwt_auth.authenticate(request)
            
            if auth_result:
                user, token = auth_result
                
                if not user.is_active:
                    logger.warning(f"Tentative de connexion avec un compte inactif: {user.email}")
                    return JsonResponse({
                        'error': 'Compte utilisateur inactif'
                    }, status=401)
                
                request.user = user
                request.auth = token
                
                self._update_last_activity(user, request)
                
                EventBus.publish('user.activity', {
                    'user_id': user.id,
                    'action': 'api_request',
                    'path': request.path,
                    'method': request.method,
                    'ip_address': self._get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                })
                
        except InvalidToken as e:
            logger.warning(f"Token JWT invalide: {e}")
            return JsonResponse({
                'error': 'Token d\'authentification invalide'
            }, status=401)
        
        except TokenError as e:
            logger.warning(f"Erreur de token JWT: {e}")
            return JsonResponse({
                'error': 'Erreur d\'authentification'
            }, status=401)
        
        except Exception as e:
            logger.error(f"Erreur lors de l'authentification JWT: {e}", exc_info=True)
            return JsonResponse({
                'error': 'Erreur interne d\'authentification'
            }, status=500)
        
        return None
    
    def _should_skip_auth(self, request):

        # Chemins qui n'ont pas besoin d'authentification
        skip_paths = [
            '/api/auth/login/',
            '/api/auth/register/',
            '/api/auth/password-reset/',
            '/api/auth/password-reset-confirm/',
            '/api/auth/email-verify/',
            '/api/health/',
            '/api/docs/',
            '/admin/',
            '/static/',
            '/media/',
        ]
        
        path = request.path
        
        # Vérifier les chemins exacts
        if path in skip_paths:
            return True
        
        # Vérifier les préfixes
        for skip_path in skip_paths:
            if path.startswith(skip_path):
                return True
        
        # Ignorer les requêtes OPTIONS (CORS preflight)
        if request.method == 'OPTIONS':
            return True
        
        return False
    
    def _update_last_activity(self, user, request):
        """
        Met à jour la dernière activité de l'utilisateur.
        """
        try:
            from django.utils import timezone
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la dernière activité: {e}")
    
    def _get_client_ip(self, request):

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class TokenBlacklistMiddleware(MiddlewareMixin):
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):

        if not hasattr(request, 'auth') or not request.auth:
            return None
        
        try:
            from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
            from rest_framework_simplejwt.tokens import UntypedToken
            
            untyped_token = UntypedToken(str(request.auth))
            jti = untyped_token.get('jti')
            
            if BlacklistedToken.objects.filter(token__jti=jti).exists():
                logger.warning(f"Tentative d'utilisation d'un token blacklisté: {jti}")
                return JsonResponse({
                    'error': 'Token révoqué'
                }, status=401)
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de blacklist: {e}")
        return None


class UserContextMiddleware(MiddlewareMixin):
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):

        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
        
        try:
            user = request.user
            request.user_type = user.user_type

            if user.user_type == 'CLIENT':
                try:
                    request.client_profile = user.client
                except:
                    request.client_profile = None
            
            elif user.user_type == 'ENTREPRISE':
                try:
                    request.entreprise_profile = user.entreprise
                    request.is_verified_entreprise = user.entreprise.is_verified
                except:
                    request.entreprise_profile = None
                    request.is_verified_entreprise = False
            
            from ..models import OrganizationMember
            user_organizations = OrganizationMember.objects.filter(
                user=user,
                status='ACTIVE'
            ).select_related('organization').values_list('organization_id', flat=True)
            
            request.user_organizations = list(user_organizations)
            
            request.user_permissions = {
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'is_verified': getattr(request, 'is_verified_entreprise', False),
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enrichissement du contexte utilisateur: {e}")
        
        return None


class SecurityHeadersMiddleware(MiddlewareMixin):
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_response(self, request, response):

        # En-têtes de sécurité
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Content-Security-Policy': "default-src 'self'",
        }
        
        for header, value in security_headers.items():
            if header not in response:
                response[header] = value
        
        return response
