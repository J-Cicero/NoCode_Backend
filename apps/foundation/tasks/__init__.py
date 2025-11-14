"""
Tâches Celery pour Foundation - Version simplifiée.
Uniquement les emails essentiels.
"""

from .email_tasks import (
    send_welcome_email,
    send_password_reset_email,
)

__all__ = [
    'send_welcome_email',
    'send_password_reset_email',
]
