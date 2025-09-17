# app/routes/main_routes.py

import os
import uuid
from datetime import datetime
from flask import (
    Blueprint, 
    render_template, 
    request, 
    jsonify, 
    session, 
    url_for, 
    send_from_directory, 
    current_app
)

# --- Impor Modul Internal (Gunakan Impor Relatif) ---
from ..utils.db import query_db, execute_db
from ..utils.prediction import predict_image
from .auth_routes import login_required # Mengimpor decorator

# --- Definisi Blueprint ---
main_bp = Blueprint('main', __name__)


## Rute Halaman Utama (Homepage)
@main_bp.route('/')
def index():
    """
    Menampilkan halaman utama (index).
    Memeriksa status login untuk menampilkan gambar profil di navbar.
    """
    profile_pic_url = None
    # Menggunakan url_for untuk default avatar agar konsisten
    default_avatar = url_for('static', filename='assets/default-avatar.png')
    
    if session.get('logged_in'):
        user_id = session.get('user_id')
        user = query_db("SELECT profile_picture_path FROM users WHERE id = %s", (user_id,), one=True)
        if user and user.get('profile_picture_path'):
            # Membuat URL yang valid untuk file gambar profil
            profile_pic_url = url_for('main.serve_upload', filepath_in_uploads_dir=user['profile_picture_path'].replace('\\', '/'))

    return render_template('public/index.html', 
        logged_in=session.get('logged_in', False), 
        user_name=session.get('user_name', ''),
        # Memastikan selalu ada URL gambar yang valid untuk ditampilkan
        profile_picture_url=profile_pic_url or default_avatar
    )


## Rute untuk Menyajikan File dari Folder 'uploads'
@main_bp.route('/uploads/<path:filepath_in_uploads_dir>')
def serve_upload(filepath_in_uploads_dir):
    """
    Menyajikan file statis (gambar) dari direktori UPLOAD_FOLDER_BASE.
    Ini penting untuk menampilkan gambar profil dan gambar hasil deteksi.
    """
    # Membuat path absolut ke direktori 'uploads' yang berada di luar folder 'app'
    base_upload_dir = os.path.join(current_app.root_path, '..', current_app.config['UPLOAD_FOLDER_BASE'])
    return send_from_directory(os.path.normpath(base_upload_dir), filepath_in_uploads_dir)

## Rute untuk Proses Unggah dan Prediksi Gambar (API)
@main_bp.route("/upload", methods=["POST"])
def upload_image():
    """
    Endpoint API yang menerima file gambar, melakukan prediksi,
    menyimpan hasilnya ke database (jika pengguna login), dan
    mengembalikan hasil prediksi dalam format JSON.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Membuat nama file yang unik untuk menghindari tumpang tindih
    unique_filename = f"{uuid.uuid4().hex}{os.path.splitext(file.filename)[1]}"
    
    # Path untuk menyimpan gambar mentah di server
    raw_image_save_path = os.path.join(current_app.config['UPLOAD_FOLDER_RAW'], unique_filename)
    # Path relatif yang akan disimpan di database
    raw_image_path_for_db = os.path.join('raw_images', unique_filename).replace('\\', '/')

    try:
        file.save(raw_image_save_path)
    except Exception as e:
        print(f"Error saving file: {e}")
        return jsonify({"error": "Failed to save uploaded file"}), 500

    # Panggil fungsi prediksi pada gambar yang telah disimpan
    result = predict_image(raw_image_save_path)

    # Cek status login dari session
    user_id = session.get('user_id')

    # Jika pengguna login, simpan data ke database
    if user_id:
        try:
            # 1. Simpan data gambar mentah
            raw_image_id = execute_db(
                "INSERT INTO fusarium_new_raw_images (user_id, image_path) VALUES (%s, %s)",
                (user_id, raw_image_path_for_db),
                fetch_lastrowid=True
            )

            # 2. Simpan hasil deteksi yang merujuk ke gambar mentah
            if raw_image_id:
                execute_db(
                    "INSERT INTO fusarium_new_detections (user_id, raw_image_id, result, confidence, image_path) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, raw_image_id, result['label'], result['confidence'], raw_image_path_for_db)
                )
            else:
                print("Failed to get raw_image_id for detection record.")
        except Exception as e:
            print(f"Database error during result saving: {e}")

    return jsonify({
        "result": result, 
        "logged_in": session.get('logged_in', False), 
        "user_name": session.get('user_name', "")
    })

## Rute untuk Riwayat Deteksi (API)
@main_bp.route('/history')
@login_required # Hanya pengguna yang sudah login yang bisa mengakses rute ini
def history_api():
    """
    Endpoint API untuk mengambil data riwayat deteksi dari pengguna yang sedang login.
    Mengembalikan data riwayat dalam format JSON.
    """
    user_id = session.get('user_id')
    
    query = """
        SELECT
            d.detection_date,
            d.result,
            d.confidence,
            r.image_path AS raw_image_path
        FROM
            fusarium_new_detections d
        JOIN
            fusarium_new_raw_images r ON d.raw_image_id = r.id
        WHERE
            d.user_id = %s
        ORDER BY
            d.detection_date DESC
    """
    history_data = query_db(query, (user_id,))
    
    # Proses data agar siap dikirim sebagai JSON
    if history_data:
        for item in history_data:
            # Konversi objek datetime ke string format ISO 8601 agar bisa di-parse oleh JavaScript
            if isinstance(item.get('detection_date'), datetime):
                item['detection_date'] = item['detection_date'].isoformat()
            
            # Buat URL lengkap untuk gambar agar bisa diakses dari frontend
            if item.get('raw_image_path'):
                item['raw_image_url'] = url_for('main.serve_upload', filepath_in_uploads_dir=item['raw_image_path'])
            else:
                item['raw_image_url'] = None
            
    return jsonify(history_data or [])