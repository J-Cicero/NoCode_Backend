"""
Tâches Celery pour Foundation - Version complète.
Emails et maintenance système.
"""

from .email_tasks import (
    send_welcome_email,
    send_password_reset_email,
)
from .maintenance_tasks import (
    cleanup_expired_sessions,
    cleanup_old_audit_logs,
    update_user_statistics,
)

__all__ = [
    'send_welcome_email',
    'send_password_reset_email',
    'cleanup_expired_sessions',
    'cleanup_old_audit_logs', 
    'update_user_statistics',
]
