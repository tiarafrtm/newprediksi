import uuid
import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from app.models import PropertyRepository, BasePriceRepository # Assuming BasePriceRepository exists
from app.services.ml_service import ml_service
import re

def _parse_price(price_str):
    """Parse price string with robust regex to remove all non-digits"""
    if not price_str:
        return None
    try:
        # Remove all non-digit characters using regex
        cleaned = re.sub(r"[^0-9]", "", str(price_str))
        return int(cleaned) if cleaned else None
    except (ValueError, AttributeError):
        return None

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
def admin_panel():
    """Admin panel dashboard"""
    properties = PropertyRepository.load_properties()
    return render_template('admin/dashboard.html', properties=properties)

@admin_bp.route('/properties')
def properties():
    """Properties management page"""
    properties = PropertyRepository.load_properties()
    return render_template('admin/properties.html', properties=properties)

@admin_bp.route('/add_property', methods=['POST'])
def add_property():
    """Add new property"""
    try:
        # Handle multiple file uploads
        image_filenames = []
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    image_filename = f"{uuid.uuid4()}_{filename}"
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename))
                    image_filenames.append(image_filename)
        
        # Backward compatibility: check for single image upload
        if 'image' in request.files and not image_filenames:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                image_filename = f"{uuid.uuid4()}_{filename}"
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename))
                image_filenames.append(image_filename)

        # Create property data
        property_data = {
            'id': str(uuid.uuid4()),
            'judul_properti': request.form.get('judul_properti'),
            'kelurahan': request.form.get('kelurahan'),
            'kecamatan': request.form.get('kecamatan'),
            'alamat': request.form.get('alamat'),
            'deskripsi': request.form.get('deskripsi', ''),
            'luas_tanah': int(request.form.get('luas_tanah') or 0),
            'luas_bangunan': int(request.form.get('luas_bangunan') or 0),
            'kamar_tidur': int(request.form.get('kamar_tidur') or 2),
            'kamar_mandi': int(request.form.get('kamar_mandi') or 1),
            'carport': int(request.form.get('carport', 0) or 0),
            'tahun_dibangun': int(request.form.get('tahun_dibangun') or 2020),
            'lantai': int(request.form.get('lantai', 1) or 1),
            'kota': request.form.get('kota'),
            'harga': _parse_price(request.form.get('harga')),
            'latitude': float(request.form.get('latitude') or 0) if request.form.get('latitude') else None,
            'longitude': float(request.form.get('longitude') or 0) if request.form.get('longitude') else None,
            'jarak_sekolah': float(request.form.get('jarak_sekolah', 1000) or 1000),
            'jarak_rs': float(request.form.get('jarak_rs', 2000) or 2000),
            'jarak_pasar': float(request.form.get('jarak_pasar', 1500) or 1500),
            'jenis_jalan': request.form.get('jenis_jalan'),
            'kondisi': request.form.get('kondisi'),
            'sertifikat': request.form.get('sertifikat'),
            'nama_penjual': request.form.get('nama_penjual', ''),
            'nomor_penjual': request.form.get('nomor_penjual', ''),
            'images': image_filenames,
            'image': image_filenames[0] if image_filenames else None,  # Backward compatibility
            'created_at': datetime.now().isoformat(),
            'status': 'available'
        }

        # Save property
        PropertyRepository.add_property(property_data)

        # Retrain ML model with new data
        ml_service.train_model()

        flash('Property added successfully!')

    except Exception as e:
        flash(f'Error adding property: {str(e)}')

    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/edit_property/<property_id>')
def edit_property(property_id):
    """Show edit property form"""
    property_data = PropertyRepository.get_property_by_id(property_id)
    if not property_data:
        flash('Property not found')
        return redirect(url_for('admin.admin_panel'))

    return render_template('admin/edit_property.html', property=property_data)

@admin_bp.route('/update_property/<property_id>', methods=['POST'])
def update_property(property_id):
    """Update existing property"""
    try:
        property_data = PropertyRepository.get_property_by_id(property_id)
        if not property_data:
            flash('Property not found')
            return redirect(url_for('admin.admin_panel'))

        # Handle multiple file uploads
        existing_images = property_data.get('images', [])
        if not existing_images and property_data.get('image'):
            # Convert old single image to array format
            existing_images = [property_data.get('image')]
        
        image_filenames = existing_images.copy()  # Keep existing images by default
        
        if 'images' in request.files:
            files = request.files.getlist('images')
            new_images = []
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    image_filename = f"{uuid.uuid4()}_{filename}"
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename))
                    new_images.append(image_filename)
            
            # If new images uploaded, replace all images
            if new_images:
                image_filenames = new_images
        
        # Backward compatibility: check for single image upload
        elif 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                image_filename = f"{uuid.uuid4()}_{filename}"
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename))
                image_filenames = [image_filename]

        # Create updated property data
        updated_data = {
            'judul_properti': request.form.get('judul_properti'),
            'kelurahan': request.form.get('kelurahan'),
            'kecamatan': request.form.get('kecamatan'),
            'alamat': request.form.get('alamat'),
            'deskripsi': request.form.get('deskripsi', ''),
            'luas_tanah': int(request.form.get('luas_tanah') or 0),
            'luas_bangunan': int(request.form.get('luas_bangunan') or 0),
            'kamar_tidur': int(request.form.get('kamar_tidur') or 2),
            'kamar_mandi': int(request.form.get('kamar_mandi') or 1),
            'carport': int(request.form.get('carport', 0) or 0),
            'tahun_dibangun': int(request.form.get('tahun_dibangun') or 2020),
            'lantai': int(request.form.get('lantai', 1) or 1),
            'kota': request.form.get('kota'),
            'harga': _parse_price(request.form.get('harga')),
            'latitude': float(request.form.get('latitude') or 0) if request.form.get('latitude') else None,
            'longitude': float(request.form.get('longitude') or 0) if request.form.get('longitude') else None,
            'jarak_sekolah': float(request.form.get('jarak_sekolah', 1000) or 1000),
            'jarak_rs': float(request.form.get('jarak_rs', 2000) or 2000),
            'jarak_pasar': float(request.form.get('jarak_pasar', 1500) or 1500),
            'jenis_jalan': request.form.get('jenis_jalan'),
            'kondisi': request.form.get('kondisi'),
            'sertifikat': request.form.get('sertifikat'),
            'nama_penjual': request.form.get('nama_penjual', ''),
            'nomor_penjual': request.form.get('nomor_penjual', ''),
            'images': image_filenames,
            'image': image_filenames[0] if image_filenames else None,  # Backward compatibility
            'status': request.form.get('status', 'available')
        }

        # Update property
        if PropertyRepository.update_property(property_id, updated_data):
            # Retrain ML model with updated data
            ml_service.train_model()
            flash('Property updated successfully!')
        else:
            flash('Failed to update property')

    except Exception as e:
        flash(f'Error updating property: {str(e)}')

    return redirect(url_for('main.property_detail', property_id=property_id))

@admin_bp.route('/delete_property/<property_id>')
def delete_property(property_id):
    """Delete property"""
    if PropertyRepository.delete_property(property_id):
        # Retrain model
        ml_service.train_model()
        flash('Property deleted successfully!')
    else:
        flash('Property not found')

    return redirect(url_for('admin.admin_panel'))

# Add routes for base price management
@admin_bp.route('/get_base_prices')
def get_base_prices():
    """Get current base price settings"""
    try:
        base_prices = BasePriceRepository.load_base_prices()
        return {'success': True, 'data': base_prices}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@admin_bp.route('/update_base_prices', methods=['POST'])
def update_base_prices():
    """Update base price settings"""
    try:
        data = request.get_json()

        # Format the data properly
        updated_data = {
            'base_price_per_sqm_land': float(data.get('base_price_per_sqm_land', 500000)),
            'base_price_per_sqm_building': float(data.get('base_price_per_sqm_building', 2000000)),
            'room_multiplier': float(data.get('room_multiplier', 50000000)),
            'bathroom_multiplier': float(data.get('bathroom_multiplier', 25000000)),
            'floor_multiplier': float(data.get('floor_multiplier', 10000000)),
            'carport_multiplier': float(data.get('carport_multiplier', 15000000)),
            'year_bonus_per_year': float(data.get('year_bonus_per_year', 2000000)),
            'condition_multipliers': {
                'baru': float(data.get('condition_baru', 1.3)),
                'baik': float(data.get('condition_baik', 1.0)),
                'renovasi_ringan': float(data.get('condition_renovasi_ringan', 0.8)),
                'butuh_renovasi': float(data.get('condition_butuh_renovasi', 0.6))
            },
            'road_multipliers': {
                'jalan_besar': float(data.get('road_jalan_besar', 1.2)),
                'jalan_sedang': float(data.get('road_jalan_sedang', 1.0)),
                'gang_kecil': float(data.get('road_gang_kecil', 0.8))
            },
            'certificate_multipliers': {
                'shm': float(data.get('cert_shm', 1.1)),
                'hgb': float(data.get('cert_hgb', 1.0)),
                'girik': float(data.get('cert_girik', 0.9))
            }
        }

        if BasePriceRepository.save_base_prices(updated_data):
            # Retrain ML model with new base prices
            ml_service.train_model()
            return {'success': True, 'message': 'Base prices updated successfully!'}
        else:
            return {'success': False, 'error': 'Failed to update base prices'}

    except Exception as e:
        return {'success': False, 'error': str(e)}

@admin_bp.route('/predictions')
def predictions():
    """Admin predictions page with base price settings"""
    try:
        base_prices = BasePriceRepository.load_base_prices()
    except:
        base_prices = {}
    return render_template('admin/predictions.html', base_prices=base_prices)

@admin_bp.route('/settings')
def settings():
    """Admin settings page"""
    return render_template('admin/settings.html')