"""
URLs pour l'application foundation
"""
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
    StripeWebhookView, SubscriptionLimitsView,
    InvoiceGenerateView, billing_stats
)
from .views.verification_views import (
    StartVerificationView, VerificationStatusView, DocumentUploadView,
    DocumentReviewView, CompleteVerificationView
)
from .views.stripe_webhook_view import StripeWebhookView as StripeWebhookViewDedicated

app_name = 'foundation'

# Configuration des URLs de l'API
router = DefaultRouter()

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

    # === WEBHOOKS STRIPE ===
    path('webhooks/stripe/', StripeWebhookViewDedicated.as_view(), name='stripe-webhook'),

    # === VÉRIFICATION DE DOCUMENTS ===
    path('verification/start/', StartVerificationView.as_view(), name='start-verification'),
    path('verification/status/', VerificationStatusView.as_view(), name='verification-status'),
    path('verification/upload/', DocumentUploadView.as_view(), name='document-upload'),
    path('verification/review/', DocumentReviewView.as_view(), name='document-review'),
    path('verification/complete/', CompleteVerificationView.as_view(), name='complete-verification'),
]

# Inclure les URLs du routeur
urlpatterns += router.urls