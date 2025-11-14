"""
Centralisation des imports des serializers du module Foundation.
Facilite l'importation des serializers dans les autres modules.
"""

# User serializers
from .user_serializers import (
    UserBaseSerializer,
    UserDetailSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    PasswordChangeSerializer,
    UserProfileSerializer,
    EmailVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    UserStatsSerializer,
)

# Organization serializers
from .org_serializers import (
    OrganizationBaseSerializer,
    OrganizationDetailSerializer,
    OrganizationCreateSerializer,
    OrganizationUpdateSerializer,
    OrganizationMemberSerializer,
    OrganizationMemberUpdateSerializer,
    OrganizationStatsSerializer,
    OrganizationListSerializer,
    OrganizationTransferOwnershipSerializer,
    OrganizationActivitySerializer,
)

# Billing serializers
from .billing_serializers import (
    TypeAbonnementSerializer,
    TypeAbonnementDetailSerializer,
    AbonnementSerializer,
    AbonnementCreateSerializer,

)

# Exports pour faciliter les imports
__all__ = [
    # User serializers
    'UserBaseSerializer',
    'UserDetailSerializer',
    'UserCreateSerializer',
    'UserUpdateSerializer',
    'PasswordChangeSerializer',
    'UserProfileSerializer',
    'EmailVerificationSerializer',
    'PasswordResetRequestSerializer',
    'PasswordResetConfirmSerializer',
    'UserStatsSerializer',
    
    # Organization serializers
    'OrganizationBaseSerializer',
    'OrganizationDetailSerializer',
    'OrganizationCreateSerializer',
    'OrganizationUpdateSerializer',
    'OrganizationMemberSerializer',
    'OrganizationMemberUpdateSerializer',
    'OrganizationStatsSerializer',
    'OrganizationListSerializer',
    'OrganizationTransferOwnershipSerializer',
    'OrganizationActivitySerializer',
    
    # Billing serializers
    'TypeAbonnementSerializer',
    'TypeAbonnementDetailSerializer',
    'AbonnementSerializer',
    'AbonnementCreateSerializer',
]
