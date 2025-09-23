"""
Utilitaires et validators pour le module Foundation.
Fournit des fonctions utilitaires, validators et helpers pour le module.
"""

from .validators import (
    SIRETValidator,
    PhoneNumberValidator,
    PasswordStrengthValidator,
    EmailDomainValidator,
    FileUploadValidator,
)

from .helpers import (
    generate_unique_token,
    format_currency,
    calculate_tax,
    sanitize_filename,
    extract_file_metadata,
    generate_invoice_number,
)

from .decorators import (
    require_organization_member,
    require_verified_enterprise,
    rate_limit,
    audit_action,
    cache_result,
)

from .formatters import (
    format_phone_number,
    format_siret,
    format_date_french,
    format_currency_french,
    truncate_text,
)

from .security import (
    hash_sensitive_data,
    encrypt_data,
    decrypt_data,
    generate_secure_token,
    validate_signature,
)
