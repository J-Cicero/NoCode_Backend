
import time
import functools
from django.http import JsonResponse
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from ..models import OrganizationMember
from ..services.event_bus import EventBus


def require_organization_member(view_func):

    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentification requise'}, status=401)
        
        org_id = kwargs.get('org_id') or request.GET.get('org_id')
        if not org_id:
            return JsonResponse({'error': 'ID organisation requis'}, status=400)
        
        # Vérifier l'appartenance à l'organisation
        is_member = OrganizationMember.objects.filter(
            organization_id=org_id,
            user=request.user,
            status='ACTIVE'
        ).exists()
        
        if not is_member:
            return JsonResponse({'error': 'Accès non autorisé'}, status=403)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_verified_enterprise(view_func):
    """
    Decorator qui vérifie que l'utilisateur est une entreprise vérifiée.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentification requise'}, status=401)
        
        if request.user.user_type != 'ENTREPRISE':
            return JsonResponse({'error': 'Compte entreprise requis'}, status=403)
        
        try:
            if not request.user.entreprise.is_verified:
                return JsonResponse({'error': 'Entreprise non vérifiée'}, status=403)
        except:
            return JsonResponse({'error': 'Profil entreprise non trouvé'}, status=404)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def rate_limit(requests_per_minute=60, key_func=None):
    """
    Decorator de limitation de débit.
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Générer la clé de cache
            if key_func:
                cache_key = key_func(request, *args, **kwargs)
            else:
                user_id = request.user.id if request.user.is_authenticated else 'anonymous'
                ip = request.META.get('REMOTE_ADDR', 'unknown')
                cache_key = f"rate_limit:{view_func.__name__}:{user_id}:{ip}"
            
            # Vérifier le nombre de requêtes
            current_requests = cache.get(cache_key, 0)
            
            if current_requests >= requests_per_minute:
                return JsonResponse({
                    'error': 'Trop de requêtes',
                    'retry_after': 60
                }, status=429)
            
            # Incrémenter le compteur
            cache.set(cache_key, current_requests + 1, 60)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator


def audit_action(action_name, sensitive=False):
    """
    Decorator pour auditer les actions.
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            start_time = time.time()
            
            # Exécuter la vue
            response = view_func(request, *args, **kwargs)
            
            # Enregistrer l'audit
            audit_data = {
                'action': action_name,
                'user_id': request.user.id if request.user.is_authenticated else None,
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration': time.time() - start_time,
                'ip_address': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
            
            if not sensitive:
                audit_data['args'] = args
                audit_data['kwargs'] = {k: v for k, v in kwargs.items() if 'password' not in k.lower()}
            
            EventBus.publish('action.audited', audit_data)
            
            return response
        
        return wrapper
    
    return decorator


def cache_result(timeout=300, key_func=None, vary_on_user=True):
    """
    Decorator pour mettre en cache le résultat d'une vue.
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Générer la clé de cache
            if key_func:
                cache_key = key_func(request, *args, **kwargs)
            else:
                base_key = f"view_cache:{view_func.__name__}"
                if vary_on_user and request.user.is_authenticated:
                    base_key += f":{request.user.id}"
                
                # Ajouter les paramètres
                params = f"{args}:{sorted(kwargs.items())}"
                cache_key = f"{base_key}:{hash(params)}"
            
            # Vérifier le cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Exécuter la vue et mettre en cache
            response = view_func(request, *args, **kwargs)
            
            # Ne mettre en cache que les réponses réussies
            if response.status_code == 200:
                cache.set(cache_key, response, timeout)
            
            return response
        
        return wrapper
    
    return decorator


def require_ajax(view_func):
    """
    Decorator qui vérifie que la requête est AJAX.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Requête AJAX requise'}, status=400)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_post(view_func):
    """
    Decorator qui vérifie que la méthode est POST.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method != 'POST':
            return JsonResponse({'error': 'Méthode POST requise'}, status=405)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def handle_exceptions(default_response=None):
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                return view_func(request, *args, **kwargs)
            except Exception as e:
                # Logger l'erreur
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur dans {view_func.__name__}: {e}", exc_info=True)
                
                # Publier un événement d'erreur
                EventBus.publish('view.error', {
                    'view_name': view_func.__name__,
                    'error': str(e),
                    'user_id': request.user.id if request.user.is_authenticated else None,
                })
                
                if default_response:
                    return default_response
                
                return JsonResponse({
                    'error': 'Erreur interne du serveur'
                }, status=500)
        
        return wrapper
    
    return decorator


def timing_decorator(view_func):
    """
    Decorator pour mesurer le temps d'exécution.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        start_time = time.time()
        
        response = view_func(request, *args, **kwargs)
        
        execution_time = time.time() - start_time
        
        # Ajouter le temps d'exécution aux headers
        response['X-Execution-Time'] = f"{execution_time:.3f}s"
        
        # Logger les requêtes lentes
        if execution_time > 2.0:  # Plus de 2 secondes
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Requête lente: {view_func.__name__} - {execution_time:.3f}s")
        
        return response
    
    return wrapper
