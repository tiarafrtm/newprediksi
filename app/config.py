import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    SECRET_KEY = os.getenv('SESSION_SECRET')
    if not SECRET_KEY or SECRET_KEY == 'your_session_secret_here_change-this-to-random-string':
        SECRET_KEY = 'dev-secret-key-change-in-production'  # Fallback for development

    UPLOAD_FOLDER = 'static/images'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # ML Model configuration
    FEATURE_COLUMNS = [
        'luas_tanah', 'luas_bangunan', 'kamar_tidur', 'kamar_mandi', 
        'carport', 'tahun_dibangun', 'lantai', 'jarak_sekolah', 'jarak_rs', 
        'jarak_pasar', 'jenis_jalan_encoded', 'kondisi_encoded', 'sertifikat_encoded'
    ]

    # Gemini AI configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

    # Google Maps configuration
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

    # Encoding mappings for categorical variables
    JENIS_JALAN_MAP = {'gang_kecil': 1, 'jalan_sedang': 2, 'jalan_besar': 3}
    KONDISI_MAP = {'butuh_renovasi': 1, 'renovasi_ringan': 2, 'baik': 3, 'baru': 4}
    SERTIFIKAT_MAP = {'girik': 1, 'hgb': 2, 'shm': 3}

    # Prabumulih-specific area mappings
    AREA_MAP = {
        'pusat_kota': 4,        # Pusat Kota Prabumulih
        'karang_raja': 3,       # Karang Raja
        'gunung_ibul': 3,       # Gunung Ibul  
        'rambutan': 2,          # Rambutan
        'tanjung_api': 2,       # Tanjung Api
        'cambai': 1             # Cambai
    }

    # Regional price factors for Prabumulih
    PRABUMULIH_PRICE_FACTORS = {
        'coal_proximity_bonus': 0.1,    # Bonus jika dekat area pertambangan
        'city_center_multiplier': 1.3,   # Multiplier untuk pusat kota
        'education_facility_bonus': 0.05  # Bonus fasilitas pendidikan
    }