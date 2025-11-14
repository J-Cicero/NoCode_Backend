"""
URLs API v1 pour le module Foundation.
Structure RESTful avec tracking_id et conventions anglaises.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from .views.auth_views import (
    RegisterView, LoginView, LogoutView, RefreshTokenView,
    PasswordResetRequestView, PasswordResetConfirmView, PasswordChangeView
)
from .views.user_views import (
    UserProfileView, UserSearchView, UserStatsView, UserDeactivateView, UserOrganizationsView
)
from .views.org_views import (
    OrganizationListCreateView, OrganizationDetailView,
    OrganizationMembersView, OrganizationMemberDetailView,
    OrganizationTransferOwnershipView, OrganizationStatsView,
    leave_organization
)
from .views.subscription_views import (
    SubscriptionViewSet, SubscriptionPlanViewSet
)

app_name = 'foundation_v1'

# Router principal
router = DefaultRouter()
router.register(r'users', UserProfileView, basename='user')
router.register(r'organizations', OrganizationListCreateView, basename='organization')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'subscription-plans', SubscriptionPlanViewSet, basename='subscription-plan')

# Router nested pour les membres d'organisation
organizations_router = routers.NestedDefaultRouter(router, r'organizations', lookup='organization')
organizations_router.register(r'members', OrganizationMembersView, basename='organization-members')

# Router nested pour les abonnements utilisateur
users_router = routers.NestedDefaultRouter(router, r'users', lookup='user')
users_router.register(r'subscriptions', SubscriptionViewSet, basename='user-subscriptions')

# URLs d'authentification
auth_urls = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', RefreshTokenView.as_view(), name='refresh'),
    path('password/reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('password/change/', PasswordChangeView.as_view(), name='password-change'),
]

# URLs principales
urlpatterns = [
    # Authentification
    path('auth/', include(auth_urls)),
    
    # Router principal
    path('', include(router.urls)),
    path('', include(organizations_router.urls)),
    path('', include(users_router.urls)),
    
    # Actions spécifiques sur les utilisateurs
    path('users/search/', UserSearchView.as_view(), name='user-search'),
    path('users/stats/', UserStatsView.as_view(), name='user-stats'),
    path('users/<uuid:tracking_id>/deactivate/', UserDeactivateView.as_view(), name='user-deactivate'),
    path('users/<uuid:tracking_id>/organizations/', UserOrganizationsView.as_view(), name='user-organizations'),
    
    # Actions spécifiques sur les organisations
    path('organizations/<uuid:tracking_id>/stats/', OrganizationStatsView.as_view(), name='organization-stats'),
    path('organizations/<uuid:tracking_id>/transfer-ownership/', OrganizationTransferOwnershipView.as_view(), name='organization-transfer-ownership'),
    path('organizations/<uuid:tracking_id>/leave/', leave_organization, name='organization-leave'),
    
    # Membre spécifique d'organisation
    path('organizations/<uuid:tracking_id>/members/<uuid:member_tracking_id>/', OrganizationMemberDetailView.as_view(), name='organization-member-detail'),
]
