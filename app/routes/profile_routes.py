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
from werkzeug.security import generate_password_hash

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
        "SELECT display_name, email, phone_number, profile_picture_path, date_of_birth, address FROM users WHERE id = %s",
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
    date_of_birth = request.form.get('date_of_birth')
    address = request.form.get('address')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    # Query dinamis untuk update
    query_parts = []
    params = []

    # Tambahkan field yang bisa diubah
    query_parts.append("display_name = %s")
    params.append(display_name)
    query_parts.append("date_of_birth = %s")
    params.append(date_of_birth if date_of_birth else None)
    query_parts.append("address = %s")
    params.append(address)

    # Logika untuk mengubah password
    if password:
        if password != confirm_password:
            flash("Password baru dan konfirmasi tidak cocok.", "danger")
            return redirect(url_for('profile.profile_page'))
        
        hashed_password = generate_password_hash(password)
        query_parts.append("password_hash = %s")
        params.append(hashed_password)

    # Logika untuk mengubah foto profil (sama seperti sebelumnya)
    if 'profile_picture' in request.files:
        file = request.files['profile_picture']
        if file.filename != '':
            unique_filename = f"user_{user_id}_{uuid.uuid4().hex[:8]}{os.path.splitext(file.filename)[1]}"
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER_PROFILE'], unique_filename)
            db_path = os.path.join('profile_pics', unique_filename).replace('\\', '/')
            file.save(save_path)
            query_parts.append("profile_picture_path = %s")
            params.append(db_path)

    if not query_parts:
        flash("Tidak ada data yang diubah.", "info")
        return redirect(url_for('profile.profile_page'))

    # Gabungkan query dan eksekusi
    query_str = f"UPDATE users SET {', '.join(query_parts)}, updated_at = NOW() WHERE id = %s"
    params.append(user_id)

    if execute_db(query_str, tuple(params)):
        session['user_name'] = display_name
        flash("Profil berhasil diperbarui!", "success")
    else:
        flash("Gagal memperbarui profil.", "danger")

    return redirect(url_for('profile.profile_page'))