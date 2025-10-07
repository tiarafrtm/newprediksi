import json
import re
import os
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
from app.models import PropertyRepository
from app.utils.search_utils import extract_search_criteria, filter_properties_strict

# Load environment variables
load_dotenv()

# Import Gemini AI integration
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
    """Enhanced AI-powered property search with deterministic filtering"""
    
    @staticmethod
    def search_properties(query: str) -> Dict:
        """
        Search properties using AI with deterministic pre/post filtering
        Returns: Dict with properties, explanation, and ai_powered flag
        """
        if not query.strip():
            return {
                'properties': PropertyRepository.load_properties()[:6],
                'explanation': 'Menampilkan beberapa properti terbaru.',
                'ai_powered': False
            }
        
        properties = PropertyRepository.load_properties()
        
        # Step 1: Pre-filter with deterministic rules
        criteria = extract_search_criteria(query)
        pre_filtered = filter_properties_strict(properties, criteria)
        
        # Step 2: Check for non-property queries
        if AIPropertySearch._is_non_property_query(query):
            return {
                'properties': [],
                'explanation': 'Silakan berikan kriteria pencarian properti yang lebih spesifik, seperti budget, jumlah kamar, atau lokasi yang diinginkan.',
                'ai_powered': True
            }
        
        # Step 3: Use AI if available for context understanding
        if GEMINI_AVAILABLE and client and len(pre_filtered) > 0:
            try:
                ai_result = AIPropertySearch._get_ai_recommendations(query, pre_filtered)
                if ai_result:
                    return ai_result
            except Exception as e:
                print(f"AI search failed: {e}")
        
        # Step 4: Fallback to deterministic results
        return {
            'properties': pre_filtered[:5],
            'explanation': f"Ditemukan {len(pre_filtered)} properti yang sesuai kriteria Anda.",
            'ai_powered': False
        }
    
    @staticmethod
    def _is_non_property_query(query: str) -> bool:
        """Check if query is non-property related"""
        non_property_queries = ['hai', 'hello', 'halo', 'hi', 'apa kabar', 'terima kasih', 'thanks', 'bye']
        return query.lower().strip() in non_property_queries
    
    @staticmethod
    def _get_ai_recommendations(query: str, filtered_properties: List[Dict]) -> Optional[Dict]:
        """Get AI recommendations from pre-filtered properties"""
        if not filtered_properties:
            return None
            
        # Create simplified context for AI
        property_context = []
        for i, prop in enumerate(filtered_properties):
            context_item = {
                'index': i,
                'alamat': prop.get('alamat', 'N/A'),
                'kelurahan': prop.get('kelurahan', 'N/A'),
                'kecamatan': prop.get('kecamatan', 'N/A'),
                'harga': prop.get('harga', 0),
                'kamar_tidur': prop.get('kamar_tidur', 0),
                'kamar_mandi': prop.get('kamar_mandi', 0),
                'luas_tanah': prop.get('luas_tanah', 0),
                'luas_bangunan': prop.get('luas_bangunan', 0),
                'judul_properti': prop.get('judul_properti', 'N/A')
            }
            property_context.append(context_item)
        
        system_prompt = f"""Anda adalah asisten properti yang membantu memilih dari properti yang SUDAH DIFILTER berdasarkan kriteria lokasi dan spesifikasi.

Properti yang tersedia (sudah sesuai kriteria dasar):
{json.dumps(property_context, indent=2)}

Query pengguna: "{query}"

TUGAS: Pilih maksimal 3 properti TERBAIK dari list di atas yang paling sesuai dengan query.

ATURAN PRIORITAS:
- HANYA pilih dari properti yang sudah disediakan (index 0 hingga {len(filtered_properties)-1})
- Jika query menyebutkan lokasi spesifik (kelurahan/daerah) → prioritaskan lokasi yang sama
- Jika query menyebutkan "murah" → pilih yang harga terendah
- Jika query menyebutkan "besar" → pilih yang luas terbesar
- Jika query menyebutkan jumlah kamar → prioritaskan yang sesuai
- Jika tidak ada preferensi khusus → pilih yang paling sesuai konteks

CONTOH KELURAHAN:
- "gunung ibul" = properti di Gunung Ibul
- "patih galung" = properti di Patih Galung
- "majasari" = properti di Majasari
- "sukajadi" = properti di Sukajadi
- "muara dua" = properti di Muara Dua
- "wonosari" = properti di Wonosari
- "cambai" = properti di Cambai

CONTOH KECAMATAN:
- "prabumulih timur" = properti di Kecamatan Prabumulih Timur
- "prabumulih barat" = properti di Kecamatan Prabumulih Barat
- "prabumulih selatan" = properti di Kecamatan Prabumulih Selatan
- "prabumulih utara" = properti di Kecamatan Prabumulih Utara
- "cambai" = properti di Kecamatan Cambai
- "rambang kapak tengah" = properti di Kecamatan Rambang Kapak Tengah

Responlah HANYA dengan format JSON:
{{"property_indices": [0, 1, 2], "explanation": "Penjelasan singkat mengapa dipilih berdasarkan kriteria lokasi dan spesifikasi"}}"""

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[types.Content(role="user", parts=[types.Part(text=system_prompt)])]
            )
            
            if response.text:
                ai_result = json.loads(response.text.strip())
                selected_indices = ai_result.get('property_indices', [])
                explanation = ai_result.get('explanation', '')
                
                # Validate indices and get properties
                selected_properties = []
                for idx in selected_indices:
                    if 0 <= idx < len(filtered_properties):
                        selected_properties.append(filtered_properties[idx])
                
                return {
                    'properties': selected_properties,
                    'explanation': explanation if selected_properties else "Tidak ada properti yang sesuai dengan kriteria pencarian Anda.",
                    'ai_powered': True
                }
        except (json.JSONDecodeError, Exception):
            pass
        
        return None

def gemini_chat_response(message: str, context: Optional[str] = None) -> str:
    """Generate chatbot response using Gemini AI"""
    if not GEMINI_AVAILABLE or not client:
        return "Maaf, layanan chatbot AI sedang tidak tersedia. Silakan hubungi admin untuk mengkonfigurasi GEMINI_API_KEY."
    
    try:
        # Create context about properties
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
            model="gemini-2.5-flash",
            contents=[
                types.Content(role="user", parts=[types.Part(text=f"{system_prompt}\n\nUser question: {message}")])
            ]
        )
        
        return response.text if response.text else "Maaf, saya tidak dapat memproses pertanyaan Anda saat ini."
        
    except Exception as e:
        return "Maaf, terjadi kesalahan pada sistem search. Silakan coba lagi."