"""
Permissions spécifiques au module Insights pour le NoCode Platform.
Gère l'accès aux analytics, métriques et rapports.
"""

from rest_framework.permissions import BasePermission
from django.contrib.auth import get_user_model
from apps.foundation.models import OrganizationMember

User = get_user_model()


def get_user_role_in_organization(user, organization):
    """Retourne le rôle d'un utilisateur dans une organisation."""
    if not user.is_authenticated:
        return None
        
    # Admin app a le rôle le plus élevé
    if user.is_admin or user.is_superuser:
        return 'ADMIN_APP'
        
    # Propriétaire de l'org
    if organization.owner == user:
        return 'OWNER'
        
    # Membre actif
    membership = organization.members.filter(
        user=user, 
        status='ACTIVE'
    ).first()
    
    if membership:
        return membership.role
        
    return None


class IsOrganizationOwnerOrAdmin(BasePermission):
    """Propriétaire de l'organisation OU admin app."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Vérifier si l'utilisateur est owner de l'organisation
        if hasattr(obj, 'organization'):
            return obj.organization.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
            
        return False


class IsOrganizationMemberOrAdmin(BasePermission):
    """Membre de l'organisation OU admin app."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Vérifier si l'utilisateur est membre de l'organisation
        if hasattr(obj, 'organization'):
            return obj.organization.members.filter(
                user=request.user, 
                status='ACTIVE'
            ).exists()
        elif hasattr(obj, 'user'):
            return obj.user == request.user
            
        return False


class CanViewAnalytics(BasePermission):
    """Visualisation des analytics de l'organisation."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Récupérer l'organisation
        if hasattr(obj, 'organization'):
            organization = obj.organization
        elif hasattr(obj, 'user'):
            # Pour les activités utilisateur, vérifier les organisations de l'utilisateur
            from apps.foundation.permissions import get_user_organizations
            org_ids = get_user_organizations(request.user)
            return obj.user.organization.id in org_ids if hasattr(obj.user, 'organization') else False
        else:
            return False
            
        user_role = get_user_role_in_organization(request.user, organization)
        
        # Owner et Admin peuvent voir tous les analytics
        return user_role in ['OWNER', 'ADMIN']


class CanManageMetrics(BasePermission):
    """Gestion des métriques système."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Pour les métriques système, seul l'admin app peut gérer
        if hasattr(obj, 'service') and obj.service == 'system':
            return request.user.is_admin or request.user.is_superuser
            
        # Pour les métriques d'application, vérifier l'organisation
        if hasattr(obj, 'organization'):
            user_role = get_user_role_in_organization(request.user, obj.organization)
            return user_role in ['OWNER', 'ADMIN']
            
        return False


class CanAccessReports(BasePermission):
    """Accès aux rapports de l'organisation."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Récupérer l'organisation
        if hasattr(obj, 'organization'):
            organization = obj.organization
        else:
            return False
            
        user_role = get_user_role_in_organization(request.user, organization)
        
        # Owner et Admin peuvent accéder aux rapports
        return user_role in ['OWNER', 'ADMIN']


class CanExportData(BasePermission):
    """Exportation des données analytics."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Récupérer l'organisation
        if hasattr(obj, 'organization'):
            organization = obj.organization
        else:
            return False
            
        user_role = get_user_role_in_organization(request.user, organization)
        
        # Owner et Admin peuvent exporter
        return user_role in ['OWNER', 'ADMIN']


class CanViewUserActivity(BasePermission):
    """Visualisation des activités utilisateur."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Utilisateur peut voir ses propres activités
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
            
        # Pour les activités d'autres utilisateurs, vérifier l'organisation
        if hasattr(obj, 'user') and hasattr(obj.user, 'organization'):
            user_role = get_user_role_in_organization(request.user, obj.user.organization)
            return user_role in ['OWNER', 'ADMIN']
            
        return False


class CanManageMonitoring(BasePermission):
    """Gestion du monitoring et alertes."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Récupérer l'organisation
        if hasattr(obj, 'organization'):
            organization = obj.organization
        else:
            return False
            
        user_role = get_user_role_in_organization(request.user, organization)
        
        # Owner et Admin peuvent gérer le monitoring
        return user_role in ['OWNER', 'ADMIN']


class CanAccessPerformanceMetrics(BasePermission):
    """Accès aux métriques de performance."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Récupérer l'organisation
        if hasattr(obj, 'organization'):
            organization = obj.organization
        elif hasattr(obj, 'project') and hasattr(obj.project, 'organization'):
            organization = obj.project.organization
        else:
            return False
            
        user_role = get_user_role_in_organization(request.user, organization)
        
        # Owner et Admin peuvent voir les métriques de performance
        return user_role in ['OWNER', 'ADMIN']


class CanViewSystemMetrics(BasePermission):
    """Visualisation des métriques système."""
    
    def has_permission(self, request, view):
        """Vérifie la permission au niveau de la vue."""
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Les métriques système sont réservées aux admins
        return False


class CanManageAlerts(BasePermission):
    """Gestion des alertes et notifications."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Récupérer l'organisation
        if hasattr(obj, 'organization'):
            organization = obj.organization
        else:
            return False
            
        user_role = get_user_role_in_organization(request.user, organization)
        
        # Owner et Admin peuvent gérer les alertes
        return user_role in ['OWNER', 'ADMIN']


class CanAccessDashboard(BasePermission):
    """Accès au dashboard analytics."""
    
    def has_permission(self, request, view):
        """Vérifie la permission au niveau de la vue."""
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Pour les dashboards d'organisation, vérifier le paramètre org_id
        org_id = view.kwargs.get('org_id') or request.query_params.get('org_id')
        if org_id:
            try:
                from apps.foundation.models import Organization
                organization = Organization.objects.get(id=org_id)
                user_role = get_user_role_in_organization(request.user, organization)
                return user_role in ['OWNER', 'ADMIN', 'MEMBER']
            except Organization.DoesNotExist:
                return False
                
        return True  # Si pas d'org spécifiée, laisser has_object_permission gérer
    
    def has_object_permission(self, request, view, obj):
        """Vérifie la permission sur l'objet."""
        return CanViewAnalytics().has_object_permission(request, view, obj)


# Helper pour valider les permissions d'insights
def has_insights_access(user, organization, required_permission='read'):
    """Vérifie l'accès insights selon le rôle."""
    if not user.is_authenticated:
        return False
        
    if user.is_admin or user.is_superuser:
        return True
        
    user_role = get_user_role_in_organization(user, organization)
    
    if not user_role:
        return False
        
    permissions = {
        'OWNER': {
            'read': True,
            'write': True,
            'delete': True,
            'analytics': True,
            'metrics': True,
            'reports': True,
            'export': True,
            'monitoring': True,
            'alerts': True,
        },
        'ADMIN': {
            'read': True,
            'write': True,
            'delete': False,
            'analytics': True,
            'metrics': True,
            'reports': True,
            'export': True,
            'monitoring': True,
            'alerts': True,
        },
        'MEMBER': {
            'read': True,
            'write': False,
            'delete': False,
            'analytics': False,
            'metrics': False,
            'reports': False,
            'export': False,
            'monitoring': False,
            'alerts': False,
        }
    }
    
    return permissions.get(user_role, {}).get(required_permission, False)


# Permission composite pour les vues avec objets multiples
class IsInsightsResource(BasePermission):
    """Permission de base pour les ressources insights."""
    
    def has_permission(self, request, view):
        """Vérifie la permission au niveau de la vue."""
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Vérifier si l'organisation est dans les paramètres de l'URL
        org_id = view.kwargs.get('org_pk') or view.kwargs.get('org_id')
        if org_id:
            try:
                from apps.foundation.models import Organization
                organization = Organization.objects.get(id=org_id)
                return has_insights_access(request.user, organization, 'read')
            except Organization.DoesNotExist:
                return False
                
        return True  # Si pas d'org spécifiée, laisser has_object_permission gérer
    
    def has_object_permission(self, request, view, obj):
        """Vérifie la permission sur l'objet."""
        return CanViewAnalytics().has_object_permission(request, view, obj)


# Validation des limites d'insights
def validate_insights_limits(user, organization, action='view_analytics'):
    """Valide les limites d'insights pour l'organisation."""
    if not user.is_authenticated:
        return False, "Non authentifié"
        
    if user.is_admin or user.is_superuser:
        return True, "Admin app"
        
    user_role = get_user_role_in_organization(user, organization)
    
    if not user_role:
        return False, "Non membre"
        
    # Vérifier les limites selon l'action
    if action == 'export_data':
        # Vérifier la limite d'exportation selon l'abonnement
        if hasattr(organization, 'subscription'):
            if not organization.subscription.allow_data_export:
                return False, "Export non autorisé par l'abonnement"
                
    elif action == 'advanced_analytics':
        # Vérifier l'accès aux analytics avancés
        if hasattr(organization, 'subscription'):
            if not organization.subscription.advanced_analytics:
                return False, "Analytics avancés non autorisés par l'abonnement"
                
    elif action == 'real_time_monitoring':
        # Vérifier l'accès au monitoring en temps réel
        if hasattr(organization, 'subscription'):
            if not organization.subscription.real_time_monitoring:
                return False, "Monitoring temps réel non autorisé par l'abonnement"
                
    return True, "Autorisé"


# Permissions pour les types spécifiques de métriques
class CanAccessSystemHealth(BasePermission):
    """Accès aux métriques de santé système."""
    
    def has_permission(self, request, view):
        """Vérifie la permission au niveau de la vue."""
        if not request.user.is_authenticated:
            return False
            
        # Réservé aux admins app
        return request.user.is_admin or request.user.is_superuser


class CanAccessUsageMetrics(BasePermission):
    """Accès aux métriques d'utilisation."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Récupérer l'organisation
        if hasattr(obj, 'organization'):
            organization = obj.organization
        else:
            return False
            
        user_role = get_user_role_in_organization(request.user, organization)
        
        # Owner et Admin peuvent voir les métriques d'utilisation
        return user_role in ['OWNER', 'ADMIN']


class CanManageDataRetention(BasePermission):
    """Gestion de la rétention des données."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin app a tous les droits
        if request.user.is_admin or request.user.is_superuser:
            return True
            
        # Récupérer l'organisation
        if hasattr(obj, 'organization'):
            organization = obj.organization
        else:
            return False
            
        user_role = get_user_role_in_organization(request.user, organization)
        
        # Seul Owner peut gérer la rétention des données
        return user_role == 'OWNER'


# Helper pour déterminer les permissions requises selon l'action
def get_insights_permission(action):
    """Retourne la permission insights requise pour une action."""
    mapping = {
        'list': 'read',
        'retrieve': 'read',
        'create': 'write',
        'update': 'write',
        'partial_update': 'write',
        'destroy': 'delete',
        'analytics': 'analytics',
        'metrics': 'metrics',
        'reports': 'reports',
        'export': 'export',
        'monitoring': 'monitoring',
        'alerts': 'alerts',
        'system_health': 'system_health',
        'usage_metrics': 'usage_metrics',
        'data_retention': 'data_retention',
    }
    return mapping.get(action, 'read')
