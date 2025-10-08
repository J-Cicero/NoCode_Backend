"""
Imports des modèles du module Foundation.
Ce fichier centralise tous les imports pour faciliter l'utilisation des modèles.
"""

# Modèles de base et mixins
from .base import (
    BaseModel,
    TimestampedModel,
    SoftDeleteModel,
    UUIDModel,
    ActiveManager,
    AllObjectsManager,
    SoftDeleteQuerySet,
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
    ActivityLogMixin,
)

# Système d'utilisateurs
from .user import (
    User,
    Client,
    Entreprise,
)

# Système d'organisations (multi-tenancy)
from .organization import (
    Organization,
    OrganizationMember,
)

# Système d'abonnements
from .subscription import (
    TypeAbonnement,
    Abonnement,
)

# Système de facturation
from .billing import (
    MoyenDePaiement,
    Paiement,
    Facture,
    HistoriqueTarification,
)

# Système de vérification des entreprises
from .verification import (
    DocumentVerification,
    DocumentUpload,
)

# Liste de tous les modèles pour faciliter les imports
__all__ = [
    # Base et mixins
    'BaseModel',
    'TimestampedModel',
    'SoftDeleteModel',
    'UUIDModel',
    'ActiveManager',
    'AllObjectsManager',
    'SoftDeleteQuerySet',
    'TimestampMixin',
    'SoftDeleteMixin',
    'StatusMixin',
    'AuditMixin',
    'PermissionMixin',
    'MetadataMixin',
    'SlugMixin',
    'OrderingMixin',
    'ActivityLogMixin',
    
    # Utilisateurs
    'User',
    'Client',
    'Entreprise',
    
    # Organisations
    'Organization',
    'OrganizationMember',

    
    # Abonnements
    'TypeAbonnement',
    'Abonnement',
    
    # Facturation
    'MoyenDePaiement',
    'Paiement',
    'Facture',
    'HistoriqueTarification',
    
    # Vérification
    'DocumentVerification',
    'DocumentUpload',
]
