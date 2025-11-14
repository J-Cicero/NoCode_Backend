
import re
import os
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.conf import settings


class SIRETValidator:

    def __init__(self, message=None):
        self.message = message or "Le numéro SIRET n'est pas valide."
    
    def __call__(self, value):
        if not self.is_valid_siret(value):
            raise ValidationError(self.message, code='invalid_siret')
    
    def is_valid_siret(self, siret):

        if not siret:
            return False
        
        siret = re.sub(r'[^0-9]', '', str(siret))
        
        if len(siret) != 14:
            return False
        
        if not siret.isdigit():
            return False
        
        total = 0
        for i, digit in enumerate(siret):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n = n // 10 + n % 10
            total += n
        
        return total % 10 == 0


class PhoneNumberValidator:
    """
    Validator pour les numéros de téléphone français.
    """
    
    def __init__(self, message=None):
        self.message = message or "Le numéro de téléphone n'est pas valide."
        # Pattern pour les numéros français
        self.pattern = re.compile(r'^(?:(?:\+33|0)[1-9])(?:[0-9]{8})$')
    
    def __call__(self, value):
        if not self.is_valid_phone(value):
            raise ValidationError(self.message, code='invalid_phone')
    
    def is_valid_phone(self, phone):
        """
        Vérifie la validité d'un numéro de téléphone français.
        """
        if not phone:
            return False
        
        # Supprimer les espaces, tirets et points
        phone = re.sub(r'[\s\-\.]', '', str(phone))
        
        return bool(self.pattern.match(phone))


class PasswordStrengthValidator:
    def __init__(self, min_length=8, require_uppercase=True, require_lowercase=True, 
                 require_digits=True, require_special=True, message=None):
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_special = require_special
        self.message = message or "Le mot de passe ne respecte pas les critères de sécurité."
    
    def __call__(self, value):
        errors = self.validate_password(value)
        if errors:
            raise ValidationError(errors, code='weak_password')
    
    def validate_password(self, password):
        errors = []
        
        if not password:
            errors.append("Le mot de passe est requis.")
            return errors
        
        if len(password) < self.min_length:
            errors.append(f"Le mot de passe doit contenir au moins {self.min_length} caractères.")
        
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Le mot de passe doit contenir au moins une majuscule.")
        
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Le mot de passe doit contenir au moins une minuscule.")
        
        if self.require_digits and not re.search(r'\d', password):
            errors.append("Le mot de passe doit contenir au moins un chiffre.")
        
        if self.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Le mot de passe doit contenir au moins un caractère spécial.")
        
        return errors


class EmailDomainValidator:
    def __init__(self, allowed_domains=None, blocked_domains=None, message=None):
        self.allowed_domains = allowed_domains or []
        self.blocked_domains = blocked_domains or [
            'tempmail.org', '10minutemail.com', 'guerrillamail.com'
        ]
        self.message = message or "Ce domaine d'email n'est pas autorisé."
        self.email_validator = EmailValidator()
    
    def __call__(self, value):
        self.email_validator(value)
        
        if not self.is_valid_domain(value):
            raise ValidationError(self.message, code='invalid_domain')
    
    def is_valid_domain(self, email):
        if not email or '@' not in email:
            return False
        
        domain = email.split('@')[1].lower()
        if domain in self.blocked_domains:
            return False
        
        if self.allowed_domains and domain not in self.allowed_domains:
            return False
        
        return True


class FileUploadValidator:

    def __init__(self, allowed_extensions=None, max_size=None, min_size=None, message=None):
        self.allowed_extensions = allowed_extensions or [
            '.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'
        ]
        self.max_size = max_size or 10 * 1024 * 1024  # 10MB par défaut
        self.min_size = min_size or 1024  # 1KB par défaut
        self.message = message or "Le fichier n'est pas valide."
    
    def __call__(self, value):
        errors = self.validate_file(value)
        if errors:
            raise ValidationError(errors, code='invalid_file')
    
    def validate_file(self, file):
        errors = []
        
        if not file:
            errors.append("Aucun fichier fourni.")
            return errors
        
        file_extension = os.path.splitext(file.name)[1].lower()
        if file_extension not in self.allowed_extensions:
            errors.append(f"Extension de fichier non autorisée. Extensions autorisées: {', '.join(self.allowed_extensions)}")
        
        if hasattr(file, 'size'):
            if file.size > self.max_size:
                errors.append(f"Le fichier est trop volumineux. Taille maximale: {self.max_size // (1024*1024)}MB")
            
            if file.size < self.min_size:
                errors.append(f"Le fichier est trop petit. Taille minimale: {self.min_size} bytes")
        
        return errors


class IBANValidator:
    def __init__(self, message=None):
        self.message = message or "Le numéro IBAN n'est pas valide."
    
    def __call__(self, value):
        if not self.is_valid_iban(value):
            raise ValidationError(self.message, code='invalid_iban')
    
    def is_valid_iban(self, iban):
        if not iban:
            return False
        
        iban = re.sub(r'\s', '', str(iban)).upper()
        
        if not (15 <= len(iban) <= 34):
            return False
        
        if not re.match(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]+$', iban):
            return False
        rearranged = iban[4:] + iban[:4]
        
        numeric_string = ''
        for char in rearranged:
            if char.isalpha():
                numeric_string += str(ord(char) - ord('A') + 10)
            else:
                numeric_string += char
        
        # Vérifier le modulo 97
        return int(numeric_string) % 97 == 1


class CompanyNameValidator:

    def __init__(self, min_length=2, max_length=100, message=None):
        self.min_length = min_length
        self.max_length = max_length
        self.message = message or "Le nom d'entreprise n'est pas valide."
        self.pattern = re.compile(r'^[a-zA-ZÀ-ÿ0-9\s\-\.\&\(\)]+$')
    
    def __call__(self, value):
        if not self.is_valid_company_name(value):
            raise ValidationError(self.message, code='invalid_company_name')
    
    def is_valid_company_name(self, name):

        if not name:
            return False
        
        name = str(name).strip()
        
        if not (self.min_length <= len(name) <= self.max_length):
            return False
        
        if not self.pattern.match(name):
            return False
        
        if not re.search(r'[a-zA-ZÀ-ÿ0-9]', name):
            return False
        
        return True


class PostalCodeValidator:
    def __init__(self, message=None):
        self.message = message or "Le code postal n'est pas valide."
        self.pattern = re.compile(r'^[0-9]{5}$')
    
    def __call__(self, value):
        if not self.is_valid_postal_code(value):
            raise ValidationError(self.message, code='invalid_postal_code')
    
    def is_valid_postal_code(self, postal_code):
        if not postal_code:
            return False
        
        postal_code = str(postal_code).strip()
        return bool(self.pattern.match(postal_code))
