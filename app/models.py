import json
import os
from typing import List, Dict, Optional
from app.config import Config

class PropertyRepository:
    """Handle property data operations"""
    
    @staticmethod
    def load_properties() -> List[Dict]:
        """Load properties from JSON file"""
        try:
            with open('data/properties.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    @staticmethod
    def save_properties(properties: List[Dict]) -> None:
        """Save properties to JSON file"""
        with open('data/properties.json', 'w') as f:
            json.dump(properties, f, indent=2)
    
    @staticmethod
    def get_property_by_id(property_id: str) -> Optional[Dict]:
        """Get property by ID"""
        properties = PropertyRepository.load_properties()
        return next((p for p in properties if p['id'] == property_id), None)
    
    @staticmethod
    def add_property(property_data: Dict) -> None:
        """Add new property"""
        properties = PropertyRepository.load_properties()
        properties.append(property_data)
        PropertyRepository.save_properties(properties)
    
    @staticmethod
    def update_property(property_id: str, updated_data: Dict) -> bool:
        """Update existing property"""
        properties = PropertyRepository.load_properties()
        for i, property_data in enumerate(properties):
            if property_data['id'] == property_id:
                # Keep the original ID and created_at
                updated_data['id'] = property_id
                if 'created_at' not in updated_data and 'created_at' in property_data:
                    updated_data['created_at'] = property_data['created_at']
                properties[i] = updated_data
                PropertyRepository.save_properties(properties)
                return True
        return False

    @staticmethod
    def delete_property(property_id: str) -> bool:
        """Delete property by ID"""
        properties = PropertyRepository.load_properties()
        original_count = len(properties)
        properties = [p for p in properties if p['id'] != property_id]
        
        if len(properties) < original_count:
            PropertyRepository.save_properties(properties)
            return True
        return False

def encode_categorical(value: str, mapping: Dict[str, int]) -> int:
    """Encode categorical values using provided mapping"""
    return mapping.get(value, 0)

class BasePriceRepository:
    """Handle base price settings for predictions"""
    
    @staticmethod
    def load_base_prices() -> Dict:
        """Load base price settings from JSON file"""
        try:
            with open('data/base_prices.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default base prices
            default_prices = {
                'base_price_per_sqm_land': 500000,  # Rp per m2 tanah
                'base_price_per_sqm_building': 2000000,  # Rp per m2 bangunan
                'room_multiplier': 50000000,  # Bonus per kamar
                'bathroom_multiplier': 25000000,  # Bonus per kamar mandi
                'floor_multiplier': 10000000,  # Bonus per lantai
                'carport_multiplier': 15000000,  # Bonus per carport
                'year_bonus_per_year': 2000000,  # Bonus per tahun setelah 2000
                'condition_multipliers': {
                    'baru': 1.3,
                    'baik': 1.0,
                    'renovasi_ringan': 0.8,
                    'butuh_renovasi': 0.6
                },
                'road_multipliers': {
                    'jalan_besar': 1.2,
                    'jalan_sedang': 1.0,
                    'gang_kecil': 0.8
                },
                'certificate_multipliers': {
                    'shm': 1.1,
                    'hgb': 1.0,
                    'girik': 0.9
                }
            }
            BasePriceRepository.save_base_prices(default_prices)
            return default_prices
    
    @staticmethod
    def save_base_prices(base_prices: Dict) -> bool:
        """Save base price settings to JSON file"""
        try:
            # Ensure the data directory exists
            os.makedirs('data', exist_ok=True)
            
            with open('data/base_prices.json', 'w') as f:
                json.dump(base_prices, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving base prices: {e}")
            return False
    
    @staticmethod
    def update_base_prices(updated_data: Dict) -> bool:
        """Update base price settings"""
        try:
            current_prices = BasePriceRepository.load_base_prices()
            current_prices.update(updated_data)
            BasePriceRepository.save_base_prices(current_prices)
            return True
        except Exception as e:
            print(f"Error updating base prices: {e}")
            return False