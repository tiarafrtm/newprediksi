from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import PropertyRepository
from app.services.ai_service import gemini_chat_response
from app.services.ml_service import ml_service

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Homepage with search functionality"""
    properties = PropertyRepository.load_properties()
    featured_properties = properties[:6]  # Show first 6 as featured
    return render_template('index.html', properties=featured_properties)

@main_bp.route('/properties')
def properties():
    """Property listings page"""
    properties = PropertyRepository.load_properties()
    
    # Apply filters
    budget_min = request.args.get('budget_min', type=int)
    budget_max = request.args.get('budget_max', type=int)
    kecamatan = request.args.get('kecamatan', type=str)
    
    filtered_properties = properties
    if budget_min:
        filtered_properties = [p for p in filtered_properties if p.get('harga', 0) >= budget_min]
    if budget_max:
        filtered_properties = [p for p in filtered_properties if p.get('harga', 0) <= budget_max]
    if kecamatan:
        filtered_properties = [p for p in filtered_properties if p.get('kecamatan', '').strip().lower() == kecamatan.strip().lower()]
    
    return render_template('properties.html', properties=filtered_properties)

@main_bp.route('/property/<property_id>')
def property_detail(property_id):
    """Property detail page"""
    property_data = PropertyRepository.get_property_by_id(property_id)
    
    if not property_data:
        flash('Property not found')
        return redirect(url_for('main.properties'))
    
    # Get similar properties
    all_properties = PropertyRepository.load_properties()
    similar_properties = [p for p in all_properties if p['id'] != property_id][:3]
    
    return render_template('property_detail.html', property=property_data, similar_properties=similar_properties)

@main_bp.route('/predict', methods=['GET', 'POST'])
def predict():
    """Property price prediction page"""
    price_range = None
    similar_properties = []
    
    if request.method == 'POST':
        # Get form data
        property_data = {
            'luas_tanah': float(request.form.get('luas_tanah', 0)),
            'luas_bangunan': float(request.form.get('luas_bangunan', 0)),
            'kamar_tidur': int(request.form.get('kamar_tidur', 2)),
            'kamar_mandi': int(request.form.get('kamar_mandi', 1)),
            'carport': int(request.form.get('carport', 0)),
            'tahun_dibangun': int(request.form.get('tahun_dibangun', 2020)),
            'lantai': int(request.form.get('lantai', 1)),
            'jarak_sekolah': float(request.form.get('jarak_sekolah', 1000)),
            'jarak_rs': float(request.form.get('jarak_rs', 2000)),
            'jarak_pasar': float(request.form.get('jarak_pasar', 1500)),
            'jenis_jalan': request.form.get('jenis_jalan'),
            'kondisi': request.form.get('kondisi'),
            'sertifikat': request.form.get('sertifikat')
        }
        
        # Get price prediction
        predicted_price = ml_service.predict_price(property_data)
        
        if predicted_price:
            # Calculate price range (±20% from predicted)
            variation = predicted_price * 0.2
            price_range = {
                'min_price': max(0, predicted_price - variation),
                'max_price': predicted_price + variation,
                'predicted_price': predicted_price,
                'formatted_predicted': f"Rp {predicted_price:,.0f}".replace(',', '.'),
                'formatted_min': f"Rp {max(0, predicted_price - variation):,.0f}".replace(',', '.'),
                'formatted_max': f"Rp {predicted_price + variation:,.0f}".replace(',', '.')
            }
            
            # Find similar properties within 30% of predicted price
            all_properties = PropertyRepository.load_properties()
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
    
    return render_template('predict.html', price_range=price_range, similar_properties=similar_properties)

