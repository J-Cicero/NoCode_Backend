"""
Utilitaires de sécurité pour le module Foundation.
Fournit des fonctions de chiffrement, hachage et validation sécurisée.
"""
import hashlib
import hmac
import secrets
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings


def hash_sensitive_data(data, salt=None):
    """
    Hache des données sensibles avec un salt.
    """
    if not data:
        return None
    
    if salt is None:
        salt = secrets.token_bytes(32)
    elif isinstance(salt, str):
        salt = salt.encode('utf-8')
    
    # Utiliser PBKDF2 pour le hachage
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    key = kdf.derive(str(data).encode('utf-8'))
    
    # Retourner le hash encodé en base64 avec le salt
    return base64.b64encode(salt + key).decode('utf-8')


def verify_hashed_data(data, hashed_data):
    """
    Vérifie des données contre leur hash.
    """
    if not data or not hashed_data:
        return False
    
    try:
        # Décoder le hash
        decoded = base64.b64decode(hashed_data.encode('utf-8'))
        salt = decoded[:32]
        stored_key = decoded[32:]
        
        # Recalculer le hash avec le même salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = kdf.derive(str(data).encode('utf-8'))
        
        # Comparaison sécurisée
        return hmac.compare_digest(stored_key, key)
        
    except Exception:
        return False


def encrypt_data(data, key=None):
    """
    Chiffre des données avec Fernet (AES 128).
    """
    if not data:
        return None
    
    if key is None:
        key = getattr(settings, 'ENCRYPTION_KEY', None)
        if not key:
            raise ValueError("Clé de chiffrement non configurée")
    
    if isinstance(key, str):
        key = key.encode('utf-8')
    
    # Générer une clé Fernet si nécessaire
    if len(key) != 44:  # Longueur d'une clé Fernet encodée en base64
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'stable_salt_for_fernet',  # Salt fixe pour la compatibilité
            iterations=100000,
        )
        derived_key = kdf.derive(key)
        key = base64.urlsafe_b64encode(derived_key)
    
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(str(data).encode('utf-8'))
    
    return base64.b64encode(encrypted_data).decode('utf-8')


def decrypt_data(encrypted_data, key=None):
    """
    Déchiffre des données chiffrées avec Fernet.
    """
    if not encrypted_data:
        return None
    
    if key is None:
        key = getattr(settings, 'ENCRYPTION_KEY', None)
        if not key:
            raise ValueError("Clé de chiffrement non configurée")
    
    if isinstance(key, str):
        key = key.encode('utf-8')
    
    try:
        # Générer une clé Fernet si nécessaire
        if len(key) != 44:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'stable_salt_for_fernet',
                iterations=100000,
            )
            derived_key = kdf.derive(key)
            key = base64.urlsafe_b64encode(derived_key)
        
        fernet = Fernet(key)
        decoded_data = base64.b64decode(encrypted_data.encode('utf-8'))
        decrypted_data = fernet.decrypt(decoded_data)
        
        return decrypted_data.decode('utf-8')
        
    except Exception:
        return None


def generate_secure_token(length=32):
    """
    Génère un token sécurisé.
    """
    return secrets.token_urlsafe(length)


def generate_api_key(prefix='sk_', length=32):
    """
    Génère une clé API sécurisée.
    """
    random_part = secrets.token_urlsafe(length)
    return f"{prefix}{random_part}"


def validate_signature(data, signature, secret_key):
    """
    Valide une signature HMAC.
    """
    if not data or not signature or not secret_key:
        return False
    
    try:
        # Calculer la signature attendue
        if isinstance(data, str):
            data = data.encode('utf-8')
        if isinstance(secret_key, str):
            secret_key = secret_key.encode('utf-8')
        
        expected_signature = hmac.new(
            secret_key,
            data,
            hashlib.sha256
        ).hexdigest()
        
        # Comparaison sécurisée
        return hmac.compare_digest(signature, expected_signature)
        
    except Exception:
        return False


def create_signature(data, secret_key):
    """
    Crée une signature HMAC pour des données.
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    if isinstance(secret_key, str):
        secret_key = secret_key.encode('utf-8')
    
    return hmac.new(
        secret_key,
        data,
        hashlib.sha256
    ).hexdigest()


def sanitize_input(input_string, max_length=1000):
    """
    Nettoie et sécurise une entrée utilisateur.
    """
    if not input_string:
        return ''
    
    # Convertir en string et limiter la longueur
    clean_input = str(input_string)[:max_length]
    
    # Supprimer les caractères de contrôle dangereux
    clean_input = ''.join(char for char in clean_input if ord(char) >= 32 or char in '\n\r\t')
    
    return clean_input.strip()


def generate_csrf_token():
    """
    Génère un token CSRF sécurisé.
    """
    return secrets.token_hex(32)


def constant_time_compare(a, b):
    """
    Compare deux chaînes en temps constant pour éviter les attaques de timing.
    """
    if not isinstance(a, str) or not isinstance(b, str):
        return False
    
    return hmac.compare_digest(a, b)


def hash_password_simple(password, salt=None):
    """
    Hache un mot de passe de manière simple (pour les cas où Django n'est pas disponible).
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Utiliser SHA-256 avec salt
    hash_obj = hashlib.sha256()
    hash_obj.update(salt.encode('utf-8'))
    hash_obj.update(password.encode('utf-8'))
    
    return f"{salt}:{hash_obj.hexdigest()}"


def verify_password_simple(password, hashed_password):
    """
    Vérifie un mot de passe contre son hash simple.
    """
    try:
        salt, hash_value = hashed_password.split(':', 1)
        
        hash_obj = hashlib.sha256()
        hash_obj.update(salt.encode('utf-8'))
        hash_obj.update(password.encode('utf-8'))
        
        return constant_time_compare(hash_obj.hexdigest(), hash_value)
        
    except Exception:
        return False


def generate_otp(length=6):
    """
    Génère un code OTP numérique.
    """
    return ''.join([str(secrets.randbelow(10)) for _ in range(length)])


def mask_email(email):
    """
    Masque une adresse email pour l'affichage.
    """
    if not email or '@' not in email:
        return email
    
    local, domain = email.split('@', 1)
    
    if len(local) <= 2:
        masked_local = '*' * len(local)
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    
    return f"{masked_local}@{domain}"


def mask_phone(phone):
    """
    Masque un numéro de téléphone pour l'affichage.
    """
    if not phone:
        return phone
    
    phone_str = str(phone)
    
    if len(phone_str) <= 4:
        return '*' * len(phone_str)
    
    return phone_str[:2] + '*' * (len(phone_str) - 4) + phone_str[-2:]
