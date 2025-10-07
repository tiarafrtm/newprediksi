import re
from urllib.parse import quote_plus

def normalize_indonesian_phone(phone_number):
    """
    Normalize Indonesian phone numbers for WhatsApp links
    Converts various formats to proper international format (62XXXXXXXXX)
    """
    if not phone_number:
        return None
    
    # Remove all non-digit characters
    clean_number = re.sub(r'\D', '', phone_number)
    
    if not clean_number:
        return None
    
    # Handle different formats
    if clean_number.startswith('62'):
        # Already in international format
        return clean_number
    elif clean_number.startswith('0'):
        # Local format (08xxx) -> convert to international (62xxx)
        return '62' + clean_number[1:]
    else:
        # Assume it's missing the country code and leading 0
        return '62' + clean_number
    
def create_whatsapp_link(phone_number, seller_name, property_title):
    """
    Create a properly formatted WhatsApp link with normalized phone and encoded message
    """
    normalized_phone = normalize_indonesian_phone(phone_number)
    
    if not normalized_phone:
        return None
    
    # Create message text
    message = f"Halo {seller_name or 'Penjual'}, saya tertarik dengan properti {property_title} yang sedang dijual. Bisa kita diskusi lebih lanjut?"
    
    # URL encode the message
    encoded_message = quote_plus(message)
    
    # Create WhatsApp link
    whatsapp_link = f"https://wa.me/{normalized_phone}?text={encoded_message}"
    
    return whatsapp_link