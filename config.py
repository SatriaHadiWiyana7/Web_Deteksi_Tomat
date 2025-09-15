# config.py
import os

class Config:
    # Kunci Rahasia
    SECRET_KEY = os.urandom(24)

    # Konfigurasi Session
    SESSION_PERMANENT = False
    SESSION_TYPE = "filesystem"

    # Konfigurasi Database
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASSWORD = ''
    DB_NAME = 'fusarium_new'

    # Konfigurasi Mail
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'satriahadiwiyana7@gmail.com'  # Ganti dengan email Anda
    MAIL_PASSWORD = 'uwdp fajv pfin iiuk'  # Ganti dengan App Password
    MAIL_DEFAULT_SENDER = ('FUSACHECK', 'satriahadiwiyana7@students.amikom.ac.id')

    # Konfigurasi Folder Upload
    UPLOAD_FOLDER_BASE = 'uploads'
    UPLOAD_FOLDER_RAW = os.path.join(UPLOAD_FOLDER_BASE, 'raw_images')
    UPLOAD_FOLDER_DETECTED = os.path.join(UPLOAD_FOLDER_BASE, 'detected_images')
    UPLOAD_FOLDER_PROFILE = os.path.join(UPLOAD_FOLDER_BASE, 'profile_pics')