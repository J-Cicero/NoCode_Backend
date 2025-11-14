

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

# Aliases pour compatibilité
IsOrgMember = IsOrganizationMember
IsOrgAdmin = IsOrganizationAdmin

# Organization permissions
from .organization_permissions import (
    OrganizationPermission,
    OrganizationMemberPermission,
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
    
    # Aliases
    'IsOrgMember',
    'IsOrgAdmin',
    
    # Organization permissions
    'OrganizationPermission',
    'OrganizationMemberPermission',
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
    

]
