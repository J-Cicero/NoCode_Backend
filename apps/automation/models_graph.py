"""DEPRECATED: kept for backward-compat imports.

Le projet a une seule source de vérité pour les modèles Node/Edge:
- `apps.automation.models.Node`
- `apps.automation.models.Edge`

Ce module reste uniquement pour ne pas casser d'anciens imports.
"""

from .models import Node, Edge  # noqa: F401
