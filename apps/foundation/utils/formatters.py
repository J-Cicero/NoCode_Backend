
import re
from datetime import datetime
from django.utils import timezone


def format_phone_number(phone, format_type='international'):

    if not phone:
        return ''
    
    clean_phone = re.sub(r'[^\d+]', '', str(phone))
    
    # Normaliser au format français
    if clean_phone.startswith('+33'):
        digits = clean_phone[3:]
    elif clean_phone.startswith('33'):
        digits = clean_phone[2:]
    elif clean_phone.startswith('0'):
        digits = clean_phone[1:]
    else:
        digits = clean_phone
    
    if len(digits) != 9:
        return phone  # Retourner tel quel si format invalide
    
    if format_type == 'international':
        return f"+33 {digits[0]} {digits[1:3]} {digits[3:5]} {digits[5:7]} {digits[7:9]}"
    elif format_type == 'national':
        return f"0{digits[0]} {digits[1:3]} {digits[3:5]} {digits[5:7]} {digits[7:9]}"
    elif format_type == 'compact':
        return f"+33{digits}"
    else:
        return phone


def format_siret(siret):
    """
    Formate un numéro SIRET.
    """
    if not siret:
        return ''
    
    # Nettoyer le SIRET
    clean_siret = re.sub(r'[^\d]', '', str(siret))
    
    if len(clean_siret) != 14:
        return siret  # Retourner tel quel si format invalide
    
    # Format: XXX XXX XXX XXXXX
    return f"{clean_siret[:3]} {clean_siret[3:6]} {clean_siret[6:9]} {clean_siret[9:]}"


def format_date_french(date, format_type='long'):
    """
    Formate une date au format français.
    """
    if not date:
        return ''
    
    if isinstance(date, str):
        try:
            date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        except:
            return date
    
    if hasattr(date, 'astimezone'):
        # Convertir en timezone locale
        date = date.astimezone(timezone.get_current_timezone())
    
    months_fr = [
        'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
        'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
    ]
    
    if format_type == 'long':
        return f"{date.day} {months_fr[date.month - 1]} {date.year}"
    elif format_type == 'short':
        return f"{date.day:02d}/{date.month:02d}/{date.year}"
    elif format_type == 'medium':
        return f"{date.day} {months_fr[date.month - 1][:3]}. {date.year}"
    else:
        return date.strftime('%d/%m/%Y')


def format_currency_french(amount, currency='EUR', show_symbol=True):
    """
    Formate un montant en devise française.
    """
    if amount is None:
        return '0,00 €' if show_symbol else '0,00'
    
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        amount = 0.0
    
    # Formatage français avec virgule comme séparateur décimal
    formatted = f"{amount:,.2f}".replace(',', ' ').replace('.', ',')
    
    if show_symbol:
        if currency.upper() == 'EUR':
            return f"{formatted} €"
        else:
            return f"{formatted} {currency}"
    
    return formatted


def truncate_text(text, max_length=100, suffix='...'):
    """
    Tronque un texte à une longueur maximale.
    """
    if not text:
        return ''
    
    text = str(text)
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_file_size(size_bytes):
    """
    Formate une taille de fichier en unités lisibles.
    """
    if not size_bytes:
        return '0 B'
    
    try:
        size_bytes = int(size_bytes)
    except (ValueError, TypeError):
        return '0 B'
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"


def format_percentage(value, decimal_places=1):
    """
    Formate un pourcentage.
    """
    if value is None:
        return '0%'
    
    try:
        value = float(value)
    except (ValueError, TypeError):
        value = 0.0
    
    return f"{value:.{decimal_places}f}%"


def format_duration(seconds):
    """
    Formate une durée en secondes en format lisible.
    """
    if not seconds:
        return '0 seconde'
    
    try:
        seconds = int(seconds)
    except (ValueError, TypeError):
        return '0 seconde'
    
    if seconds < 60:
        return f"{seconds} seconde{'s' if seconds > 1 else ''}"
    
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    
    if minutes < 60:
        if remaining_seconds == 0:
            return f"{minutes} minute{'s' if minutes > 1 else ''}"
        else:
            return f"{minutes}m {remaining_seconds}s"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if hours < 24:
        if remaining_minutes == 0:
            return f"{hours} heure{'s' if hours > 1 else ''}"
        else:
            return f"{hours}h {remaining_minutes}m"
    
    days = hours // 24
    remaining_hours = hours % 24
    
    if remaining_hours == 0:
        return f"{days} jour{'s' if days > 1 else ''}"
    else:
        return f"{days}j {remaining_hours}h"


def format_address(address_dict):
    """
    Formate une adresse complète.
    """
    if not address_dict:
        return ''
    
    parts = []
    
    # Numéro et rue
    if address_dict.get('street_number') and address_dict.get('street_name'):
        parts.append(f"{address_dict['street_number']} {address_dict['street_name']}")
    elif address_dict.get('street_name'):
        parts.append(address_dict['street_name'])
    
    # Complément d'adresse
    if address_dict.get('complement'):
        parts.append(address_dict['complement'])
    
    # Code postal et ville
    city_line = []
    if address_dict.get('postal_code'):
        city_line.append(address_dict['postal_code'])
    if address_dict.get('city'):
        city_line.append(address_dict['city'])
    
    if city_line:
        parts.append(' '.join(city_line))
    
    # Pays (si différent de France)
    if address_dict.get('country') and address_dict['country'].upper() != 'FRANCE':
        parts.append(address_dict['country'])
    
    return '\n'.join(parts)


def format_iban(iban):
    """
    Formate un IBAN avec des espaces.
    """
    if not iban:
        return ''
    
    # Nettoyer l'IBAN
    clean_iban = re.sub(r'[^\w]', '', str(iban)).upper()
    
    # Ajouter des espaces tous les 4 caractères
    formatted_parts = []
    for i in range(0, len(clean_iban), 4):
        formatted_parts.append(clean_iban[i:i+4])
    
    return ' '.join(formatted_parts)
