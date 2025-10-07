import json
import os
import time
import random
from typing import List, Dict, Optional
from dotenv import load_dotenv
from app.models import PropertyRepository

load_dotenv()

try:
    from google import genai
    from google.genai import types
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and api_key != "your_gemini_api_key_here":
        client = genai.Client(api_key=api_key)
        GEMINI_AVAILABLE = True
    else:
        raise ValueError("GEMINI_API_KEY not found or not configured")
except Exception as e:
    print(f"Gemini AI not available: {e}")
    GEMINI_AVAILABLE = False
    client = None
    types = None

class AIPropertySearch:
    """AI-powered property search using Gemini for natural language understanding"""

    @staticmethod
    def search_properties(query: str) -> Dict:
        """
        Search properties using AI to understand user queries
        Returns: Dict with properties, explanation, and ai_powered flag
        """
        if not query.strip():
            properties = PropertyRepository.load_properties()[:6]
            return {
                'properties': properties,
                'explanation': 'Menampilkan beberapa properti terbaru.',
                'ai_powered': False
            }

        if not GEMINI_AVAILABLE or not client:
            return {
                'properties': [],
                'explanation': 'Sistem AI sedang tidak tersedia. Silakan hubungi admin.',
                'ai_powered': False
            }

        all_properties = PropertyRepository.load_properties()
        available_properties = [p for p in all_properties if p.get('status') == 'available']

        if not available_properties:
            return {
                'properties': [],
                'explanation': 'Tidak ada properti yang tersedia saat ini.',
                'ai_powered': False
            }

        try:
            criteria = AIPropertySearch._extract_criteria_with_ai(query, available_properties)
            print(f"AI Extracted criteria: {criteria}")

            filtered_properties = AIPropertySearch._filter_properties_with_criteria(
                available_properties, criteria
            )
            print(f"Filtered results: {len(filtered_properties)} properties")

            if filtered_properties:
                result_count = min(len(filtered_properties), 6)
                explanation = AIPropertySearch._generate_explanation(criteria, len(filtered_properties))

                return {
                    'properties': filtered_properties[:result_count],
                    'explanation': explanation,
                    'ai_powered': True
                }
            else:
                return {
                    'properties': [],
                    'explanation': 'Tidak ada properti yang sesuai dengan kriteria Anda. Coba ubah kriteria pencarian.',
                    'ai_powered': True
                }

        except Exception as e:
            import traceback
            print(f"AI Search error: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return {
                'properties': available_properties[:6],
                'explanation': f'Terjadi kesalahan dalam pencarian. Menampilkan beberapa properti yang tersedia.',
                'ai_powered': False
            }

    @staticmethod
    def _extract_criteria_with_ai(query: str, properties: List[Dict]) -> Dict:
        """Use Gemini AI to extract search criteria from natural language query"""
        
        prices = [p.get('harga') for p in properties if p.get('harga') is not None and p.get('harga') > 0]
        
        property_schema = {
            "fields": [
                "judul_properti", "kelurahan", "kecamatan", "alamat", "deskripsi",
                "luas_tanah", "luas_bangunan", "kamar_tidur", "kamar_mandi", "carport",
                "tahun_dibangun", "lantai", "harga", "jarak_sekolah", "jarak_rs", "jarak_pasar",
                "jenis_jalan", "kondisi", "sertifikat"
            ],
            "sample_locations": {
                "kelurahan": ["Sukaraja", "Majasari", "Gunung Ibul", "Patih Galung", "Wonosari", 
                             "Gunung Kemala", "Sukajadi", "Karang Bindu", "Tanjung Telang", 
                             "Tanjung Raman", "Cambai", "Muara Dua", "Anak Petai", "Pangkul",
                             "Karang Jaya", "Gunung Ibul Barat", "Mangga"],
                "kecamatan": ["Prabumulih Selatan", "Prabumulih Timur", "Prabumulih Barat",
                             "Prabumulih Utara", "Cambai", "Rambang Kapak Tengah"]
            },
            "price_range": {
                "min": min(prices) if prices else 0,
                "max": max(prices) if prices else 0,
                "avg": sum(prices) / len(prices) if prices else 0
            }
        }

        prompt = f"""Anda adalah asisten AI untuk sistem pencarian properti rumah. Tugas Anda adalah menganalisis pertanyaan pengguna dan mengekstrak kriteria pencarian.

Database Properties memiliki field berikut:
{json.dumps(property_schema['fields'], indent=2)}

Lokasi yang tersedia:
Kelurahan: {', '.join(property_schema['sample_locations']['kelurahan'])}
Kecamatan: {', '.join(property_schema['sample_locations']['kecamatan'])}

Range Harga:
- Minimum: Rp {property_schema['price_range']['min']:,.0f}
- Maximum: Rp {property_schema['price_range']['max']:,.0f}
- Rata-rata: Rp {property_schema['price_range']['avg']:,.0f}

Pertanyaan pengguna: "{query}"

Ekstrak kriteria pencarian dari pertanyaan di atas dan berikan dalam format JSON berikut:
{{
  "budget_min": <angka atau null>,
  "budget_max": <angka atau null>,
  "kamar_tidur": <angka atau null>,
  "kamar_mandi": <angka atau null>,
  "kelurahan": <string atau null>,
  "kecamatan": <string atau null>,
  "luas_tanah_min": <angka atau null>,
  "luas_bangunan_min": <angka atau null>,
  "kondisi": <"baik" atau "sedang" atau "kurang" atau null>,
  "sertifikat": <"SHM" atau "HGB" atau null>,
  "carport": <angka atau null>,
  "jarak_sekolah_max": <angka dalam meter atau null>,
  "jarak_rs_max": <angka dalam meter atau null>,
  "jarak_pasar_max": <angka dalam meter atau null>,
  "price_preference": <"low" untuk murah, "high" untuk mahal, atau null>,
  "search_keywords": [<array kata kunci dari deskripsi/alamat yang dicari>]
}}

Panduan:
- Jika pengguna menyebut "200 jutaan" atau "200 juta", set budget_min=140000000, budget_max=260000000 (±30%)
- Jika pengguna menyebut "milyar" atau "M", kalikan dengan 1000000000
- Jika pengguna menyebut lokasi spesifik, cari di kelurahan/kecamatan
- Jika pengguna menyebut "dekat sekolah/rumah sakit/pasar", set jarak maksimal (contoh: 1000 meter)
- Jika pengguna minta "murah" atau "termurah", set price_preference="low"
- Jika pengguna minta "mewah" atau "mahal", set price_preference="high"
- Ekstrak kata kunci penting untuk mencari di deskripsi/alamat (contoh: "citymall", "dekat", dll)

Hanya berikan JSON, tanpa penjelasan tambahan."""

        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash-exp",
                    contents=prompt
                )
                
                response_text = response.text.strip()
                
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.startswith('```'):
                    response_text = response_text[3:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                
                response_text = response_text.strip()
                
                criteria = json.loads(response_text)
                return criteria

            except Exception as e:
                error_msg = str(e).lower()
                if ('503' in str(e) or 'overloaded' in error_msg or 'unavailable' in error_msg) and attempt < max_retries - 1:
                    wait_time = min(base_delay * (2 ** attempt), 32)
                    jitter = random.uniform(0, 1)
                    sleep_time = wait_time + jitter
                    print(f"Gemini API overloaded (503). Retry {attempt + 1}/{max_retries} in {sleep_time:.1f}s...")
                    time.sleep(sleep_time)
                elif attempt == max_retries - 1:
                    print(f"Error extracting criteria with AI after {max_retries} retries: {str(e)}")
                    return {}
                else:
                    print(f"Error extracting criteria with AI: {str(e)}")
                    return {}

    @staticmethod
    def _filter_properties_with_criteria(properties: List[Dict], criteria: Dict) -> List[Dict]:
        """Filter and score properties based on AI-extracted criteria"""
        
        if not criteria:
            return properties

        scored_properties = []

        for prop in properties:
            score = 0.0
            passes_hard_filters = True

            if criteria.get('budget_min') is not None and criteria.get('budget_max') is not None:
                prop_price = prop.get('harga')
                if prop_price is None or prop_price <= 0:
                    passes_hard_filters = False
                elif prop_price < criteria['budget_min'] or prop_price > criteria['budget_max']:
                    passes_hard_filters = False
                else:
                    budget_center = (criteria['budget_min'] + criteria['budget_max']) / 2
                    price_diff = abs(prop_price - budget_center) / budget_center
                    if price_diff <= 0.1:
                        score += 40
                    elif price_diff <= 0.3:
                        score += 30
                    elif price_diff <= 0.5:
                        score += 20
                    else:
                        score += 10

            if criteria.get('kamar_tidur') is not None:
                prop_rooms = prop.get('kamar_tidur', 0)
                required_rooms = criteria['kamar_tidur']
                if prop_rooms == required_rooms:
                    score += 25
                elif abs(prop_rooms - required_rooms) == 1:
                    score += 12

            if criteria.get('kamar_mandi') is not None:
                prop_bathrooms = prop.get('kamar_mandi', 0)
                required_bathrooms = criteria['kamar_mandi']
                if prop_bathrooms == required_bathrooms:
                    score += 15
                elif abs(prop_bathrooms - required_bathrooms) == 1:
                    score += 7

            if criteria.get('kelurahan'):
                prop_kelurahan = prop.get('kelurahan', '').lower().strip()
                criteria_kelurahan = criteria['kelurahan'].lower().strip()
                if criteria_kelurahan in prop_kelurahan or prop_kelurahan in criteria_kelurahan:
                    score += 20

            if criteria.get('kecamatan'):
                prop_kecamatan = prop.get('kecamatan', '').lower().strip()
                criteria_kecamatan = criteria['kecamatan'].lower().strip()
                if criteria_kecamatan in prop_kecamatan or prop_kecamatan in criteria_kecamatan:
                    score += 20

            if criteria.get('luas_tanah_min') is not None:
                prop_luas = prop.get('luas_tanah', 0)
                if prop_luas >= criteria['luas_tanah_min']:
                    score += 10

            if criteria.get('luas_bangunan_min') is not None:
                prop_luas = prop.get('luas_bangunan', 0)
                if prop_luas >= criteria['luas_bangunan_min']:
                    score += 10

            if criteria.get('kondisi'):
                if prop.get('kondisi', '').lower() == criteria['kondisi'].lower():
                    score += 10

            if criteria.get('sertifikat'):
                if prop.get('sertifikat', '').upper() == criteria['sertifikat'].upper():
                    score += 10

            if criteria.get('carport') is not None:
                if prop.get('carport', 0) >= criteria['carport']:
                    score += 5

            if criteria.get('jarak_sekolah_max') is not None:
                prop_jarak = prop.get('jarak_sekolah', 999999)
                if prop_jarak <= criteria['jarak_sekolah_max']:
                    score += 10

            if criteria.get('jarak_rs_max') is not None:
                prop_jarak = prop.get('jarak_rs', 999999)
                if prop_jarak <= criteria['jarak_rs_max']:
                    score += 10

            if criteria.get('jarak_pasar_max') is not None:
                prop_jarak = prop.get('jarak_pasar', 999999)
                if prop_jarak <= criteria['jarak_pasar_max']:
                    score += 10

            if criteria.get('search_keywords'):
                keywords = criteria['search_keywords']
                prop_text = f"{prop.get('judul_properti', '')} {prop.get('deskripsi', '')} {prop.get('alamat', '')}".lower()
                for keyword in keywords:
                    if keyword.lower() in prop_text:
                        score += 15

            if passes_hard_filters or score > 0:
                scored_properties.append({
                    'property': prop,
                    'score': score
                })

        scored_properties.sort(key=lambda x: x['score'], reverse=True)
        filtered = [item['property'] for item in scored_properties]

        if criteria.get('price_preference'):
            if criteria['price_preference'] == 'low':
                filtered.sort(key=lambda p: p['harga'] if p.get('harga') is not None else float('inf'))
            elif criteria['price_preference'] == 'high':
                filtered.sort(key=lambda p: p['harga'] if p.get('harga') is not None else 0, reverse=True)

        return filtered

    @staticmethod
    def _generate_explanation(criteria: Dict, total_found: int) -> str:
        """Generate human-friendly explanation based on AI-extracted criteria"""
        parts = []

        if criteria.get('budget_min') and criteria.get('budget_max'):
            avg_budget = (criteria['budget_min'] + criteria['budget_max']) / 2
            parts.append(f"budget sekitar Rp {avg_budget:,.0f}".replace(',', '.'))

        if criteria.get('kamar_tidur'):
            parts.append(f"{criteria['kamar_tidur']} kamar tidur")

        if criteria.get('kamar_mandi'):
            parts.append(f"{criteria['kamar_mandi']} kamar mandi")

        if criteria.get('kelurahan'):
            parts.append(f"di kelurahan {criteria['kelurahan']}")
        elif criteria.get('kecamatan'):
            parts.append(f"di kecamatan {criteria['kecamatan']}")

        if criteria.get('kondisi'):
            parts.append(f"kondisi {criteria['kondisi']}")

        if criteria.get('jarak_sekolah_max'):
            parts.append(f"dekat sekolah (< {criteria['jarak_sekolah_max']}m)")

        if criteria.get('search_keywords'):
            keywords_str = ', '.join(criteria['search_keywords'][:3])
            parts.append(f"dengan: {keywords_str}")

        if parts:
            criteria_text = ", ".join(parts)
            return f"Ditemukan {total_found} properti dengan {criteria_text}. Menampilkan {min(total_found, 6)} properti terbaik."
        else:
            return f"Ditemukan {total_found} properti berdasarkan pencarian Anda. Menampilkan {min(total_found, 6)} properti teratas."


def gemini_chat_response(message: str, context: Optional[str] = None) -> str:
    """Generate chatbot response using Gemini AI"""
    if not GEMINI_AVAILABLE or not client:
        return "Maaf, layanan chatbot AI sedang tidak tersedia. Silakan hubungi admin untuk mengkonfigurasi GEMINI_API_KEY."

    try:
        properties = PropertyRepository.load_properties()
        property_context = f"Available properties count: {len(properties)}"
        if properties:
            prices = [float(p.get('harga', 0)) for p in properties if p.get('harga')]
            if prices:
                avg_price = sum(prices) / len(prices)
                property_context += f", Average price: Rp {avg_price:,.0f}"

        system_prompt = f"""You are a helpful real estate assistant for a property recommendation system. 
        Context: {property_context}

        Help users with:
        - Property searches and recommendations
        - Price predictions and market analysis
        - Location and facility information
        - Answering questions about property features

        Be friendly, informative, and helpful. Respond in Bahasa Indonesia when appropriate."""

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[
                types.Content(role="user", parts=[types.Part(text=f"{system_prompt}\n\nUser question: {message}")])
            ]
        )

        return response.text if response.text else "Maaf, saya tidak dapat memproses pertanyaan Anda saat ini."

    except Exception as e:
        print(f"Gemini chat error: {str(e)}")
        return "Maaf, terjadi kesalahan pada sistem chat. Silakan coba lagi."
