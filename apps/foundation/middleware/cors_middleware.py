
import logging
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger(__name__)

class CORSMiddleware(MiddlewareMixin):
    
    def __init__(self, get_response):
        self.get_response = get_response

        self.allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [
            'http://localhost:3000',
            'http://localhost:8080',
            'https://app.nocode.com',
        ])
        
        self.allowed_methods = getattr(settings, 'CORS_ALLOWED_METHODS', [
            'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'
        ])
        
        self.allowed_headers = getattr(settings, 'CORS_ALLOWED_HEADERS', [
            'accept',
            'accept-encoding',
            'authorization',
            'content-type',
            'dnt',
            'origin',
            'user-agent',
            'x-csrftoken',
            'x-requested-with',
            'x-organization-id',
        ])
        
        self.allow_credentials = getattr(settings, 'CORS_ALLOW_CREDENTIALS', True)
        self.max_age = getattr(settings, 'CORS_PREFLIGHT_MAX_AGE', 86400)
        
        super().__init__(get_response)
    
    def process_request(self, request):
        origin = request.META.get('HTTP_ORIGIN')
        
        if request.method == 'OPTIONS':
            return self._handle_preflight_request(request, origin)
        
        return None
    
    def process_response(self, request, response):

        origin = request.META.get('HTTP_ORIGIN')
        
        if origin and self._is_origin_allowed(origin):

            response['Access-Control-Allow-Origin'] = origin
            
            if self.allow_credentials:
                response['Access-Control-Allow-Credentials'] = 'true'
            
            exposed_headers = [
                'Content-Length',
                'Content-Type',
                'X-Total-Count',
                'X-Page-Count',
            ]
            response['Access-Control-Expose-Headers'] = ', '.join(exposed_headers)
            
            vary_header = response.get('Vary', '')
            if 'Origin' not in vary_header:
                response['Vary'] = f"{vary_header}, Origin".strip(', ')
        
        return response
    
    def _handle_preflight_request(self, request, origin):

        if not origin or not self._is_origin_allowed(origin):
            return HttpResponse(status=403)
        
        requested_method = request.META.get('HTTP_ACCESS_CONTROL_REQUEST_METHOD')
        if requested_method and requested_method not in self.allowed_methods:
            return HttpResponse(status=405)
        
        requested_headers = request.META.get('HTTP_ACCESS_CONTROL_REQUEST_HEADERS', '')
        if requested_headers:
            requested_headers_list = [h.strip().lower() for h in requested_headers.split(',')]
            allowed_headers_lower = [h.lower() for h in self.allowed_headers]
            
            for header in requested_headers_list:
                if header not in allowed_headers_lower:
                    return HttpResponse(status=400)
        
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Methods'] = ', '.join(self.allowed_methods)
        response['Access-Control-Allow-Headers'] = ', '.join(self.allowed_headers)
        response['Access-Control-Max-Age'] = str(self.max_age)
        
        if self.allow_credentials:
            response['Access-Control-Allow-Credentials'] = 'true'
        
        return response
    
    def _is_origin_allowed(self, origin):
        if not origin:
            return False
        
        if origin in self.allowed_origins:
            return True
        
        for allowed_origin in self.allowed_origins:
            if '*' in allowed_origin:
                pattern = allowed_origin.replace('*', '.*')
                import re
                if re.match(f'^{pattern}$', origin):
                    return True
        
        # En développement, permettre localhost avec n'importe quel port
        if settings.DEBUG:
            if origin.startswith('http://localhost:') or origin.startswith('http://127.0.0.1:'):
                return True
        
        return False


class CSRFExemptCORSMiddleware(MiddlewareMixin):

    def __init__(self, get_response):
        self.get_response = get_response
        
        # Endpoints exemptés de CSRF (généralement les APIs)
        self.csrf_exempt_paths = getattr(settings, 'CSRF_EXEMPT_PATHS', [
            '/api/',
        ])
        
        super().__init__(get_response)
    
    def process_request(self, request):

        path = request.path
        
        for exempt_path in self.csrf_exempt_paths:
            if path.startswith(exempt_path):
                setattr(request, '_dont_enforce_csrf_checks', True)
                break
        
        return None


class SecurityCORSMiddleware(MiddlewareMixin):
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_response(self, request, response):

        if not response.get('Content-Security-Policy'):
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
                "style-src 'self' 'unsafe-inline'",
                "img-src 'self' data: https:",
                "font-src 'self' data:",
                "connect-src 'self'",
                "frame-ancestors 'none'",
            ]
            response['Content-Security-Policy'] = '; '.join(csp_directives)
        
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
        }
        
        for header, value in security_headers.items():
            if not response.get(header):
                response[header] = value
        
        return response
