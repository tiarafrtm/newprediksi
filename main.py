"""
Main application entry point using Flask app factory pattern
"""
from app import create_app
from app.services.ml_service import ml_service

# Create Flask application
app = create_app()

if __name__ == '__main__':
    # Initialize ML model on startup
    ml_service.load_model()
    app.run(host='0.0.0.0', port=5000, debug=True)