"""
Centralisation des imports des permissions du module Foundation.
Facilite l'importation des permissions dans les autres modules.
"""

# Base permissions
from .base_permissions import (
    IsOwnerOrReadOnly,
    IsOrganizationMember,
    IsOrganizationOwner,
    IsOrganizationAdmin,
    CanManageBilling,
    IsEntrepriseOwner,
    IsStaffOrOwner,
    IsVerifiedEntreprise,
    HasActiveSubscription,
    CanInviteMembers,
    IsOwnerOrStaff,
    CanAccessUserData,
    HasSubscriptionLimit,
    DynamicPermission,
)

# Organization permissions
from .organization_permissions import (
    OrganizationPermission,
    OrganizationMemberPermission,
    OrganizationInvitationPermission,
    CanManageOrganizationSettings,
    CanViewOrganizationStats,
    OrganizationContextPermission,
)

# Billing permissions
from .billing_permissions import (
    CanManageBilling as BillingCanManageBilling,
    CanViewBillingInfo,
    CanManageSubscriptions,
    CanManagePaymentMethods,
    CanViewInvoices,
    HasActiveSubscription as BillingHasActiveSubscription,
    CanCreatePaymentIntent,
    CanGenerateInvoices,
    CanViewBillingStats,
    SubscriptionLimitPermission,
)

# Verification permissions
from .verification_permissions import (
    CanStartVerification,
    CanViewVerificationStatus,
    CanUploadDocuments,
    CanReviewDocuments,
    CanCompleteVerification,
    CanViewPendingVerifications,
    CanViewVerificationStats,
    IsVerifiedEntreprise as VerificationIsVerifiedEntreprise,
    CanAccessVerificationData,
    VerificationStatusPermission,
)

# Exports pour faciliter les imports
__all__ = [
    # Base permissions
    'IsOwnerOrReadOnly',
    'IsOrganizationMember',
    'IsOrganizationOwner',
    'IsOrganizationAdmin',
    'CanManageBilling',
    'IsEntrepriseOwner',
    'IsStaffOrOwner',
    'IsVerifiedEntreprise',
    'HasActiveSubscription',
    'CanInviteMembers',
    'IsOwnerOrStaff',
    'CanAccessUserData',
    'HasSubscriptionLimit',
    'DynamicPermission',
    
    # Organization permissions
    'OrganizationPermission',
    'OrganizationMemberPermission',
    'OrganizationInvitationPermission',
    'CanManageOrganizationSettings',
    'CanViewOrganizationStats',
    'OrganizationContextPermission',
    
    # Billing permissions
    'BillingCanManageBilling',
    'CanViewBillingInfo',
    'CanManageSubscriptions',
    'CanManagePaymentMethods',
    'CanViewInvoices',
    'BillingHasActiveSubscription',
    'CanCreatePaymentIntent',
    'CanGenerateInvoices',
    'CanViewBillingStats',
    'SubscriptionLimitPermission',
    
    # Verification permissions
    'CanStartVerification',
    'CanViewVerificationStatus',
    'CanUploadDocuments',
    'CanReviewDocuments',
    'CanCompleteVerification',
    'CanViewPendingVerifications',
    'CanViewVerificationStats',
    'VerificationIsVerifiedEntreprise',
    'CanAccessVerificationData',
    'VerificationStatusPermission',
]
