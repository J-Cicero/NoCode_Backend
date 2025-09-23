"""
Tâches Celery pour le module Foundation.
Gère les opérations asynchrones comme l'envoi d'emails, la synchronisation Stripe, etc.
"""

from .email_tasks import (
    send_welcome_email,
    send_verification_email,
    send_password_reset_email,
    send_invitation_email,
    send_billing_notification,
)

from .billing_tasks import (
    sync_stripe_subscription,
    process_failed_payment,
    generate_invoice,
    send_payment_reminder,
    update_subscription_usage,
)

from .verification_tasks import (
    process_document_verification,
    send_verification_status_update,
    cleanup_expired_verifications,
)

from .organization_tasks import (
    cleanup_expired_invitations,
    sync_organization_data,
    generate_organization_report,
)

from .maintenance_tasks import (
    cleanup_old_audit_logs,
    backup_critical_data,
    health_check_services,
)
