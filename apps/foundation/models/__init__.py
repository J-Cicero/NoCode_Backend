
from .base import (
    BaseModel,
    TimestampedModel,
    UUIDModel,
)

from .mixins import (
    TimestampMixin,
    SoftDeleteMixin,
    StatusMixin,
    AuditMixin,
    PermissionMixin,
    MetadataMixin,
    SlugMixin,
    OrderingMixin,
)

# Système d'utilisateurs
from .user import (
    User,
    Client,
)

# Système d'organisations (multi-tenancy)
from .organization import (
    Organization,
    OrganizationMember,
    OrganizationSettings,
)

# Système d'abonnements
from .subscription import (
    TypeAbonnement,
    Abonnement,
)


# Liste de tous les modèles pour faciliter les imports
__all__ = [
    # Base et mixins
    'BaseModel',
    'TimestampedModel',
    'UUIDModel',
    'TimestampMixin',
    'SoftDeleteMixin',
    'StatusMixin',
    'AuditMixin',
    'PermissionMixin',
    'MetadataMixin',
    'SlugMixin',
    'OrderingMixin',
    
    # Utilisateurs
    'User',
    'Client',
    
    # Organisations
    'Organization',
    'OrganizationMember',
    'OrganizationSettings',
    
    # Abonnements
    'TypeAbonnement',
    'Abonnement',
]
