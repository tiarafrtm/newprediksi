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
    """Enhanced AI-powered property search with clean deterministic filtering"""

    @staticmethod
    def search_properties(query: str) -> Dict:
        """
        Search properties using clean NLP extraction and scoring
        Returns: Dict with properties, explanation, and ai_powered flag
        """
        if not query.strip():
            properties = PropertyRepository.load_properties()[:6]
            return {
                'properties': properties,
                'explanation': 'Menampilkan beberapa properti terbaru.',
                'ai_powered': False
            }

        # Check for non-property queries
        if AIPropertySearch._is_non_property_query(query):
            return {
                'properties': [],
                'explanation': 'Silakan berikan kriteria pencarian properti yang lebih spesifik, seperti budget, jumlah kamar, atau lokasi yang diinginkan.',
                'ai_powered': True
            }

        # Load all properties
        all_properties = PropertyRepository.load_properties()

        # Extract search criteria using NLP
        criteria = extract_search_criteria(query)
        print(f"Extracted criteria: {criteria}")  # Debug

        # Apply filtering and scoring
        filtered_properties = filter_properties_strict(all_properties, criteria)
        print(f"Filtered results: {len(filtered_properties)} properties")  # Debug

        # If we have results, return them
        if filtered_properties:
            result_count = min(len(filtered_properties), 6)
            explanation = AIPropertySearch._generate_explanation(criteria, len(filtered_properties))

            return {
                'properties': filtered_properties[:result_count],
                'explanation': explanation,
                'ai_powered': True
            }

        # No results found - return empty with helpful message
        return {
            'properties': [],
            'explanation': 'Tidak ada properti yang sesuai dengan kriteria pencarian Anda. Coba ubah kriteria seperti budget atau lokasi.',
            'ai_powered': True
        }

    @staticmethod
    def _is_non_property_query(query: str) -> bool:
        """Check if query is non-property related"""
        non_property_queries = ['hai', 'hello', 'halo', 'hi', 'apa kabar', 'terima kasih', 'thanks', 'bye', 'selamat pagi', 'selamat siang', 'selamat malam']
        return query.lower().strip() in non_property_queries

    @staticmethod
    def _generate_explanation(criteria: Dict, total_found: int) -> str:
        """Generate human-friendly explanation based on criteria"""
        parts = []

        if 'budget' in criteria:
            budget = criteria['budget']
            parts.append(f"budget sekitar Rp {budget:,.0f}".replace(',', '.'))

        if 'kamar_tidur' in criteria:
            parts.append(f"{criteria['kamar_tidur']} kamar tidur")

        if 'kamar_mandi' in criteria:
            parts.append(f"{criteria['kamar_mandi']} kamar mandi")

        if 'kelurahan' in criteria:
            parts.append(f"di kelurahan {criteria['kelurahan']}")
        elif 'kecamatan' in criteria:
            parts.append(f"di kecamatan {criteria['kecamatan']}")

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
            model="gemini-2.5-flash",
            contents=[
                types.Content(role="user", parts=[types.Part(text=f"{system_prompt}\n\nUser question: {message}")])
            ]
        )

        return response.text if response.text else "Maaf, saya tidak dapat memproses pertanyaan Anda saat ini."

    except Exception as e:
        return "Maaf, terjadi kesalahan pada sistem search. Silakan coba lagi."