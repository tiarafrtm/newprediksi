# Prediksi Harga Rumah - Real Estate Price Prediction App

## Overview
This is a Flask-based real estate property management and price prediction application for properties in Prabumulih, Indonesia. It uses Machine Learning (Random Forest) and AI (Google Gemini) to help users find properties and predict property prices.

## Project Architecture

### Technology Stack
- **Backend Framework**: Flask 3.1.2
- **Package Manager**: uv (Python package manager)
- **Python Version**: 3.11
- **ML Framework**: scikit-learn 1.7.2
- **AI Service**: Google Gemini AI
- **Production Server**: Gunicorn

### Project Structure
```
.
├── app/
│   ├── blueprints/          # Flask blueprints (routes)
│   │   ├── main.py         # Main user-facing routes
│   │   ├── admin.py        # Admin panel routes
│   │   └── api.py          # API endpoints
│   ├── services/           # Business logic
│   │   ├── ai_service.py   # Gemini AI integration
│   │   └── ml_service.py   # ML price prediction
│   ├── utils/              # Utility functions
│   ├── config.py           # Application configuration
│   └── models.py           # Data models (JSON-based)
├── data/
│   ├── properties.json     # Property database
│   └── base_prices.json    # Base price settings
├── models/
│   └── price_model.pkl     # Trained ML model
├── static/                 # Static files (images, CSS, JS)
├── templates/              # HTML templates
└── main.py                 # Application entry point
```

## Features

### User Features
1. **Property Search**: Natural language property search using AI
2. **Property Listings**: Browse and filter properties by budget and location
3. **Price Prediction**: ML-based property price prediction based on:
   - Land area (luas tanah)
   - Building area (luas bangunan)
   - Number of bedrooms/bathrooms
   - Building condition
   - Certificate type
   - Location factors

### Admin Features
1. **Property Management**: Add, edit, delete properties
2. **Base Price Settings**: Configure pricing parameters
3. **Prediction Dashboard**: View price predictions

## Data Storage
The application uses JSON file-based storage:
- **Properties**: Stored in `data/properties.json`
- **Base Prices**: Stored in `data/base_prices.json`

## Configuration

### Environment Variables
The following environment variables are configured in `.env`:
- `GEMINI_API_KEY`: API key for Google Gemini AI
- `GOOGLE_MAPS_API_KEY`: API key for Google Maps (optional)
- `SESSION_SECRET`: Flask session secret key

### ML Model
- **Type**: Random Forest Regressor
- **Training Version**: scikit-learn 1.5.2
- **Current Version**: scikit-learn 1.7.2 (backward compatible with warnings)
- **Location**: `models/price_model.pkl`

## Development

### Running Locally
The application runs on port 5000:
```bash
uv run python main.py
```

### Deployment
Configured for Replit Autoscale deployment using Gunicorn:
```bash
gunicorn --bind=0.0.0.0:5000 --reuse-port main:app
```

## Recent Changes (October 2025)
- Migrated to Replit environment
- Configured uv package manager
- Set up development workflow on port 5000
- Configured production deployment with Gunicorn
- Added .gitignore for Python project
- **Changed prediction to 100% Machine Learning**: Removed base price calculation hybrid model, now uses pure ML predictions

## Known Issues
- ML model shows version warnings (trained with scikit-learn 1.5.2, running on 1.7.2)
  - This is non-critical and doesn't affect functionality
  - Consider retraining model with current version if needed

## Notes
- The application is designed for properties in Prabumulih, South Sumatra, Indonesia
- Uses Indonesian language (Bahasa Indonesia) for the interface
- Implements ProxyFix middleware for proper handling in Replit environment
