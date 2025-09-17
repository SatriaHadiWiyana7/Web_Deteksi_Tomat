# app/__init__.py
import os
from flask import Flask
from flask_cors import CORS
from flask_session import Session
from flask_mail import Mail
from config import Config

# Inisialisasi ekstensi di luar factory agar bisa diimpor di file lain
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inisialisasi Ekstensi
    CORS(app)
    Session(app)
    mail.init_app(app)

    # Membuat folder upload jika belum ada
    os.makedirs(app.config['UPLOAD_FOLDER_RAW'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER_DETECTED'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER_PROFILE'], exist_ok=True)

    # Mengimpor dan mendaftarkan Blueprints
    from app.routes.main_routes import main_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.profile_routes import profile_bp
    from app.routes.admin_routes import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(admin_bp)

    return app