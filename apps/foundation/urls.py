
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
    OrganizationInvitationsView, OrganizationInvitationAcceptView,
    OrganizationTransferOwnershipView, OrganizationStatsView,
    leave_organization, resend_invitation
)
from .views.billing_views import (
    SubscriptionPlansView, OrganizationSubscriptionView,
    OrganizationBillingInfoView, CreatePaymentIntentView,
    SubscriptionLimitsView,InvoiceGenerateView, billing_stats
)
from .views.subscription_views import (
    SubscriptionViewSet, SubscriptionPlanViewSet,
    PaymentViewSet, InvoiceViewSet, PaymentMethodViewSet
)

app_name = 'foundation'

# Configuration des URLs de l'API
router = DefaultRouter()

# Enregistrement des ViewSets pour les abonnements
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'subscription-plans', SubscriptionPlanViewSet, basename='subscription-plan')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
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
    path('organizations/<int:org_id>/invitations/', OrganizationInvitationsView.as_view(), name='organization-invitations'),
    path('organizations/invitations/accept/', OrganizationInvitationAcceptView.as_view(), name='organization-invitation-accept'),
    path('organizations/<int:org_id>/transfer-ownership/', OrganizationTransferOwnershipView.as_view(), name='organization-transfer-ownership'),
    path('organizations/<int:org_id>/stats/', OrganizationStatsView.as_view(), name='organization-stats'),
    path('organizations/<int:org_id>/leave/', leave_organization, name='leave-organization'),
    path('organizations/<int:org_id>/invitations/<int:invitation_id>/resend/', resend_invitation, name='resend-invitation'),

    # === FACTURATION ===
    path('billing/plans/', SubscriptionPlansView.as_view(), name='subscription-plans'),
    path('billing/organizations/<int:org_id>/subscription/', OrganizationSubscriptionView.as_view(), name='organization-subscription'),
    path('billing/organizations/<int:org_id>/info/', OrganizationBillingInfoView.as_view(), name='organization-billing-info'),
    path('billing/organizations/<int:org_id>/limits/', SubscriptionLimitsView.as_view(), name='subscription-limits'),
    path('billing/organizations/<int:org_id>/invoice/', InvoiceGenerateView.as_view(), name='generate-invoice'),
    path('billing/payment-intent/', CreatePaymentIntentView.as_view(), name='create-payment-intent'),
    path('billing/stats/', billing_stats, name='billing-stats'),


]

# Inclure les URLs du routeur
urlpatterns += router.urls