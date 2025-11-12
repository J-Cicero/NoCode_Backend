
import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from ..models import Organization, OrganizationMember


logger = logging.getLogger(__name__)


class TenantMiddleware(MiddlewareMixin):

    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):

        # Ignorer les requêtes qui n'ont pas besoin de contexte tenant
        if self._should_skip_tenant(request):
            return None
        
        # Ignorer si l'utilisateur n'est pas authentifié
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
        
        try:
            # Déterminer l'organisation courante
            current_org = self._determine_current_organization(request)
            
            if current_org:
                # Vérifier que l'utilisateur est membre de cette organisation
                if not self._is_user_member(request.user, current_org):
                    logger.warning(f"Utilisateur {request.user.id} tente d'accéder à l'organisation {current_org.id} sans être membre")
                    return JsonResponse({
                        'error': 'Accès non autorisé à cette organisation'
                    }, status=403)
                
                # Injecter le contexte tenant
                request.current_organization = current_org
                request.tenant_id = current_org.id
                
                # Récupérer le rôle de l'utilisateur dans cette organisation
                member = OrganizationMember.objects.get(
                    organization=current_org,
                    user=request.user,
                    status='ACTIVE'
                )
                request.user_role = member.role
                request.user_permissions_in_org = member.permissions or []
                
                # Vérifier l'abonnement de l'organisation
                self._check_organization_subscription(request, current_org)
                
            else:
                # Aucune organisation spécifiée - utiliser l'organisation par défaut si applicable
                default_org = self._get_default_organization(request.user)
                if default_org:
                    request.current_organization = default_org
                    request.tenant_id = default_org.id
                
        except Organization.DoesNotExist:
            logger.warning(f"Organisation introuvable dans la requête: {request.path}")
            return JsonResponse({
                'error': 'Organisation introuvable'
            }, status=404)
        
        except OrganizationMember.DoesNotExist:
            logger.warning(f"Utilisateur {request.user.id} n'est pas membre de l'organisation")
            return JsonResponse({
                'error': 'Vous n\'êtes pas membre de cette organisation'
            }, status=403)
        
        except Exception as e:
            logger.error(f"Erreur dans le middleware tenant: {e}", exc_info=True)
            return JsonResponse({
                'error': 'Erreur interne du système tenant'
            }, status=500)
        
        return None
    
    def _should_skip_tenant(self, request):
        """
        Détermine si le contexte tenant doit être ignoré pour cette requête.
        """
        # Chemins qui n'ont pas besoin de contexte tenant
        skip_paths = [
            '/api/auth/',
            '/api/users/me/',
            '/api/users/profile/',
            '/api/organizations/',  # Liste des organisations de l'utilisateur
            '/api/billing/plans/',  # Plans publics
            '/api/health/',
            '/api/docs/',
            '/admin/',
            '/static/',
            '/media/',
        ]
        
        path = request.path
        
        # Vérifier les préfixes
        for skip_path in skip_paths:
            if path.startswith(skip_path):
                return True
        
        return False
    
    def _determine_current_organization(self, request):

        # 1. Vérifier l'en-tête X-Organization-ID
        org_id = request.META.get('HTTP_X_ORGANIZATION_ID')
        if org_id:
            try:
                return Organization.objects.get(id=int(org_id))
            except (ValueError, Organization.DoesNotExist):
                pass
        
        # 2. Vérifier les paramètres d'URL
        org_id = request.GET.get('org_id')
        if org_id:
            try:
                return Organization.objects.get(id=int(org_id))
            except (ValueError, Organization.DoesNotExist):
                pass
        
        # 3. Vérifier les paramètres d'URL dans le path
        if '/organizations/' in request.path:
            path_parts = request.path.split('/')
            try:
                org_index = path_parts.index('organizations')
                if org_index + 1 < len(path_parts):
                    org_id = path_parts[org_index + 1]
                    return Organization.objects.get(id=int(org_id))
            except (ValueError, IndexError, Organization.DoesNotExist):
                pass
        
        # 4. Vérifier le paramètre org_id dans l'URL
        import re
        org_match = re.search(r'/org/(\d+)/', request.path)
        if org_match:
            try:
                return Organization.objects.get(id=int(org_match.group(1)))
            except Organization.DoesNotExist:
                pass
        
        return None
    
    def _is_user_member(self, user, organization):

        return OrganizationMember.objects.filter(
            organization=organization,
            user=user,
            status='ACTIVE'
        ).exists()
    
    def _get_default_organization(self, user):

        # Récupérer la première organisation où l'utilisateur est propriétaire
        owned_org = Organization.objects.filter(owner=user).first()
        if owned_org:
            return owned_org
        
        # Sinon, récupérer la première organisation où l'utilisateur est membre
        member = OrganizationMember.objects.filter(
            user=user,
            status='ACTIVE'
        ).select_related('organization').first()
        
        return member.organization if member else None
    
    def _check_organization_subscription(self, request, organization):

        try:
            from ..models import Abonnement
            
            subscription = Abonnement.objects.filter(
                organization=organization,
                status='ACTIF'
            ).select_related('type_abonnement').first()
            
            if subscription:
                request.current_subscription = subscription
                request.subscription_limits = subscription.get_limits()
                request.subscription_active = True
            else:
                request.current_subscription = None
                request.subscription_limits = {}
                request.subscription_active = False
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de l'abonnement: {e}")
            request.current_subscription = None
            request.subscription_limits = {}
            request.subscription_active = False


class TenantIsolationMiddleware(MiddlewareMixin):
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):

        # Ignorer si pas de contexte tenant
        if not hasattr(request, 'current_organization'):
            return None
        
        try:
            # Stocker l'organisation courante dans le thread local
            from threading import local
            if not hasattr(self, '_local'):
                self._local = local()
            
            self._local.current_organization = request.current_organization
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration de l'isolation tenant: {e}")
        
        return None
    
    def process_response(self, request, response):

        try:
            if hasattr(self, '_local'):
                self._local.current_organization = None
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage du contexte tenant: {e}")
        
        return response


class OrganizationSwitchMiddleware(MiddlewareMixin):

    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):

        # Vérifier si c'est une requête de changement d'organisation
        if request.path == '/api/organizations/switch/' and request.method == 'POST':
            return self._handle_organization_switch(request)
        
        return None
    
    def _handle_organization_switch(self, request):

        if not request.user.is_authenticated:
            return JsonResponse({
                'error': 'Authentification requise'
            }, status=401)
        
        try:
            import json
            data = json.loads(request.body)
            org_id = data.get('organization_id')
            
            if not org_id:
                return JsonResponse({
                    'error': 'ID d\'organisation requis'
                }, status=400)
            
            try:
                organization = Organization.objects.get(id=org_id)
                member = OrganizationMember.objects.get(
                    organization=organization,
                    user=request.user,
                    status='ACTIVE'
                )
                
                from ..services.event_bus import EventBus
                EventBus.publish('organization.switched', {
                    'user_id': request.user.id,
                    'organization_id': org_id,
                    'role': member.role,
                })
                
                return JsonResponse({
                    'success': True,
                    'organization': {
                        'id': organization.id,
                        'name': organization.name,
                        'role': member.role,
                    }
                })
                
            except Organization.DoesNotExist:
                return JsonResponse({
                    'error': 'Organisation introuvable'
                }, status=404)
            
            except OrganizationMember.DoesNotExist:
                return JsonResponse({
                    'error': 'Vous n\'êtes pas membre de cette organisation'
                }, status=403)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Données JSON invalides'
            }, status=400)
        
        except Exception as e:
            logger.error(f"Erreur lors du changement d'organisation: {e}")
            return JsonResponse({
                'error': 'Erreur interne'
            }, status=500)
