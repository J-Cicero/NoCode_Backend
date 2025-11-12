
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.auth_views import (
    RegisterClientView, LoginView, LogoutView, RefreshTokenView,
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
# billing_views.py supprimé
from .views.subscription_views import (
    SubscriptionViewSet, SubscriptionPlanViewSet,
    PaymentMethodViewSet
)

app_name = 'foundation'

# Configuration des URLs de l'API
router = DefaultRouter()

# Enregistrement des ViewSets pour les abonnements
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'subscription-plans', SubscriptionPlanViewSet, basename='subscription-plan')
router.register(r'payment-methods', PaymentMethodViewSet, basename='payment-method')

urlpatterns = [
    # === AUTHENTIFICATION ===
    path('auth/register/client/', RegisterClientView.as_view(), name='register-client'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/refresh/', RefreshTokenView.as_view(), name='refresh-token'),
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('auth/password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('auth/change-password/', PasswordChangeView.as_view(), name='change-password'),

    # === UTILISATEURS ===
    path('users/profile/', UserProfileView.as_view(), name='user-profile'),
    path('users/profile/<int:user_id>/', UserProfileView.as_view(), name='user-profile-detail'),
    path('users/search/', UserSearchView.as_view(), name='user-search'),
    path('users/stats/', UserStatsView.as_view(), name='user-stats'),
    path('users/<int:user_id>/deactivate/', UserDeactivateView.as_view(), name='user-deactivate'),
    path('users/<int:user_id>/organizations/', UserOrganizationsView.as_view(), name='user-organizations'),

    # === ORGANISATIONS ===
    path('organizations/', OrganizationListCreateView.as_view(), name='organization-list-create'),
    path('organizations/<int:org_id>/', OrganizationDetailView.as_view(), name='organization-detail'),
    path('organizations/<int:org_id>/members/', OrganizationMembersView.as_view(), name='organization-members'),
    path('organizations/<int:org_id>/members/<int:member_id>/', OrganizationMemberDetailView.as_view(), name='organization-member-detail'),
    # Invitations - SUPPRIMÉES (modèle OrganizationInvitation supprimé)
    path('organizations/<int:org_id>/transfer-ownership/', OrganizationTransferOwnershipView.as_view(), name='organization-transfer-ownership'),
    path('organizations/<int:org_id>/stats/', OrganizationStatsView.as_view(), name='organization-stats'),
    path('organizations/<int:org_id>/leave/', leave_organization, name='leave-organization'),
    # resend_invitation - SUPPRIMÉ (modèle OrganizationInvitation supprimé)



]

# Inclure les URLs du routeur
urlpatterns += router.urls