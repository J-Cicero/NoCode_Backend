"""
Tests pour les utilitaires du module Foundation.
"""
import os
import tempfile
from decimal import Decimal
from datetime import datetime, date
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.http import JsonResponse

from ..utils.validators import (
    SIRETValidator, PhoneNumberValidator, PasswordStrengthValidator,
    EmailDomainValidator, FileUploadValidator, IBANValidator,
    CompanyNameValidator, PostalCodeValidator
)
from ..utils.helpers import (
    generate_unique_token, format_currency, calculate_tax,
    sanitize_filename, generate_invoice_number, parse_phone_number,
    mask_sensitive_data, validate_json_structure
)
from ..utils.formatters import (
    format_phone_number, format_siret, format_date_french,
    format_currency_french, format_file_size, format_address
)
from ..utils.security import (
    hash_sensitive_data, verify_hashed_data, encrypt_data, decrypt_data,
    generate_secure_token, validate_signature, create_signature,
    mask_email, mask_phone
)

User = get_user_model()


class ValidatorsTestCase(TestCase):
    """Tests pour les validators."""
    
    def test_siret_validator(self):
        """Test du validator SIRET."""
        validator = SIRETValidator()
        
        # SIRET valides
        valid_sirets = [
            '73282932000074',  # SIRET valide
            '732 829 320 00074',  # Avec espaces
        ]
        
        for siret in valid_sirets:
            try:
                validator(siret)
            except ValidationError:
                self.fail(f"SIRET {siret} devrait être valide")
        
        # SIRET invalides
        invalid_sirets = [
            '12345678901234',  # Checksum invalide
            '1234567890123',   # Trop court
            '123456789012345', # Trop long
            'abcd1234567890',  # Caractères non numériques
            '',                # Vide
        ]
        
        for siret in invalid_sirets:
            with self.assertRaises(ValidationError):
                validator(siret)
    
    def test_phone_validator(self):
        """Test du validator de téléphone."""
        validator = PhoneNumberValidator()
        
        # Numéros valides
        valid_phones = [
            '0123456789',
            '+33123456789',
            '01 23 45 67 89',
            '+33 1 23 45 67 89',
        ]
        
        for phone in valid_phones:
            try:
                validator(phone)
            except ValidationError:
                self.fail(f"Téléphone {phone} devrait être valide")
        
        # Numéros invalides
        invalid_phones = [
            '123456789',      # Trop court
            '01234567890',    # Trop long
            '0023456789',     # Commence par 00
            '+1234567890',    # Pas français
            '',               # Vide
        ]
        
        for phone in invalid_phones:
            with self.assertRaises(ValidationError):
                validator(phone)
    
    def test_password_strength_validator(self):
        """Test du validator de force de mot de passe."""
        validator = PasswordStrengthValidator()
        
        # Mots de passe valides
        valid_passwords = [
            'Password123!',
            'MyStr0ng@Pass',
            'Complex1ty#',
        ]
        
        for password in valid_passwords:
            try:
                validator(password)
            except ValidationError:
                self.fail(f"Mot de passe {password} devrait être valide")
        
        # Mots de passe invalides
        invalid_passwords = [
            'weak',           # Trop court
            'password',       # Pas de majuscule, chiffre, caractère spécial
            'PASSWORD',       # Pas de minuscule, chiffre, caractère spécial
            '12345678',       # Pas de lettres, caractère spécial
        ]
        
        for password in invalid_passwords:
            with self.assertRaises(ValidationError):
                validator(password)
    
    def test_iban_validator(self):
        """Test du validator IBAN."""
        validator = IBANValidator()
        
        # IBAN valides
        valid_ibans = [
            'FR1420041010050500013M02606',  # IBAN français valide
            'DE89370400440532013000',       # IBAN allemand valide
        ]
        
        for iban in valid_ibans:
            try:
                validator(iban)
            except ValidationError:
                self.fail(f"IBAN {iban} devrait être valide")
        
        # IBAN invalides
        invalid_ibans = [
            'FR1420041010050500013M02607',  # Checksum invalide
            'INVALID',                      # Format invalide
            '',                             # Vide
        ]
        
        for iban in invalid_ibans:
            with self.assertRaises(ValidationError):
                validator(iban)


class HelpersTestCase(TestCase):
    """Tests pour les helpers."""
    
    def test_generate_unique_token(self):
        """Test de génération de token unique."""
        token1 = generate_unique_token()
        token2 = generate_unique_token()
        
        self.assertNotEqual(token1, token2)
        self.assertTrue(len(token1) > 0)
    
    def test_format_currency(self):
        """Test de formatage de devise."""
        self.assertEqual(format_currency(1234.56), "1 234,56 €")
        self.assertEqual(format_currency(0), "0,00 €")
        self.assertEqual(format_currency(1234.56, 'USD'), "1,234.56 USD")
    
    def test_calculate_tax(self):
        """Test de calcul de TVA."""
        result = calculate_tax(100, 0.20)
        
        self.assertEqual(result['amount_ht'], 100.0)
        self.assertEqual(result['tax_amount'], 20.0)
        self.assertEqual(result['amount_ttc'], 120.0)
        self.assertEqual(result['tax_rate'], 0.20)
    
    def test_sanitize_filename(self):
        """Test de nettoyage de nom de fichier."""
        self.assertEqual(sanitize_filename('test<>file.txt'), 'test__file.txt')
        self.assertEqual(sanitize_filename(''), 'unnamed_file')
        
        # Test avec nom très long
        long_name = 'a' * 150 + '.txt'
        result = sanitize_filename(long_name)
        self.assertTrue(len(result) <= 104)  # 100 + '.txt'
    
    def test_parse_phone_number(self):
        """Test de parsing de numéro de téléphone."""
        self.assertEqual(parse_phone_number('01 23 45 67 89'), '+33123456789')
        self.assertEqual(parse_phone_number('0123456789'), '+33123456789')
        self.assertEqual(parse_phone_number('+33123456789'), '+33123456789')
        self.assertEqual(parse_phone_number('33123456789'), '+33123456789')
    
    def test_mask_sensitive_data(self):
        """Test de masquage de données sensibles."""
        self.assertEqual(mask_sensitive_data('1234567890'), '12****7890')
        self.assertEqual(mask_sensitive_data('123'), '***')
        self.assertEqual(mask_sensitive_data(''), '')
    
    def test_validate_json_structure(self):
        """Test de validation de structure JSON."""
        data = {'name': 'test', 'email': 'test@example.com'}
        required_fields = ['name', 'email']
        
        valid, message = validate_json_structure(data, required_fields)
        self.assertTrue(valid)
        
        # Test avec champ manquant
        data_incomplete = {'name': 'test'}
        valid, message = validate_json_structure(data_incomplete, required_fields)
        self.assertFalse(valid)
        self.assertIn('email', message)


class FormattersTestCase(TestCase):
    """Tests pour les formatters."""
    
    def test_format_phone_number(self):
        """Test de formatage de numéro de téléphone."""
        phone = '+33123456789'
        
        self.assertEqual(
            format_phone_number(phone, 'international'),
            '+33 1 23 45 67 89'
        )
        self.assertEqual(
            format_phone_number(phone, 'national'),
            '01 23 45 67 89'
        )
        self.assertEqual(
            format_phone_number(phone, 'compact'),
            '+33123456789'
        )
    
    def test_format_siret(self):
        """Test de formatage SIRET."""
        siret = '73282932000074'
        expected = '732 829 320 00074'
        
        self.assertEqual(format_siret(siret), expected)
        self.assertEqual(format_siret(''), '')
        self.assertEqual(format_siret('invalid'), 'invalid')
    
    def test_format_currency_french(self):
        """Test de formatage de devise française."""
        self.assertEqual(format_currency_french(1234.56), '1 234,56 €')
        self.assertEqual(format_currency_french(0), '0,00 €')
        self.assertEqual(format_currency_french(None), '0,00 €')
    
    def test_format_file_size(self):
        """Test de formatage de taille de fichier."""
        self.assertEqual(format_file_size(1024), '1.0 KB')
        self.assertEqual(format_file_size(1048576), '1.0 MB')
        self.assertEqual(format_file_size(0), '0 B')
    
    def test_format_address(self):
        """Test de formatage d'adresse."""
        address = {
            'street_number': '123',
            'street_name': 'Rue de la Paix',
            'postal_code': '75001',
            'city': 'Paris'
        }
        
        formatted = format_address(address)
        self.assertIn('123 Rue de la Paix', formatted)
        self.assertIn('75001 Paris', formatted)


class SecurityTestCase(TestCase):
    """Tests pour les utilitaires de sécurité."""
    
    def test_hash_and_verify_sensitive_data(self):
        """Test de hachage et vérification de données sensibles."""
        data = "sensitive_information"
        
        hashed = hash_sensitive_data(data)
        self.assertIsNotNone(hashed)
        self.assertNotEqual(hashed, data)
        
        # Vérification
        self.assertTrue(verify_hashed_data(data, hashed))
        self.assertFalse(verify_hashed_data("wrong_data", hashed))
    
    def test_generate_secure_token(self):
        """Test de génération de token sécurisé."""
        token1 = generate_secure_token()
        token2 = generate_secure_token()
        
        self.assertNotEqual(token1, token2)
        self.assertTrue(len(token1) > 0)
    
    def test_signature_validation(self):
        """Test de validation de signature."""
        data = "test_data"
        secret = "secret_key"
        
        signature = create_signature(data, secret)
        self.assertTrue(validate_signature(data, signature, secret))
        self.assertFalse(validate_signature(data, signature, "wrong_secret"))
        self.assertFalse(validate_signature("wrong_data", signature, secret))
    
    def test_mask_email(self):
        """Test de masquage d'email."""
        self.assertEqual(mask_email('test@example.com'), 't**t@example.com')
        self.assertEqual(mask_email('ab@example.com'), '**@example.com')
        self.assertEqual(mask_email('a@example.com'), '*@example.com')
    
    def test_mask_phone(self):
        """Test de masquage de téléphone."""
        self.assertEqual(mask_phone('0123456789'), '01****89')
        self.assertEqual(mask_phone('123'), '***')
        self.assertEqual(mask_phone(''), '')


class FileUploadValidatorTestCase(TestCase):
    """Tests pour le validator de fichiers."""
    
    def setUp(self):
        self.validator = FileUploadValidator()
    
    def test_valid_file(self):
        """Test avec un fichier valide."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(b'test content')
            tmp_file.flush()
            
            # Simuler un fichier uploadé
            class MockFile:
                def __init__(self, name, size):
                    self.name = name
                    self.size = size
            
            mock_file = MockFile('test.pdf', 1024)
            
            try:
                self.validator(mock_file)
            except ValidationError:
                self.fail("Le fichier devrait être valide")
            
            os.unlink(tmp_file.name)
    
    def test_invalid_extension(self):
        """Test avec une extension invalide."""
        class MockFile:
            def __init__(self, name, size):
                self.name = name
                self.size = size
        
        mock_file = MockFile('test.exe', 1024)
        
        with self.assertRaises(ValidationError):
            self.validator(mock_file)
    
    def test_file_too_large(self):
        """Test avec un fichier trop volumineux."""
        class MockFile:
            def __init__(self, name, size):
                self.name = name
                self.size = size
        
        mock_file = MockFile('test.pdf', 20 * 1024 * 1024)  # 20MB
        
        with self.assertRaises(ValidationError):
            self.validator(mock_file)
