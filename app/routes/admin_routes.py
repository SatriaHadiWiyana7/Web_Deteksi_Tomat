# app/routes/admin_routes.py

import os
from datetime import datetime
from flask import (
    Blueprint, 
    render_template, 
    session, 
    jsonify, 
    request, 
    url_for, 
    current_app,
    flash
)
from werkzeug.security import generate_password_hash

# --- Impor Modul Internal (Gunakan Impor Relatif) ---
from ..utils.db import query_db, execute_db, get_db_connection
from .auth_routes import admin_required

# --- Definisi Blueprint ---
admin_bp = Blueprint('admin', __name__)

# ====================================================================
# RUTE UNTUK MENAMPILKAN HALAMAN (RENDER TEMPLATE)
# ====================================================================

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Menampilkan halaman utama dashboard admin."""
    return render_template('admin/dashboard.html', admin_username=session.get('admin_username'))

@admin_bp.route('/users')
@admin_required
def users_page():
    """Menampilkan halaman manajemen pengguna."""
    return render_template('admin/users.html', admin_username=session.get('admin_username'))

# ====================================================================
# API ENDPOINTS UNTUK LOG DETEKSI
# ====================================================================

@admin_bp.route('/logs', methods=['GET'])
@admin_required
def get_admin_logs():
    """API untuk mengambil semua data log deteksi untuk ditampilkan di dashboard."""
    try:
        logs_data = query_db(
            """
            SELECT
                d.id, d.detection_date, d.result, d.confidence,
                r.image_path AS raw_image_path,
                u.display_name AS user_name,
                u.phone_number AS user_phone
            FROM fusarium_new_detections d
            JOIN users u ON d.user_id = u.id
            LEFT JOIN fusarium_new_raw_images r ON d.raw_image_id = r.id
            ORDER BY d.detection_date DESC
            """
        )

        if logs_data is None:
            return jsonify({"error": "Gagal mengambil log dari database"}), 500

        # Proses data agar siap dikirim sebagai JSON
        for log in logs_data:
            if isinstance(log.get('detection_date'), datetime):
                log['detection_date'] = log['detection_date'].isoformat()
            
            image_path = log.get('raw_image_path')
            if image_path:
                log['raw_image_url'] = url_for('main.serve_upload', filepath_in_uploads_dir=image_path.replace('\\', '/'))
            else:
                log['raw_image_url'] = None
        
        return jsonify(logs_data)
    except Exception as e:
        print(f"Error fetching admin logs: {e}")
        return jsonify({"error": "Terjadi kesalahan internal saat mengambil log."}), 500

@admin_bp.route('/logs/<int:detection_id>', methods=['DELETE'])
@admin_required
def delete_admin_log(detection_id):
    """API untuk menghapus satu entri log deteksi beserta file gambarnya."""
    # Logika untuk mengambil path gambar dan ID gambar mentah
    detection_info = query_db(
        """
        SELECT d.raw_image_id, r.image_path 
        FROM fusarium_new_detections d
        LEFT JOIN fusarium_new_raw_images r ON d.raw_image_id = r.id
        WHERE d.id = %s
        """, 
        (detection_id,), 
        one=True
    )

    if not detection_info:
        return jsonify({"error": "Log deteksi tidak ditemukan"}), 404

    # Hapus dari database
    execute_db("DELETE FROM fusarium_new_detections WHERE id = %s", (detection_id,))
    if detection_info.get('raw_image_id'):
        execute_db("DELETE FROM fusarium_new_raw_images WHERE id = %s", (detection_info['raw_image_id'],))

    # Hapus file gambar dari server
    if detection_info.get('image_path'):
        try:
            image_path = os.path.join(current_app.root_path, '..', current_app.config['UPLOAD_FOLDER_BASE'], detection_info['image_path'].replace('\\', '/'))
            if os.path.exists(image_path):
                os.remove(image_path)
        except OSError as e:
            print(f"Error deleting image file {image_path}: {e}")
            # Gagal hapus file bukan error fatal, jadi tetap kembalikan sukses
            return jsonify({"message": "Log berhasil dihapus, tetapi file gambar gagal dihapus."}), 200

    return jsonify({"message": "Log dan data terkait berhasil dihapus"}), 200


# ====================================================================
# API ENDPOINTS UNTUK MANAJEMEN PENGGUNA (CRUD)
# ====================================================================

@admin_bp.route('/users/data', methods=['GET'])
@admin_required
def get_admin_users_data():
    """API untuk mengambil semua data pengguna."""
    try:
        users = query_db("SELECT id, display_name, phone_number, email, total_uploads, is_active, created_at FROM users ORDER BY created_at DESC")
        if users is None:
            return jsonify({"error": "Gagal mengambil data pengguna"}), 500
        for user in users:
            if isinstance(user.get('created_at'), datetime):
                user['created_at'] = user['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        return jsonify(users)
    except Exception as e:
        print(f"Error fetching users data: {e}")
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/users/add', methods=['POST'])
@admin_required
def add_admin_user():
    """API untuk menambah pengguna baru."""
    data = request.get_json()
    phone = data.get('phone_number')
    name = data.get('display_name')
    email = data.get('email')
    password = data.get('password')

    if not all([phone, name, email, password]):
        return jsonify({"error": "Semua field (nama, no. telp, email, password) wajib diisi"}), 400
    if query_db("SELECT id FROM users WHERE phone_number = %s OR email = %s", (phone, email), one=True):
        return jsonify({"error": "Nomor telepon atau email sudah ada"}), 409

    hashed_password = generate_password_hash(password)
    success = execute_db(
        "INSERT INTO users (phone_number, display_name, email, password_hash, is_active, total_uploads) VALUES (%s, %s, %s, %s, 1, 0)",
        (phone, name, email, hashed_password)
    )
    return jsonify({"message": "Pengguna berhasil ditambahkan"}) if success else jsonify({"error": "Gagal menambahkan pengguna"}), (201 if success else 500)

@admin_bp.route('/users/update/<int:user_id>', methods=['POST'])
@admin_required
def update_admin_user(user_id):
    """API untuk mengupdate data pengguna."""
    data = request.get_json()
    name = data.get('display_name')
    phone = data.get('phone_number')
    email = data.get('email')
    password = data.get('password')

    if not name or not phone or not email:
        return jsonify({"error": "Nama, no. telp, dan email wajib diisi"}), 400

    # Cek konflik nomor telepon atau email dengan pengguna lain
    if query_db("SELECT id FROM users WHERE (phone_number = %s OR email = %s) AND id != %s", (phone, email, user_id), one=True):
        return jsonify({"error": "Nomor telepon atau email sudah digunakan oleh pengguna lain"}), 409

    if password: # Jika password diisi, update password
        hashed_password = generate_password_hash(password)
        success = execute_db("UPDATE users SET display_name=%s, phone_number=%s, email=%s, password_hash=%s WHERE id=%s", (name, phone, email, hashed_password, user_id))
    else: # Jika password kosong, jangan update password
        success = execute_db("UPDATE users SET display_name=%s, phone_number=%s, email=%s WHERE id=%s", (name, phone, email, user_id))
    
    return jsonify({"message": "Pengguna berhasil diperbarui"}) if success else jsonify({"error": "Gagal memperbarui pengguna"}), (200 if success else 500)

@admin_bp.route('/users/toggle_activation/<int:user_id>', methods=['POST'])
@admin_required
def toggle_user_activation(user_id):
    """API untuk mengaktifkan atau menonaktifkan pengguna."""
    user = query_db("SELECT is_active FROM users WHERE id = %s", (user_id,), one=True)
    if not user:
        return jsonify({"error": "Pengguna tidak ditemukan"}), 404
    
    new_status = not user['is_active']
    success = execute_db("UPDATE users SET is_active = %s WHERE id = %s", (new_status, user_id))
    action = "diaktifkan" if new_status else "dinonaktifkan"
    return jsonify({"message": f"Pengguna berhasil {action}", "is_active": new_status}) if success else jsonify({"error": "Gagal mengubah status"}), (200 if success else 500)

@admin_bp.route('/users/delete/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_admin_user(user_id):
    """API untuk menghapus pengguna."""
    # Untuk keamanan, hapus dulu data terkait pengguna ini
    execute_db("DELETE FROM fusarium_new_detections WHERE user_id = %s", (user_id,))
    execute_db("DELETE FROM fusarium_new_raw_images WHERE user_id = %s", (user_id,))
    execute_db("DELETE FROM password_reset_tokens WHERE user_id = %s", (user_id,))
    
    # Baru hapus pengguna
    success = execute_db("DELETE FROM users WHERE id = %s", (user_id,))
    
    return jsonify({"message": "Pengguna dan semua data terkait berhasil dihapus"}) if success else jsonify({"error": "Gagal menghapus pengguna"}), (200 if success else 500)

@admin_bp.route('/logs/delete_all', methods=['DELETE'])
@admin_required
def delete_all_admin_logs():
    """
    Endpoint API untuk menghapus SEMUA log deteksi dan gambar mentah terkait.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Koneksi database gagal"}), 500
        cursor = conn.cursor(dictionary=True)

        # Langkah 1: Kumpulkan semua path gambar yang akan dihapus SEBELUM menghapus record DB
        cursor.execute("SELECT image_path FROM fusarium_new_raw_images WHERE image_path IS NOT NULL")
        image_paths_to_delete = [row['image_path'] for row in cursor.fetchall()]

        # Langkah 2: Lakukan penghapusan database dalam satu transaksi
        conn.start_transaction()
        cursor.execute("DELETE FROM fusarium_new_detections")
        detections_deleted_count = cursor.rowcount
        
        cursor.execute("DELETE FROM fusarium_new_raw_images")
        raw_images_deleted_count = cursor.rowcount
        conn.commit()

        # Langkah 3: Hapus file fisik dari server
        deleted_files_count = 0
        failed_to_delete_files = []
        for rel_path in image_paths_to_delete:
            full_path = os.path.join(current_app.root_path, '..', current_app.config['UPLOAD_FOLDER_BASE'], rel_path.replace('\\', '/'))
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                    deleted_files_count += 1
                except OSError as e:
                    print(f"Gagal menghapus file {full_path}: {e}")
                    failed_to_delete_files.append(os.path.basename(full_path))
        
        # Buat pesan respons yang informatif
        message = (
            f"Operasi selesai. {detections_deleted_count} log deteksi dan "
            f"{raw_images_deleted_count} data gambar dihapus dari database. "
            f"{deleted_files_count} file gambar berhasil dihapus dari server."
        )
        if failed_to_delete_files:
            message += f" Gagal menghapus beberapa file: {', '.join(failed_to_delete_files)}."
            
        return jsonify({"message": message}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error saat menghapus semua log: {e}")
        return jsonify({"error": f"Terjadi kesalahan tak terduga: {e}"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()