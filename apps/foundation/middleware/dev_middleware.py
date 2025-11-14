
from django.http import JsonResponse
from django.conf import settings

class DevCORSMiddleware:
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.method == 'OPTIONS':
            response = JsonResponse({'status': 'ok'})
        else:
            response = self.get_response(request)
        
        if settings.DEBUG:
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = (
                'Accept, Accept-Language, Authorization, Content-Type, '
                'X-Requested-With, X-CSRFToken, X-API-Key'
            )
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Max-Age'] = '86400'
        
        return response


class DevCSRFExemptMiddleware:
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_paths = [
            '/api/auth/',
            '/api/organizations/',
            '/api/billing/',
            '/api/verification/',
            '/api/webhooks/',
        ]
    
    def __call__(self, request):
        if settings.DEBUG and any(request.path.startswith(path) for path in self.exempt_paths):
            setattr(request, '_dont_enforce_csrf_checks', True)
        
        return self.get_response(request)


class DevAuthBypassMiddleware:
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.test_token = 'dev-test-token-123'
    
    def __call__(self, request):

        if settings.DEBUG:
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header == f'Bearer {self.test_token}':
                # Créer un utilisateur de test temporaire
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                try:
                    test_user = User.objects.get(email='test@dev.local')
                except User.DoesNotExist:
                    test_user = User.objects.create_user(
                        email='test@dev.local',
                        password='testpass',
                        user_type='CLIENT'
                    )
                
                request.user = test_user
        
        return self.get_response(request)


class DevRequestLoggingMiddleware:
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if settings.DEBUG:
            print(f"\n🔍 DEV REQUEST: {request.method} {request.path}")
            print(f"   Headers: {dict(request.headers)}")
            if request.body:
                try:
                    import json
                    body = json.loads(request.body)
                    print(f"   Body: {body}")
                except:
                    print(f"   Body (raw): {request.body[:200]}...")
        
        response = self.get_response(request)
        
        if settings.DEBUG:
            print(f"   Response: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"   Response data: {response.data}")
        
        return response
