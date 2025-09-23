"""
Fonctions utilitaires et helpers pour le module Foundation.
"""
import os
import re
import uuid
import hashlib
import secrets
from datetime import datetime, timezone
from decimal import Decimal
from django.utils import timezone as django_timezone
from django.conf import settings


def generate_unique_token(length=32):
    """
    Génère un token unique sécurisé.
    """
    return secrets.token_urlsafe(length)


def generate_uuid():
    """
    Génère un UUID4 unique.
    """
    return str(uuid.uuid4())


def format_currency(amount, currency='EUR'):
    """
    Formate un montant en devise.
    """
    if not isinstance(amount, (int, float, Decimal)):
        return "0,00 €"
    
    amount = float(amount)
    
    if currency.upper() == 'EUR':
        return f"{amount:,.2f} €".replace(',', ' ').replace('.', ',')
    else:
        return f"{amount:,.2f} {currency}"


def calculate_tax(amount_ht, tax_rate=0.20):
    """
    Calcule la TVA et le montant TTC.
    """
    if not isinstance(amount_ht, (int, float, Decimal)):
        amount_ht = 0
    
    amount_ht = Decimal(str(amount_ht))
    tax_rate = Decimal(str(tax_rate))
    
    tax_amount = amount_ht * tax_rate
    amount_ttc = amount_ht + tax_amount
    
    return {
        'amount_ht': float(amount_ht),
        'tax_amount': float(tax_amount),
        'amount_ttc': float(amount_ttc),
        'tax_rate': float(tax_rate)
    }


def sanitize_filename(filename):
    """
    Nettoie un nom de fichier pour le rendre sûr.
    """
    if not filename:
        return 'unnamed_file'
    
    # Supprimer les caractères dangereux
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Limiter la longueur
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    return f"{name}{ext}"


def extract_file_metadata(file):
    """
    Extrait les métadonnées d'un fichier.
    """
    metadata = {
        'name': file.name if hasattr(file, 'name') else 'unknown',
        'size': file.size if hasattr(file, 'size') else 0,
        'content_type': getattr(file, 'content_type', 'application/octet-stream'),
    }
    
    # Ajouter l'extension
    if metadata['name']:
        _, ext = os.path.splitext(metadata['name'])
        metadata['extension'] = ext.lower()
    
    # Calculer le hash du fichier
    if hasattr(file, 'read'):
        file.seek(0)
        content = file.read()
        metadata['sha256'] = hashlib.sha256(content).hexdigest()
        file.seek(0)  # Remettre le curseur au début
    
    return metadata


def generate_invoice_number(organization_id=None, date=None):
    """
    Génère un numéro de facture unique.
    """
    if date is None:
        date = django_timezone.now()
    
    year = date.year
    month = date.month
    
    # Format: YYYY-MM-ORG-XXXXX
    org_part = f"{organization_id:04d}" if organization_id else "0000"
    timestamp_part = int(date.timestamp() * 1000) % 100000
    
    return f"{year}-{month:02d}-{org_part}-{timestamp_part:05d}"


def slugify_text(text, max_length=50):
    """
    Convertit un texte en slug.
    """
    if not text:
        return ''
    
    # Convertir en minuscules et remplacer les espaces
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    
    # Limiter la longueur
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')
    
    return slug


def parse_phone_number(phone):
    """
    Parse et normalise un numéro de téléphone français.
    """
    if not phone:
        return None
    
    # Supprimer tous les caractères non numériques sauf le +
    phone = re.sub(r'[^\d+]', '', str(phone))
    
    # Convertir les formats français
    if phone.startswith('0'):
        phone = '+33' + phone[1:]
    elif phone.startswith('33'):
        phone = '+' + phone
    elif not phone.startswith('+'):
        phone = '+33' + phone
    
    return phone


def calculate_age(birth_date):
    """
    Calcule l'âge à partir d'une date de naissance.
    """
    if not birth_date:
        return None
    
    today = datetime.now().date()
    if hasattr(birth_date, 'date'):
        birth_date = birth_date.date()
    
    age = today.year - birth_date.year
    
    # Ajuster si l'anniversaire n'est pas encore passé cette année
    if today < birth_date.replace(year=today.year):
        age -= 1
    
    return age


def mask_sensitive_data(data, mask_char='*', visible_chars=4):
    """
    Masque les données sensibles.
    """
    if not data:
        return data
    
    data_str = str(data)
    
    if len(data_str) <= visible_chars:
        return mask_char * len(data_str)
    
    visible_start = visible_chars // 2
    visible_end = visible_chars - visible_start
    
    masked_middle = mask_char * (len(data_str) - visible_chars)
    
    return data_str[:visible_start] + masked_middle + data_str[-visible_end:]


def generate_reference_number(prefix='REF', length=8):
    """
    Génère un numéro de référence unique.
    """
    timestamp = int(datetime.now().timestamp())
    random_part = secrets.randbelow(10**(length-6))
    
    return f"{prefix}{timestamp % 1000000:06d}{random_part:0{length-6}d}"


def validate_json_structure(data, required_fields):
    """
    Valide la structure d'un objet JSON.
    """
    if not isinstance(data, dict):
        return False, "Les données doivent être un objet JSON"
    
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    
    if missing_fields:
        return False, f"Champs manquants: {', '.join(missing_fields)}"
    
    return True, "Structure valide"


def deep_merge_dict(dict1, dict2):
    """
    Fusionne récursivement deux dictionnaires.
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dict(result[key], value)
        else:
            result[key] = value
    
    return result


def chunk_list(lst, chunk_size):
    """
    Divise une liste en chunks de taille donnée.
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def safe_int(value, default=0):
    """
    Convertit une valeur en entier de manière sécurisée.
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    """
    Convertit une valeur en float de manière sécurisée.
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def get_client_ip(request):
    """
    Récupère l'adresse IP réelle du client.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def is_valid_uuid(uuid_string):
    """
    Vérifie si une chaîne est un UUID valide.
    """
    try:
        uuid.UUID(str(uuid_string))
        return True
    except (ValueError, TypeError):
        return False
