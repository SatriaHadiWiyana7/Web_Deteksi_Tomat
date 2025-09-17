# app/routes/profile_routes.py

import os
import uuid
from flask import (
    Blueprint, 
    render_template, 
    request, 
    session, 
    flash, 
    redirect, 
    url_for, 
    current_app
)

# --- Impor Modul Internal (Gunakan Impor Relatif) ---
from ..utils.db import query_db, execute_db
from .auth_routes import login_required # Impor decorator

# --- Definisi Blueprint ---
profile_bp = Blueprint('profile', __name__)

## Rute untuk Menampilkan Halaman Profil
@profile_bp.route('/')
@login_required
def profile_page():
    """Menampilkan halaman edit profil untuk pengguna yang sedang login."""
    user_id = session['user_id']
    user_data = query_db(
        "SELECT display_name, email, phone_number, profile_picture_path FROM users WHERE id = %s",
        (user_id,), 
        one=True
    )

    if not user_data:
        flash("Pengguna tidak ditemukan.", "danger")
        return redirect(url_for('main.index'))

    # Menentukan URL gambar profil
    if user_data.get('profile_picture_path'):
        user_data['profile_picture_url'] = url_for('main.serve_upload', filepath_in_uploads_dir=user_data['profile_picture_path'].replace('\\', '/'))
    else:
        user_data['profile_picture_url'] = url_for('static', filename='assets/default-avatar.png')

    return render_template('public/profile.html', user=user_data)

## Rute untuk Memproses Update Profil
@profile_bp.route('/update', methods=['POST'])
@login_required
def update_profile():
    """Memproses form update profil."""
    user_id = session['user_id']
    
    # Ambil data dari form
    display_name = request.form.get('display_name')
    email = request.form.get('email')
    phone_number = request.form.get('phone_number')

    if not all([display_name, email, phone_number]):
        flash("Nama, email, dan nomor telepon tidak boleh kosong.", "danger")
        return redirect(url_for('profile.profile_page'))

    # Dapatkan data pengguna saat ini, terutama path gambar lama
    current_user_data = query_db("SELECT profile_picture_path FROM users WHERE id = %s", (user_id,), one=True)
    old_image_path = current_user_data.get('profile_picture_path') if current_user_data else None

    update_query = "UPDATE users SET display_name = %s, email = %s, phone_number = %s, updated_at = NOW()"
    params = [display_name, email, phone_number]

    # Cek apakah ada file gambar profil baru yang diunggah
    if 'profile_picture' in request.files:
        file = request.files['profile_picture']
        if file.filename != '':
            # Buat nama file unik dan tentukan path penyimpanan
            unique_filename = f"user_{user_id}_{uuid.uuid4().hex[:8]}{os.path.splitext(file.filename)[1]}"
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER_PROFILE'], unique_filename)
            
            # Path relatif untuk disimpan di database
            db_path = os.path.join('profile_pics', unique_filename).replace('\\', '/')
            
            # Simpan file baru
            file.save(save_path)
            
            # Tambahkan update path gambar ke query
            update_query += ", profile_picture_path = %s"
            params.append(db_path)

            # Hapus file gambar lama jika ada
            if old_image_path:
                try:
                    old_file_full_path = os.path.join(current_app.root_path, '..', current_app.config['UPLOAD_FOLDER_BASE'], old_image_path)
                    if os.path.exists(old_file_full_path):
                        os.remove(old_file_full_path)
                except Exception as e:
                    print(f"Error deleting old profile picture: {e}")

    # Selesaikan query dan eksekusi
    update_query += " WHERE id = %s"
    params.append(user_id)

    if execute_db(update_query, tuple(params)):
        # Update nama pengguna di session jika berubah
        session['user_name'] = display_name
        flash("Profil berhasil diperbarui!", "success")
    else:
        flash("Gagal memperbarui profil. Terjadi kesalahan pada server.", "danger")

    return redirect(url_for('profile.profile_page'))