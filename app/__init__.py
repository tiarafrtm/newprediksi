import os
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

def create_app():
    """Flask application factory"""
    load_dotenv()
    
    # Configure Flask to use templates and static files from root directory
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    from app.config import Config
    app.secret_key = Config.SECRET_KEY
    
    # Configure ProxyFix for Replit environment
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    app.config['UPLOAD_FOLDER'] = 'static/images'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Ensure required directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('data', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    
    # Register blueprints
    from app.blueprints.main import main_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app