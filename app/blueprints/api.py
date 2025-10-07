from flask import Blueprint, jsonify, request
from app.models import PropertyRepository
from app.services.ai_service import AIPropertySearch
from app.services.ml_service import ml_service

api_bp = Blueprint('api', __name__)

@api_bp.route('/properties')
def get_properties():
    """API endpoint for properties"""
    properties = PropertyRepository.load_properties()
    return jsonify(properties)

@api_bp.route('/search_properties', methods=['POST'])
def search_properties():
    """Enhanced AI-powered property search with deterministic filtering"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        print(f"Search query received: {query}")  # Debug log
        
        if not query:
            response_data = {
                'properties': PropertyRepository.load_properties()[:6],
                'explanation': 'Menampilkan beberapa properti terbaru.',
                'ai_powered': False
            }
        else:
            # Use the new AI search service
            response_data = AIPropertySearch.search_properties(query)
        
        # Create response with no-cache headers
        response = jsonify(response_data)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
        
    except Exception as e:
        print(f"Search error: {str(e)}")  # Debug log
        # Fallback to basic properties on error
        error_response = {
            'properties': PropertyRepository.load_properties()[:5],
            'explanation': 'Terjadi kesalahan dalam pencarian. Menampilkan properti terbaru.',
            'ai_powered': False,
            'error': str(e)
        }
        response = jsonify(error_response)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response

@api_bp.route('/predict', methods=['POST'])
def predict_price():
    """API endpoint for price prediction with similar properties"""
    try:
        data = request.get_json()
        
        # Log input data for debugging
        print(f"Prediction input received: {data}")
        print(f"Input keys: {list(data.keys()) if data else 'No data'}")
        print(f"Input values: {list(data.values()) if data else 'No values'}")
        
        # Get price prediction
        predicted_price = ml_service.predict_price(data)
        
        if predicted_price:
            # Calculate price range (±20% from predicted)
            variation = predicted_price * 0.2
            price_range = {
                'min_price': max(0, predicted_price - variation),
                'max_price': predicted_price + variation,
                'predicted_price': predicted_price,
                'formatted': f"Rp {predicted_price:,.0f}".replace(',', '.')
            }
            
            # Find similar properties within 30% of predicted price
            all_properties = PropertyRepository.load_properties()
            similar_properties = []
            price_tolerance = predicted_price * 0.3  # 30% tolerance
            min_similar_price = predicted_price - price_tolerance
            max_similar_price = predicted_price + price_tolerance
            
            for prop in all_properties:
                if prop.get('harga') and prop.get('status') == 'available':
                    prop_price = float(prop['harga'])
                    if min_similar_price <= prop_price <= max_similar_price:
                        similar_properties.append(prop)
            
            # Sort by price difference and limit to 6 properties
            similar_properties.sort(key=lambda p: abs(float(p['harga']) - predicted_price))
            similar_properties = similar_properties[:6]
            
            response_data = {
                'success': True,
                'prediction': price_range,
                'similar_properties': similar_properties,
                'formatted': price_range['formatted'],
                'timestamp': request.args.get('t', '')  # Include timestamp for debugging
            }
            
            print(f"Prediction result: {predicted_price:,.0f}")  # Debug log
            
            # Create response with no-cache headers
            response = jsonify(response_data)
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            
            return response
        else:
            return jsonify({'success': False, 'error': 'Unable to predict price'})
    
    except Exception as e:
        print(f"Prediction error: {str(e)}")  # Debug log
        return jsonify({'success': False, 'error': str(e)})
def predict_price():
    """API endpoint for price prediction"""
    try:
        data = request.get_json()
        prediction = ml_service.predict_price(data)
        
        if prediction:
            return jsonify({
                'prediction': prediction, 
                'formatted': f"Rp {prediction:,.0f}"
            })
        else:
            return jsonify({
                'error': 'Cannot predict price with current data. Please check if all required fields are provided.'
            }), 400
    except Exception as e:
        return jsonify({
            'error': f'Prediction failed: {str(e)}'
        }), 500