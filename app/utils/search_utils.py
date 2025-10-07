import re
from typing import Dict, List, Optional, Any

def extract_search_criteria(query: str) -> Dict[str, Any]:
    """
    Extract search criteria from query using enhanced NLP patterns
    Returns: Dict with extracted criteria
    """
    query_lower = query.lower().strip()
    criteria = {}

    # Normalize conversational patterns
    query_lower = re.sub(r'\b(ada\s*ga|ada\s*tidak|ada\s*ngga|ada\s*enggak)\b', '', query_lower)
    query_lower = re.sub(r'\b(kalau|kalo|gimana|bagaimana|berapa)\b', '', query_lower)
    query_lower = re.sub(r'\b(rumah|properti|yang|dengan|punya|memiliki|untuk|saya|mau|ingin|cari|mencari|butuh)\b', ' ', query_lower)
    query_lower = query_lower.strip()

    # Extract budget with improved patterns
    budget_patterns = [
        (r'(\d+)\s*jutaan', 1000000),
        (r'(\d+)\s*juta', 1000000),
        (r'kisaran\s*(\d+)', 1000000),
        (r'budget\s*(\d+)', 1000000),
        (r'(\d+)\s*m\b', 1000000),
        (r'harga\s*(\d+)', 1000000),
        (r'(\d+)\s*milyar', 1000000000),
    ]

    for pattern, multiplier in budget_patterns:
        matches = re.findall(pattern, query_lower)
        if matches:
            budget = int(matches[0]) * multiplier
            criteria['budget'] = budget
            # Flexible range ±30%
            criteria['budget_range'] = (budget * 0.7, budget * 1.3)
            break

    # Extract bedroom count
    room_patterns = [
        r'(\d+)\s*kamar\s*tidur',
        r'(\d+)\s*kt\b',
        r'kt\s*(\d+)',
        r'(\d+)\s*bedroom',
        r'(\d+)\s*kamar(?!\s*mandi)',
    ]

    for pattern in room_patterns:
        matches = re.findall(pattern, query_lower)
        if matches:
            criteria['kamar_tidur'] = int(matches[0])
            break

    # Extract bathroom count
    bathroom_patterns = [
        r'(\d+)\s*kamar\s*mandi',
        r'(\d+)\s*km\b',
        r'km\s*(\d+)',
        r'(\d+)\s*bathroom',
    ]

    for pattern in bathroom_patterns:
        matches = re.findall(pattern, query_lower)
        if matches:
            criteria['kamar_mandi'] = int(matches[0])
            break

    # Extract location
    kelurahan_list = [
        'majasari', 'sukaraja', 'gunung ibul', 'gunungibul', 'patih galung',
        'wonosari', 'gunung kemala', 'sukajadi', 'karang bindu', 'tanjung telang',
        'tanjung raman', 'cambai', 'muara dua', 'anak petai', 'pangkul', 
        'karang jaya', 'gunung ibul barat', 'mangga'
    ]

    kecamatan_list = [
        'prabumulih selatan', 'prabumulih timur', 'prabumulih barat', 
        'prabumulih utara', 'cambai', 'rambang kapak tengah'
    ]

    # Check for kelurahan
    for kelurahan in kelurahan_list:
        if kelurahan in query_lower:
            criteria['kelurahan'] = kelurahan.replace('gunungibul', 'gunung ibul').title()
            break

    # Check for kecamatan if no kelurahan found
    if 'kelurahan' not in criteria:
        for kecamatan in kecamatan_list:
            if kecamatan in query_lower:
                criteria['kecamatan'] = kecamatan.title()
                break

    # Price preferences
    if any(term in query_lower for term in ['murah', 'termurah', 'paling murah', 'cheap']):
        criteria['price_preference'] = 'low'
    elif any(term in query_lower for term in ['mahal', 'termahal', 'mewah', 'luxury']):
        criteria['price_preference'] = 'high'

    return criteria

def calculate_property_score(prop: Dict, criteria: Dict[str, Any]) -> float:
    """Calculate relevance score for a property based on criteria"""
    score = 0.0

    # Price scoring (40 points max)
    if 'budget' in criteria:
        budget = criteria['budget']
        prop_price = prop.get('harga', 0)
        if prop_price > 0:
            price_diff_percent = abs(prop_price - budget) / budget
            if price_diff_percent <= 0.1:
                score += 40
            elif price_diff_percent <= 0.3:
                score += 30
            elif price_diff_percent <= 0.5:
                score += 20
            elif price_diff_percent <= 0.8:
                score += 10

    # Bedroom scoring (25 points max)
    if 'kamar_tidur' in criteria:
        prop_rooms = prop.get('kamar_tidur', 0)
        required_rooms = criteria['kamar_tidur']
        if prop_rooms == required_rooms:
            score += 25
        elif abs(prop_rooms - required_rooms) == 1:
            score += 12

    # Bathroom scoring (15 points max)
    if 'kamar_mandi' in criteria:
        prop_bathrooms = prop.get('kamar_mandi', 0)
        required_bathrooms = criteria['kamar_mandi']
        if prop_bathrooms == required_bathrooms:
            score += 15
        elif abs(prop_bathrooms - required_bathrooms) == 1:
            score += 7

    # Location scoring (20 points max)
    if 'kelurahan' in criteria:
        prop_kelurahan = prop.get('kelurahan', '').lower().strip()
        criteria_kelurahan = criteria['kelurahan'].lower().strip()
        if prop_kelurahan == criteria_kelurahan or criteria_kelurahan in prop_kelurahan:
            score += 20

    if 'kecamatan' in criteria:
        prop_kecamatan = prop.get('kecamatan', '').lower().strip()
        criteria_kecamatan = criteria['kecamatan'].lower().strip()
        if prop_kecamatan == criteria_kecamatan or criteria_kecamatan in prop_kecamatan:
            score += 20

    return score

def filter_properties_strict(properties: List[Dict], criteria: Dict[str, Any]) -> List[Dict]:
    """Apply scoring-based filtering for varied and relevant results"""
    if not criteria:
        # No criteria - return all available properties sorted by date
        return [p for p in properties if p.get('status') == 'available']

    # Calculate scores for all available properties
    scored_properties = []
    for prop in properties:
        if prop.get('status') != 'available':
            continue

        score = calculate_property_score(prop, criteria)

        # Apply hard filters for budget range
        passes_filter = True
        if 'budget_range' in criteria:
            prop_price = prop.get('harga', 0)
            if prop_price > 0:
                min_budget, max_budget = criteria['budget_range']
                if prop_price < min_budget or prop_price > max_budget:
                    passes_filter = False

        # Include properties that either pass filters OR have a positive score
        if passes_filter or score > 0:
            scored_properties.append({
                'property': prop,
                'score': score
            })

    # Sort by score (highest first)
    scored_properties.sort(key=lambda x: x['score'], reverse=True)

    # Extract properties
    filtered = [item['property'] for item in scored_properties]

    # Apply price preference for final sorting
    if 'price_preference' in criteria and len(filtered) > 0:
        if criteria['price_preference'] == 'low':
            # Sort by price ascending
            filtered.sort(key=lambda p: p.get('harga', float('inf')))
        elif criteria['price_preference'] == 'high':
            # Sort by price descending
            filtered.sort(key=lambda p: p.get('harga', 0), reverse=True)

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