# app/__init__.py

import os
from flask import Flask
from flask_cors import CORS
from flask_session import Session
from flask_mail import Mail
from config import Config

# Inisialisasi ekstensi di luar factory agar bisa diimpor oleh modul lain
mail = Mail()

def create_app(config_class=Config):
    """
    Application Factory: Membuat dan mengonfigurasi instance aplikasi Flask.
    """
    # Secara eksplisit memberitahu Flask lokasi folder static dan templates
    # relatif terhadap folder 'app' ini.
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')

    # Memuat konfigurasi dari file config.py
    app.config.from_object(config_class)

    # Inisialisasi ekstensi Flask dengan aplikasi
    CORS(app)
    Session(app)
    mail.init_app(app)

    # Memastikan folder untuk unggahan ada
    # Path dibuat relatif terhadap root direktori proyek
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    os.makedirs(os.path.join(root_dir, app.config['UPLOAD_FOLDER_RAW']), exist_ok=True)
    os.makedirs(os.path.join(root_dir, app.config['UPLOAD_FOLDER_DETECTED']), exist_ok=True)
    os.makedirs(os.path.join(root_dir, app.config['UPLOAD_FOLDER_PROFILE']), exist_ok=True)


    # --- Registrasi Blueprint ---
    # Impor dilakukan di dalam fungsi untuk menghindari circular import
    from app.routes.main_routes import main_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.profile_routes import profile_bp
    from app.routes.admin_routes import admin_bp
    
    # Mendaftarkan setiap blueprint ke aplikasi
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp, url_prefix='/profile')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    return app