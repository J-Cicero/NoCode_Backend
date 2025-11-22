

# Permissions principales (simplifiées et centralisées)
from .core import (
    IsAuthenticated,
    IsStaffUser,
    IsResourceOwner,
    IsOrgMember,
    IsOrgAdmin,
    IsOrgOwner,
    HasActiveSubscription,
    IsOwnerOrReadOnly,
    # Helpers
    get_user_organizations,
    is_org_member,
    is_org_admin,
    is_org_owner,
)

# Aliases pour compatibilité avec l'ancien code
IsOrganizationMember = IsOrgMember
IsOrganizationOwner = IsOrgOwner
IsOrganizationAdmin = IsOrgAdmin

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
    # Core permissions (simplifiées)
    'IsAuthenticated',
    'IsStaffUser',
    'IsResourceOwner',
    'IsOrgMember',
    'IsOrgAdmin',
    'IsOrgOwner',
    'HasActiveSubscription',
    'IsOwnerOrReadOnly',
    
    'IsOrganizationMember',
    'IsOrganizationOwner',
    'IsOrganizationAdmin',
    
    'get_user_organizations',
    'is_org_member',
    'is_org_admin',
    'is_org_owner',
    
    'OrganizationPermission',
    'OrganizationMemberPermission',
    'CanViewOrganizationStats',
    'OrganizationContextPermission',
    
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
