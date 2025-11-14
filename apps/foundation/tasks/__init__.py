"""
Tâches Celery pour le module Foundation.
Gère les opérations asynchrones comme l'envoi d'emails, la facturation, etc.
"""

from .email_tasks import (
    send_welcome_email,
    send_verification_email,
    send_password_reset_email,
    send_billing_notification,
)

from .billing_tasks import (
    process_failed_payment,
    generate_invoice,
    send_payment_reminder,
)

from .organization_tasks import (
    sync_organization_data,
    generate_organization_report,
)

from .maintenance_tasks import (
    cleanup_old_audit_logs,
    backup_critical_data,
    health_check_services,
)
