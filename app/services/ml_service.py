import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import pickle
from typing import Optional, Dict, Any
from app.models import PropertyRepository, BasePriceRepository, encode_categorical
from app.config import Config

class MLPredictionService:
    """Machine Learning service for property price prediction"""
    
    def __init__(self):
        self.model: Optional[RandomForestRegressor] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_columns = Config.FEATURE_COLUMNS
    
    def prepare_ml_data(self) -> Optional[pd.DataFrame]:
        """Prepare data for machine learning"""
        properties = PropertyRepository.load_properties()
        if len(properties) < 5:  # Need minimum data for training
            return None
        
        # Prepare dataset
        data = []
        for prop in properties:
            if prop.get('harga') and all(key in prop for key in ['luas_tanah', 'luas_bangunan']):
                row = [
                    float(prop['luas_tanah']),
                    float(prop['luas_bangunan']),
                    int(prop.get('kamar_tidur', 2)),
                    int(prop.get('kamar_mandi', 1)),
                    int(prop.get('carport', 0)),
                    int(prop.get('tahun_dibangun', 2020)),
                    int(prop.get('lantai', 1)),
                    float(prop.get('jarak_sekolah', 1000)),
                    float(prop.get('jarak_rs', 2000)),
                    float(prop.get('jarak_pasar', 1500)),
                    encode_categorical(prop.get('jenis_jalan'), Config.JENIS_JALAN_MAP),
                    encode_categorical(prop.get('kondisi'), Config.KONDISI_MAP),
                    encode_categorical(prop.get('sertifikat'), Config.SERTIFIKAT_MAP),
                    float(prop['harga'])
                ]
                data.append(row)
        
        if len(data) < 5:
            return None
            
        columns = self.feature_columns + ['harga']
        df = pd.DataFrame(data, columns=columns)
        return df
    
    def train_model(self) -> bool:
        """Train the machine learning model"""
        df = self.prepare_ml_data()
        if df is None:
            return False
        
        # Prepare features and target
        X = df[self.feature_columns]
        y = df['harga']
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model.fit(X_scaled, y)
        
        # Save model
        try:
            with open('models/price_model.pkl', 'wb') as f:
                pickle.dump({'model': self.model, 'scaler': self.scaler}, f)
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def load_model(self) -> bool:
        """Load the trained ML model"""
        try:
            with open('models/price_model.pkl', 'rb') as f:
                model_data = pickle.load(f)
                self.model = model_data['model']
                self.scaler = model_data['scaler']
            return True
        except FileNotFoundError:
            return self.train_model()
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def predict_price(self, property_data: Dict[str, Any]) -> Optional[float]:
        """Predict house price using 100% Machine Learning model"""
        # Use pure ML prediction
        ml_prediction = self._get_ml_prediction(property_data)
        return ml_prediction
    
    def _get_ml_prediction(self, property_data: Dict[str, Any]) -> Optional[float]:
        """Get ML model prediction"""
        if self.model is None:
            if not self.load_model():
                return None
        
        # Prepare input data
        tahun_dibangun = int(property_data.get('tahun_dibangun', 2020))
        
        features = [
            float(property_data.get('luas_tanah', 100)),
            float(property_data.get('luas_bangunan', 80)),
            int(property_data.get('kamar_tidur', 2)),
            int(property_data.get('kamar_mandi', 1)),
            int(property_data.get('carport', 0)),
            tahun_dibangun,
            int(property_data.get('lantai', 1)),
            float(property_data.get('jarak_sekolah', 1000)),
            float(property_data.get('jarak_rs', 2000)),
            float(property_data.get('jarak_pasar', 1500)),
            encode_categorical(property_data.get('jenis_jalan'), Config.JENIS_JALAN_MAP),
            encode_categorical(property_data.get('kondisi'), Config.KONDISI_MAP),
            encode_categorical(property_data.get('sertifikat'), Config.SERTIFIKAT_MAP)
        ]
        
        print(f"Debug ML - Year built feature: {tahun_dibangun}")
        
        # Scale and predict
        if self.scaler is not None and self.model is not None:
            try:
                features_scaled = self.scaler.transform([features])
                prediction = self.model.predict(features_scaled)[0]
                return max(0, prediction)
            except Exception as e:
                print(f"Error predicting price: {e}")
                return None
        
        return None
    
    def _get_base_price_prediction(self, property_data: Dict[str, Any]) -> Optional[float]:
        """Calculate price using base price methodology"""
        try:
            base_prices = BasePriceRepository.load_base_prices()
            
            # Basic calculation
            luas_tanah = float(property_data.get('luas_tanah', 100))
            luas_bangunan = float(property_data.get('luas_bangunan', 80))
            kamar_tidur = int(property_data.get('kamar_tidur', 2))
            kamar_mandi = int(property_data.get('kamar_mandi', 1))
            lantai = int(property_data.get('lantai', 1))
            tahun_dibangun = int(property_data.get('tahun_dibangun', 2020))
            
            # Base price calculation
            land_value = luas_tanah * base_prices['base_price_per_sqm_land']
            building_value = luas_bangunan * base_prices['base_price_per_sqm_building']
            room_bonus = kamar_tidur * base_prices['room_multiplier']
            bathroom_bonus = kamar_mandi * base_prices['bathroom_multiplier']
            floor_bonus = lantai * base_prices.get('floor_multiplier', 10000000)  # Default 10M per floor
            
            # Calculate age factor - newer buildings are more valuable
            current_year = 2025
            building_age = current_year - tahun_dibangun
            
            # Age multiplier: newer = higher value, older = lower value
            # Buildings 0-5 years: 100% value
            # Buildings 6-10 years: 95% value  
            # Buildings 11-15 years: 90% value
            # Buildings 16-20 years: 85% value
            # Buildings >20 years: 80% value
            if building_age <= 5:
                age_multiplier = 1.0
            elif building_age <= 10:
                age_multiplier = 0.95
            elif building_age <= 15:
                age_multiplier = 0.90
            elif building_age <= 20:
                age_multiplier = 0.85
            else:
                age_multiplier = 0.80
            
            print(f"Debug - Year built: {tahun_dibangun}, Age: {building_age}, Age multiplier: {age_multiplier}")
            
            base_total = (land_value + building_value + room_bonus + bathroom_bonus + floor_bonus) * age_multiplier
            
            # Apply multipliers
            kondisi = property_data.get('kondisi', 'baik')
            condition_mult = base_prices['condition_multipliers'].get(kondisi, 1.0)
            
            jenis_jalan = property_data.get('jenis_jalan', 'jalan_sedang')
            road_mult = base_prices['road_multipliers'].get(jenis_jalan, 1.0)
            
            sertifikat = property_data.get('sertifikat', 'hgb')
            cert_mult = base_prices['certificate_multipliers'].get(sertifikat, 1.0)
            
            final_price = base_total * condition_mult * road_mult * cert_mult
            
            return max(0, final_price)
            
        except Exception as e:
            print(f"Error calculating base price: {e}")
            return None
    
    def get_price_range(self, property_data: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """Get price range (min, max, predicted)"""
        predicted_price = self.predict_price(property_data)
        if predicted_price is None:
            return None
        
        # Calculate range (±20% from predicted)
        variation = predicted_price * 0.2
        return {
            'min_price': max(0, predicted_price - variation),
            'max_price': predicted_price + variation,
            'predicted_price': predicted_price
        }

# Global ML service instance
ml_service = MLPredictionService()