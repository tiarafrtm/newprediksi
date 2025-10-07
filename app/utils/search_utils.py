import re
from typing import Dict, List, Optional, Any

def extract_search_criteria(query: str) -> Dict[str, Any]:
    """
    Extract search criteria from query using enhanced NLP patterns
    Returns: Dict with extracted criteria
    """
    query_lower = query.lower()
    criteria = {}
    
    # Normalize common conversational patterns
    query_lower = re.sub(r'\b(ada\s*ga|ada\s*tidak|ada\s*ngga|ada\s*enggak)\b', '', query_lower)
    query_lower = re.sub(r'\b(kalau|kalo|gimana|bagaimana|berapa)\b', '', query_lower)
    query_lower = re.sub(r'\b(rumah|properti|yang|dengan|punya|memiliki)\b', '', query_lower)
    query_lower = query_lower.strip()
    
    # Extract budget (enhanced patterns)
    budget_patterns = [
        r'(\d+)\s*juta',  # "500 juta"
        r'budget\s*(\d+)',  # "budget 500"
        r'(\d+)\s*m\b',  # "500m"
        r'harga\s*(\d+)',  # "harga 500"
        r'(\d+)\s*milyar',  # "1 milyar"
    ]
    
    for pattern in budget_patterns:
        matches = re.findall(pattern, query_lower)
        if matches:
            budget = int(matches[0]) * 1000000
            criteria['budget'] = budget
            criteria['budget_range'] = (budget * 0.8, budget * 1.2)  # ±20%
            break
    
    # Extract bedroom count (enhanced patterns)
    room_patterns = [
        r'(\d+)\s*kamar\s*tidur',  # "2 kamar tidur"
        r'(\d+)\s*kt\b',           # "2 kt"
        r'kt\s*(\d+)',             # "kt 2"
        r'kamar\s*tidur\s*(\d+)',  # "kamar tidur 2"
        r'(\d+)\s*bedroom',        # "2 bedroom"
        r'bedroom\s*(\d+)',        # "bedroom 2"
        # Handle cases where "kamar" might refer to bedroom in context
        r'(?<!mandi\s)(\d+)\s*kamar(?!\s*mandi)',  # "2 kamar" but not "2 kamar mandi"
    ]
    
    for pattern in room_patterns:
        matches = re.findall(pattern, query_lower)
        if matches:
            criteria['kamar_tidur'] = int(matches[0])
            break
    
    # Extract bathroom count (enhanced patterns)
    bathroom_patterns = [
        r'(\d+)\s*kamar\s*mandi',  # "2 kamar mandi"
        r'(\d+)\s*km\b',           # "2 km"
        r'km\s*(\d+)',             # "km 2"
        r'kamar\s*mandi\s*(\d+)',  # "kamar mandi 2"
        r'(\d+)\s*bathroom',       # "2 bathroom"
        r'bathroom\s*(\d+)',       # "bathroom 2"
        r'(\d+)\s*wc\b',           # "2 wc"
        r'wc\s*(\d+)',             # "wc 2"
    ]
    
    for pattern in bathroom_patterns:
        matches = re.findall(pattern, query_lower)
        if matches:
            criteria['kamar_mandi'] = int(matches[0])
            break
    
    # Extract area/size requirements
    luas_patterns = [
        r'(\d+)\s*m2?\s*tanah',     # "100 m2 tanah"
        r'tanah\s*(\d+)\s*m2?',     # "tanah 100 m2"
        r'luas\s*tanah\s*(\d+)',    # "luas tanah 100"
        r'(\d+)\s*meter\s*tanah',   # "100 meter tanah"
    ]
    
    for pattern in luas_patterns:
        matches = re.findall(pattern, query_lower)
        if matches:
            criteria['min_luas_tanah'] = int(matches[0])
            break
    
    building_patterns = [
        r'(\d+)\s*m2?\s*bangunan',     # "100 m2 bangunan"
        r'bangunan\s*(\d+)\s*m2?',     # "bangunan 100 m2"
        r'luas\s*bangunan\s*(\d+)',    # "luas bangunan 100"
        r'(\d+)\s*meter\s*bangunan',   # "100 meter bangunan"
    ]
    
    for pattern in building_patterns:
        matches = re.findall(pattern, query_lower)
        if matches:
            criteria['min_luas_bangunan'] = int(matches[0])
            break
    
    # Extract carport requirements
    carport_patterns = [
        r'(\d+)\s*carport',         # "1 carport"
        r'carport\s*(\d+)',         # "carport 1"
        r'(\d+)\s*garasi',          # "1 garasi"
        r'garasi\s*(\d+)',          # "garasi 1"
    ]
    
    for pattern in carport_patterns:
        matches = re.findall(pattern, query_lower)
        if matches:
            criteria['min_carport'] = int(matches[0])
            break
    
    # Extract location/facility requirements (enhanced)
    if any(term in query_lower for term in ['dekat sekolah', 'near school', 'sekolah', 'deket sekolah']):
        criteria['max_distance_school'] = 500  # 500m
    
    if any(term in query_lower for term in ['dekat rumah sakit', 'dekat rs', 'near hospital', 'hospital', 'deket rs']):
        criteria['max_distance_hospital'] = 1000  # 1km
    
    if any(term in query_lower for term in ['dekat pasar', 'near market', 'pasar', 'deket pasar']):
        criteria['max_distance_market'] = 800  # 800m
    
    # Extract condition preferences (enhanced)
    if any(term in query_lower for term in ['baru', 'new', 'brand new']):
        criteria['kondisi'] = 'baru'
    elif any(term in query_lower for term in ['baik', 'good', 'bagus']):
        criteria['kondisi'] = 'baik'
    elif any(term in query_lower for term in ['renovasi', 'butuh renovasi']):
        criteria['kondisi'] = 'butuh_renovasi'
    
    # Extract certificate preferences
    if any(term in query_lower for term in ['shm', 'sertifikat hak milik']):
        criteria['sertifikat'] = 'SHM'
    elif any(term in query_lower for term in ['hgb', 'hak guna bangunan']):
        criteria['sertifikat'] = 'HGB'
    
    # Extract kelurahan/location preferences (enhanced with actual data)
    kelurahan_list = [
        'majasari', 'sukaraja', 'gunung ibul', 'gunungibul', 'patih galung',
        'wonosari', 'gunung kemala', 'sukajadi', 'karang bindu', 'kel. tanjung telang',
        'tanjung telang', 'tanjung raman', 'cambai', 'muara dua', 'anak petai',
        'pangkul', 'karang jaya', 'gunung ibul barat', 'mangga'
    ]
    
    # Extract kecamatan/district preferences
    kecamatan_list = [
        'prabumulih selatan', 'prabumulih timur', 'prabumulih barat', 
        'prabumulih utara', 'cambai', 'rambang kapak tengah'
    ]
    
    # Extract location with various patterns
    location_patterns = [
        r'di\s+kelurahan\s+([a-zA-Z\s]+)',      # "di kelurahan gunung ibul"
        r'kelurahan\s+([a-zA-Z\s]+)',          # "kelurahan gunung ibul"
        r'di\s+kecamatan\s+([a-zA-Z\s]+)',     # "di kecamatan prabumulih timur"
        r'kecamatan\s+([a-zA-Z\s]+)',          # "kecamatan prabumulih timur"
        r'di\s+([a-zA-Z\s]+)',                 # "di gunung ibul"
        r'daerah\s+([a-zA-Z\s]+)',             # "daerah gunung ibul"
        r'wilayah\s+([a-zA-Z\s]+)',            # "wilayah gunung ibul"
        r'area\s+([a-zA-Z\s]+)',               # "area gunung ibul"
    ]
    
    # Try pattern matching first for kelurahan
    for pattern in location_patterns:
        matches = re.findall(pattern, query_lower)
        if matches:
            location = matches[0].strip()
            # Check if the extracted location is in our known kelurahan list
            for kelurahan in kelurahan_list:
                if kelurahan in location.lower() or location.lower() in kelurahan:
                    criteria['kelurahan'] = kelurahan.replace('gunungibul', 'gunung ibul').replace('kel. ', '').title()
                    break
            # Check if the extracted location is in our known kecamatan list
            if 'kelurahan' not in criteria:
                for kecamatan in kecamatan_list:
                    if kecamatan in location.lower() or location.lower() in kecamatan:
                        criteria['kecamatan'] = kecamatan.title()
                        break
            if 'kelurahan' in criteria or 'kecamatan' in criteria:
                break
    
    # Fallback to direct keyword matching for kelurahan
    if 'kelurahan' not in criteria and 'kecamatan' not in criteria:
        for kelurahan in kelurahan_list:
            if kelurahan in query_lower:
                criteria['kelurahan'] = kelurahan.replace('gunungibul', 'gunung ibul').replace('kel. ', '').title()
                break
        
        # If no kelurahan found, try kecamatan
        if 'kelurahan' not in criteria:
            for kecamatan in kecamatan_list:
                if kecamatan in query_lower:
                    criteria['kecamatan'] = kecamatan.title()
                    break
    
    # Extract price preferences
    if any(term in query_lower for term in ['murah', 'cheap', 'ekonomis']):
        criteria['price_preference'] = 'low'
    elif any(term in query_lower for term in ['mahal', 'expensive', 'mewah', 'luxury']):
        criteria['price_preference'] = 'high'
    
    # Extract size preferences
    if any(term in query_lower for term in ['besar', 'luas', 'big', 'large']):
        criteria['size_preference'] = 'large'
    elif any(term in query_lower for term in ['kecil', 'small', 'compact']):
        criteria['size_preference'] = 'small'
    
    return criteria

def filter_properties_strict(properties: List[Dict], criteria: Dict[str, Any]) -> List[Dict]:
    """
    Apply strict deterministic filtering based on extracted criteria
    """
    if not criteria:
        return properties
    
    filtered = []
    
    for prop in properties:
        matches = True
        
        # EXACT bedroom match (critical fix for the reported issue)
        if 'kamar_tidur' in criteria:
            prop_rooms = prop.get('kamar_tidur', 0)
            required_rooms = criteria['kamar_tidur']
            # For "2 kamar tidur" query, only show properties with EXACTLY 2 bedrooms
            if prop_rooms != required_rooms:
                matches = False
        
        # EXACT bathroom match
        if 'kamar_mandi' in criteria:
            prop_bathrooms = prop.get('kamar_mandi', 0)
            required_bathrooms = criteria['kamar_mandi']
            if prop_bathrooms != required_bathrooms:
                matches = False
        
        # Area/size filtering
        if 'min_luas_tanah' in criteria:
            prop_luas_tanah = prop.get('luas_tanah', 0)
            if prop_luas_tanah < criteria['min_luas_tanah']:
                matches = False
        
        if 'min_luas_bangunan' in criteria:
            prop_luas_bangunan = prop.get('luas_bangunan', 0)
            if prop_luas_bangunan < criteria['min_luas_bangunan']:
                matches = False
        
        # Carport filtering
        if 'min_carport' in criteria:
            prop_carport = prop.get('carport', 0)
            if prop_carport < criteria['min_carport']:
                matches = False
        
        # Location/kelurahan filtering (improved with fuzzy matching)
        if 'kelurahan' in criteria:
            prop_kelurahan = prop.get('kelurahan', '').lower().strip()
            criteria_kelurahan = criteria['kelurahan'].lower().strip()
            
            # Exact match
            if prop_kelurahan == criteria_kelurahan:
                pass  # matches = True
            # Fuzzy matching for variations
            elif 'gunung ibul' in criteria_kelurahan and 'gunung ibul' in prop_kelurahan:
                pass  # matches = True
            elif criteria_kelurahan in prop_kelurahan or prop_kelurahan in criteria_kelurahan:
                pass  # matches = True
            else:
                matches = False
        
        # Location/kecamatan filtering
        if 'kecamatan' in criteria:
            prop_kecamatan = prop.get('kecamatan', '').lower().strip()
            criteria_kecamatan = criteria['kecamatan'].lower().strip()
            
            # Exact match
            if prop_kecamatan == criteria_kecamatan:
                pass  # matches = True
            # Fuzzy matching for variations
            elif criteria_kecamatan in prop_kecamatan or prop_kecamatan in criteria_kecamatan:
                pass  # matches = True
            else:
                matches = False
        
        # Certificate filtering
        if 'sertifikat' in criteria:
            prop_sertifikat = prop.get('sertifikat', '')
            if prop_sertifikat.upper() != criteria['sertifikat'].upper():
                matches = False
        
        # Budget range filtering
        if 'budget_range' in criteria:
            prop_price = prop.get('harga', 0)
            if prop_price == 0:  # Skip properties without price
                matches = False
            else:
                min_budget, max_budget = criteria['budget_range']
                if not (min_budget <= prop_price <= max_budget):
                    matches = False
        
        # Distance filtering (strict)
        if 'max_distance_school' in criteria:
            if prop.get('jarak_sekolah', 9999) > criteria['max_distance_school']:
                matches = False
        
        if 'max_distance_hospital' in criteria:
            if prop.get('jarak_rs', 9999) > criteria['max_distance_hospital']:
                matches = False
        
        if 'max_distance_market' in criteria:
            if prop.get('jarak_pasar', 9999) > criteria['max_distance_market']:
                matches = False
        
        # Condition filtering
        if 'kondisi' in criteria:
            prop_kondisi = prop.get('kondisi', '')
            if prop_kondisi.lower() != criteria['kondisi'].lower():
                matches = False
        
        if matches:
            filtered.append(prop)
    
    # Apply preference-based sorting
    if 'price_preference' in criteria:
        if criteria['price_preference'] == 'low':
            filtered.sort(key=lambda p: p.get('harga', float('inf')))
        elif criteria['price_preference'] == 'high':
            filtered.sort(key=lambda p: p.get('harga', 0), reverse=True)
    
    if 'size_preference' in criteria:
        if criteria['size_preference'] == 'large':
            filtered.sort(key=lambda p: p.get('luas_tanah', 0) + p.get('luas_bangunan', 0), reverse=True)
        elif criteria['size_preference'] == 'small':
            filtered.sort(key=lambda p: p.get('luas_tanah', 0) + p.get('luas_bangunan', 0))
    
    return filtered

def is_property_related_query(query: str) -> bool:
    """Check if query contains property-related keywords (enhanced)"""
    property_keywords = [
        'rumah', 'juta', 'kamar', 'budget', 'luas', 'sekolah', 'hospital', 'pasar', 
        'properti', 'beli', 'cari', 'house', 'bedroom', 'bathroom', 'price', 'search',
        'carport', 'garasi', 'tanah', 'bangunan', 'sertifikat', 'kelurahan', 'alamat',
        'kt', 'km', 'wc', 'm2', 'meter', 'dekat', 'deket', 'jarak', 'kondisi',
        'shm', 'hgb', 'tahun', 'dibangun', 'renovasi', 'mandi', 'tidur', 'ada',
        'di', 'daerah', 'wilayah', 'area', 'lokasi', 'kecamatan',
        'mencari', 'sedang', 'butuh', 'ingin', 'perlu', 'mau',
        # Kelurahan keywords
        'majasari', 'sukaraja', 'gunung ibul', 'patih galung', 'wonosari',
        'gunung kemala', 'sukajadi', 'karang bindu', 'tanjung telang', 'tanjung raman',
        'cambai', 'muara dua', 'anak petai', 'pangkul', 'karang jaya', 'gunung ibul barat', 'mangga',
        # Kecamatan keywords
        'prabumulih selatan', 'prabumulih timur', 'prabumulih barat', 
        'prabumulih utara', 'rambang kapak tengah'
    ]
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in property_keywords)